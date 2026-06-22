# -*- coding: utf-8 -*-
# 练习模块 - 业务逻辑层
# 适配新数据库模型：Student、QuestionTemplate、PracticeProgress、PracticeFavorite

import json
import math
import random
import time
from collections import defaultdict
from django.db import models
from django.utils import timezone

from .models import PracticeProgress, PracticeFavorite
from apps.system.models import Student, QuestionTemplate
from apps.exam.services import _generate_dynamic_options, _validate_answer_format, _normalize_multi_answer
from utils.redis_client import RedisClient

# Redis key 前缀
SESSION_PREFIX = "prac_session:"
COUNTER_KEY = "prac_counter"


def _next_session_id():
    """生成唯一 session_id"""
    try:
        redis_client = RedisClient()
        counter = redis_client.incr(COUNTER_KEY)
    except Exception:
        counter = int(time.time() * 1000)
    return f"prac_{time.strftime('%Y%m%d')}_{counter:05d}"


def _get_redis(key):
    """Redis 读取线程安全封装"""
    try:
        redis_client = RedisClient()
        return redis_client.get(key)
    except Exception:
        return None


def _set_redis(key, value, ttl=7200):
    """Redis 写入封装"""
    try:
        redis_client = RedisClient()
        redis_client.setex(key, value, ttl)
        return True
    except Exception:
        return False


def _del_redis(key):
    """Redis 删除封装"""
    try:
        redis_client = RedisClient()
        redis_client.delete(key)
        return True
    except Exception:
        return False


def _get_session_data(session_id):
    """从 Redis 获取会话数据"""
    raw = _get_redis(f"{SESSION_PREFIX}{session_id}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _save_session_data(session_id, data, ttl=7200):
    """将会话数据存入 Redis"""
    return _set_redis(f"{SESSION_PREFIX}{session_id}", json.dumps(data, ensure_ascii=False), ttl)


def _get_current_student_xid(session):
    """
    从会话数据中获取当前学生ID（兼容普通模式/批量模式）
    普通模式：直接读取 session['student_xid']
    批量模式：根据 session['current_index'] 从 student_list 中取
    """
    if session.get('mode') == 'batch':
        idx = session.get('current_index', 0)
        student_list = session.get('student_list', [])
        if idx < len(student_list):
            return student_list[idx]['student_xid']
        return None
    return session.get('student_xid')


def _get_current_student_name(session):
    """
    从会话数据中获取当前学生姓名（兼容普通模式/批量模式）
    """
    if session.get('mode') == 'batch':
        idx = session.get('current_index', 0)
        student_list = session.get('student_list', [])
        if idx < len(student_list):
            return student_list[idx]['student_name']
        return ''
    return session.get('student_name', '')


def _find_next_student(user_id):
    """
    为该辅导员随机找下一个未全部答对的学生（单次聚合查询，O(1)次DB查询）
    user_id: 用于查询练习进度和匹配学生（FK 关联 User → Student.advisor_id）
    """
    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    if not templates:
        return None
    total_template_count = len(templates)
    template_ids = [t.id for t in templates]

    # 获取该辅导员名下的所有学生（通过 FK advisor_id 匹配）
    students = list(Student.objects.filter(advisor_id=user_id))
    if not students:
        return None

    # 一次聚合查询：按 student_id 分组统计已通过的模板数
    passed_counts = (
        PracticeProgress.objects
        .filter(
            user_id=user_id,
            student_id__in=[s.id for s in students],
            template_id__in=template_ids,
            is_passed=True,
        )
        .values('student_id')
        .annotate(cnt=models.Count('id'))
    )
    passed_map = defaultdict(int, {p['student_id']: p['cnt'] for p in passed_counts})

    # 筛出未全部答对的学生，随机选取一个
    unfinished = [s for s in students if passed_map[s.id] < total_template_count]
    if not unfinished:
        return None
    return random.choice(unfinished)


def _generate_questions(student, templates, all_students):
    """
    根据学生信息和模板动态生成题目列表（含选项和正确答案）
    student: Student 模型实例
    templates: QuestionTemplate 列表
    all_students: 同辅导员的所有学生列表（用于生成干扰项）
    """
    questions = []
    for t in templates:
        # 将题干中的 {name} 替换为学生姓名
        stem = t.stem.replace('{name}', student.name)
        # 动态生成选项和正确答案
        options, _ = _generate_dynamic_options(t, student, all_students)
        q = {
            'question_id': t.id,
            'template_id': t.id,
            'title': stem,
            'question_type': t.question_type,
        }
        if options:
            q['options'] = options
        questions.append(q)
    return questions


def _calc_progress(user_id):
    """
    计算总体练习进度
    user_id: 辅导员用户ID（用于 FK 查询和匹配学生）
    """
    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    # 获取该辅导员名下的所有学生（通过 FK advisor_id 匹配）
    students = list(Student.objects.filter(advisor_id=user_id))
    if not templates or not students:
        return 1.0 if not templates else 0.0

    total = len(students) * len(templates)
    if total == 0:
        return 1.0

    # 统计已答对的练习进度
    passed = PracticeProgress.objects.filter(
        user_id=user_id,
        template_id__in=[t.id for t in templates],
        is_passed=True,
    ).count()

    return round(passed / total, 4)


# ============================================================
# 2.1 开始练习 / 恢复练习
# ============================================================

def start_practice(user_id, advisor_name):
    """
    开始或恢复练习
    随机选取一名未全部答对的学生，基于题库生成练习题目
    参数:
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容，实际匹配使用 advisor_id FK）
    返回值: (success, data_or_error)
    """
    student = _find_next_student(user_id)
    # 没有待练习的学生时返回空结果
    if not student:
        progress = _calc_progress(user_id)
        return True, {
            'session_id': '',
            'student_xid': 0,
            'student_name': '',
            'questions': [],
            'progress': progress,
        }

    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    if not templates:
        return True, {
            'session_id': '',
            'student_xid': student.id,
            'student_name': student.name,
            'questions': [],
            'progress': _calc_progress(user_id),
        }

    # 生成唯一会话ID
    session_id = _next_session_id()
    # 获取同辅导员所有学生（用于生成干扰项，通过 FK advisor_id 匹配）
    all_students = list(Student.objects.filter(advisor_id=user_id))
    # 动态生成题目
    questions = _generate_questions(student, templates, all_students)

    # 会话数据存入 Redis
    session_data = {
        'user_id': user_id,
        'student_xid': student.id,
        'student_name': student.name,
        'template_ids': [t.id for t in templates],
    }
    _save_session_data(session_id, session_data)

    progress = _calc_progress(user_id)

    return True, {
        'session_id': session_id,
        'student_xid': student.id,
        'student_name': student.name,
        'questions': questions,
        'progress': progress,
    }


# ============================================================
# 2.2 提交本题答案
# ============================================================

def _process_single_answer(question_id, user_answer, user_id, session, all_students=None):
    """
    处理单题提交的核心逻辑（提取为内部函数，供单题和批量模式复用）
    参数:
        question_id: 题目模板ID
        user_answer: 用户提交的答案
        user_id: 辅导员用户ID
        session: 已校验的会话数据
        all_students: 同辅导员所有学生列表（批量模式复用，避免重复查询）
    返回值: (success, data_or_error)
        data: {question_id, is_correct, correct_answer}
    """
    # 校验题目是否属于当前会话（防止提交不属于当前会话的题目）
    if question_id not in session.get('template_ids', []):
        return False, (400, f"题目{question_id}不属于当前练习会话")

    # 获取题目模板
    try:
        template = QuestionTemplate.objects.get(id=question_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, f"题目{question_id}不存在")

    # 校验答案格式是否符合题型要求（空答案跳过校验，允许保存未作答状态）
    if user_answer.strip():
        valid, err_msg = _validate_answer_format(user_answer, template.question_type)
        if not valid:
            return False, (400, err_msg)

    # 获取当前学生ID（兼容普通模式/批量模式）
    current_student_xid = _get_current_student_xid(session)
    if current_student_xid is None:
        return False, (400, "当前会话无有效学生")

    # 获取学生对象及同辅导员所有学生，动态生成正确答案
    is_correct = None
    correct_answer = ''
    try:
        student = Student.objects.get(id=current_student_xid)
        if all_students is None:
            all_students = list(Student.objects.filter(advisor_id=user_id))
        _, correct_answer = _generate_dynamic_options(template, student, all_students)
        correct_answer = correct_answer or ''
    except Student.DoesNotExist:
        correct_answer = ''

    # 客观题自动判分：单选题/多选题/判断题
    if template.question_type in ('single', 'multi', 'judge'):
        if template.question_type == 'multi':
            # 多选题：归一化后比较，避免 "B,A" vs "A,B" 误判
            is_correct = (
                _normalize_multi_answer(user_answer) == _normalize_multi_answer(correct_answer)
            )
        else:
            # 单选题/判断题：直接去空格转大写后比较
            is_correct = (user_answer.strip().upper() == correct_answer.strip().upper())

    # 统一更新进度：做对 is_passed=True，做错/essay is_passed=False（待巩固）
    PracticeProgress.objects.update_or_create(
        user_id=user_id,
        student_id=current_student_xid,
        template_id=question_id,
        defaults={'is_passed': True if is_correct else False},
    )

    return True, {
        'question_id': question_id,
        'is_correct': is_correct,
        'correct_answer': correct_answer,
    }


def submit_answer(session_id, question_id, user_answer, user_id, advisor_name, answers=None):
    """
    提交答案（支持单题/批量两种模式）
    单题模式: 传 question_id + user_answer
    批量模式: 传 answers=[{question_id, user_answer}, ...]
    参数:
        session_id: 练习会话ID
        question_id: 题目模板ID（单题模式）
        user_answer: 用户提交的答案（单题模式）
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名
        answers: 批量答案列表（批量模式）
    返回值: (success, data_or_error)
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")

    # 批量模式
    if answers:
        # 提前查询同辅导员所有学生，批量模式复用避免 N+1 查询
        batch_all_students = list(Student.objects.filter(advisor_id=user_id))
        results = []
        for item in answers:
            success, result = _process_single_answer(
                item['question_id'], item.get('user_answer', ''),
                user_id, session, all_students=batch_all_students,
            )
            if not success:
                return False, result  # 批量中任一题目校验失败，整体返回错误
            results.append(result)
        return True, {'results': results}

    # 单题模式（兼容旧版）
    return _process_single_answer(question_id, user_answer, user_id, session)


# ============================================================
# 2.3 查看本题答案
# ============================================================

def view_answer(session_id, question_id, user_id, advisor_name):
    """
    查看本题答案（查看后自动标记为错误）
    参数:
        session_id: 练习会话ID
        question_id: 题目模板ID
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容）
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")

    # 校验题目是否属于当前会话（防止查看不属于当前会话的题目答案）
    if question_id not in session.get('template_ids', []):
        return False, (400, f"题目{question_id}不属于当前练习会话")

    # 获取题目模板
    try:
        template = QuestionTemplate.objects.get(id=question_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, "题目不存在")

    # 获取当前学生ID（兼容普通模式/批量模式）
    current_student_xid = _get_current_student_xid(session)
    if current_student_xid is None:
        return False, (400, "当前会话无有效学生")

    # 获取学生对象及同辅导员所有学生，动态生成正确答案
    correct_answer = ''
    try:
        student = Student.objects.get(id=current_student_xid)
        all_students = list(Student.objects.filter(advisor_id=user_id))
        _, correct_answer = _generate_dynamic_options(template, student, all_students)
        correct_answer = correct_answer or ''
    except Student.DoesNotExist:
        correct_answer = ''

    # 查看答案后自动标记为未通过（待巩固）
    PracticeProgress.objects.update_or_create(
        user_id=user_id,
        student_id=current_student_xid,
        template_id=question_id,
        defaults={'is_passed': False},
    )

    return True, {
        'correct_answer': correct_answer,
        'analysis': template.explanation or '',
    }


# ============================================================
# 2.4 下一组题目（换学生）
# ============================================================

def next_group(session_id, user_id, advisor_name):
    """
    换下一组学生，删除旧 session，创建新 session
    参数:
        session_id: 当前练习会话ID
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容）
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")

    # 删除旧会话
    _del_redis(f"{SESSION_PREFIX}{session_id}")

    # 找下一个未全部答对的学生（随机抽取）
    student = _find_next_student(user_id)
    if not student:
        progress = _calc_progress(user_id)
        return True, {
            'session_id': '',
            'student_xid': 0,
            'student_name': '',
            'questions': [],
            'progress': progress,
        }

    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    # 创建新会话
    new_session_id = _next_session_id()
    all_students = list(Student.objects.filter(advisor_id=user_id))
    questions = _generate_questions(student, templates, all_students)

    # 新会话数据存入 Redis
    session_data = {
        'user_id': user_id,
        'student_xid': student.id,
        'student_name': student.name,
        'template_ids': [t.id for t in templates],
    }
    _save_session_data(new_session_id, session_data)
    progress = _calc_progress(user_id)

    return True, {
        'session_id': new_session_id,
        'student_xid': student.id,
        'student_name': student.name,
        'questions': questions,
        'progress': progress,
    }


# ============================================================
# 2.5 重置练习进度
# ============================================================

def reset_progress(user_id):
    """
    清空该辅导员所有答对记录，全部重新进入待练
    参数:
        user_id: 辅导员用户ID
    """
    PracticeProgress.objects.filter(user_id=user_id).delete()
    return True, {}


# ============================================================
# 2.6 练习结果统计
# ============================================================

def get_practice_result(user_id, advisor_name):
    """
    练习结果统计
    参数:
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容）
    """
    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    # 获取该辅导员名下的所有学生（通过 FK advisor_id 匹配）
    students = list(Student.objects.filter(advisor_id=user_id))
    template_ids = [t.id for t in templates]

    # 计算总题数和已通过题数
    total = len(students) * len(templates) if templates and students else 0
    passed = PracticeProgress.objects.filter(
        user_id=user_id,
        template_id__in=template_ids,
        is_passed=True,
    ).count() if template_ids else 0

    # 统计错误题型分布（按学生×模板维度统计每条未通过记录）
    wrong_distribution = {'single': 0, 'multi': 0, 'judge': 0, 'essay': 0}
    redo_count = 0
    if template_ids and students:
        # 查询所有未通过的练习记录，按 template_id 分组统计
        wrong_records = PracticeProgress.objects.filter(
            user_id=user_id,
            template_id__in=template_ids,
            is_passed=False,
        ).values('template_id')
        # 构建 template_id → 题型映射
        template_type_map = {t.id: t.question_type for t in templates}
        for wr in wrong_records:
            qtype = template_type_map.get(wr['template_id'], '')
            if qtype in wrong_distribution:
                wrong_distribution[qtype] += 1
                redo_count += 1

    progress = round(passed / total, 4) if total > 0 else 1.0

    return True, {
        'total_questions': total,
        'passed_questions': passed,
        'progress': progress,
        'wrong_distribution': wrong_distribution,
        'redo_count': redo_count,
    }


# ============================================================
# 3. 收藏夹模块
# ============================================================

def get_favorites_list(user_id, advisor_name, page=1, size=10, sort_type='time_desc', keyword=''):
    """
    3.1 收藏列表（分页），支持按学生姓名搜索
    参数:
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（用于搜索学生）
        page: 页码
        size: 每页数量
        sort_type: 排序方式（time_desc / name_asc）
        keyword: 学生姓名关键词
    """
    # 查询该辅导员的收藏记录
    qs = PracticeFavorite.objects.filter(user_id=user_id)

    # 按学生姓名关键词过滤：先找到匹配的学生ID集合，再筛选收藏记录
    if keyword:
        matching_ids = set(
            Student.objects.filter(
                advisor_id=user_id,
                name__icontains=keyword,
            ).values_list('id', flat=True)
        )
        if matching_ids:
            qs = qs.filter(student_id__in=matching_ids)
        else:
            # 无匹配学生，返回空结果（pages=1 与正常分页逻辑一致）
            return True, {
                'list': [],
                'total': 0,
                'pages': 1,
            }

    # 排序处理
    if sort_type == 'name_asc':
        qs = qs.order_by('student_id', '-created_at')
    else:
        qs = qs.order_by('-created_at')

    # 分页计算
    total = qs.count()
    pages = max(1, math.ceil(total / size))
    items = qs[(page - 1) * size: page * size]

    # 批量获取学生姓名（列表展示用）
    student_ids = list(set(i.student_id for i in items))
    student_map = {}
    if student_ids:
        for s in Student.objects.filter(id__in=student_ids):
            student_map[s.id] = s.name

    # 组装结果列表（直接使用收藏时的快照数据）
    result_list = [
        {
            'favorite_id': i.id,
            'student_xid': i.student_id,
            'student_name': student_map.get(i.student_id, str(i.student_id)),
            'question_title': i.question_title or '',
            'question_type': i.question_type or '',
            'options': i.options or {},
            'correct_answer': i.correct_answer or '',
            'create_time': timezone.localtime(i.created_at).strftime('%Y-%m-%d %H:%M:%S') if i.created_at else '',
        }
        for i in items
    ]
    # name_asc 模式：在 Python 端按学生姓名排序
    if sort_type == 'name_asc':
        result_list.sort(key=lambda x: x['student_name'])

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def add_favorite(session_id, question_id, user_id):
    """
    3.2 收藏题目（收藏时快照保存原题的题干、选项、正确答案）
    参数:
        session_id: 练习会话ID
        question_id: 题目模板ID
        user_id: 辅导员用户ID
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")

    # 获取当前学生ID和姓名（兼容普通模式/批量模式）
    current_student_xid = _get_current_student_xid(session)
    current_student_name = _get_current_student_name(session)
    if current_student_xid is None:
        return False, (400, "当前会话无有效学生")

    # 校验题目是否属于当前会话（防止收藏不属于当前会话的题目）
    if question_id not in session.get('template_ids', []):
        return False, (400, f"题目{question_id}不属于当前练习会话")

    # 检查是否已收藏（幂等操作）
    existing = PracticeFavorite.objects.filter(
        user_id=user_id,
        student_id=current_student_xid,
        template_id=question_id,
    ).first()
    if existing:
        return True, {'favorite_id': existing.id}

    # 获取题目模板，生成原题快照数据
    try:
        template = QuestionTemplate.objects.get(id=question_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, "题目不存在")

    # 获取学生及同辅导员所有学生，动态生成选项和正确答案
    student = Student.objects.get(id=current_student_xid)
    all_students = list(Student.objects.filter(advisor_id=user_id))
    options, correct_answer = _generate_dynamic_options(template, student, all_students)
    correct_answer = correct_answer or ''

    # 渲染题干（将 {name} 替换为学生姓名）
    question_title = template.stem.replace('{name}', current_student_name)

    # 新建收藏记录（含快照数据）
    fav = PracticeFavorite.objects.create(
        user_id=user_id,
        student_id=current_student_xid,
        template_id=question_id,
        question_title=question_title,
        question_type=template.question_type,
        options=options,
        correct_answer=correct_answer,
    )
    return True, {'favorite_id': fav.id}


def remove_favorite(favorite_id, user_id):
    """
    3.3 取消收藏
    参数:
        favorite_id: 收藏记录ID
        user_id: 辅导员用户ID
    """
    try:
        fav = PracticeFavorite.objects.get(id=favorite_id, user_id=user_id)
    except PracticeFavorite.DoesNotExist:
        return False, (404, "收藏记录不存在")
    fav.delete()
    return True, {}


def clear_favorites(user_id):
    """
    3.4 清空收藏
    参数:
        user_id: 辅导员用户ID
    """
    PracticeFavorite.objects.filter(user_id=user_id).delete()
    return True, {}


# ============================================================
# 3.5 收藏题目回放练习
# ============================================================

def replay_favorite(favorite_id, user_answer, user_id):
    """
    3.5 收藏题目回放练习（基于快照数据，不关联练习进度）
    参数:
        favorite_id: 收藏记录ID
        user_answer: 用户提交的答案
        user_id: 辅导员用户ID
    返回值: (success, data_or_error)
        data: {favorite_id, is_correct, correct_answer, question_title, question_type}
    """
    # 校验收藏记录归属
    try:
        fav = PracticeFavorite.objects.get(id=favorite_id, user_id=user_id)
    except PracticeFavorite.DoesNotExist:
        return False, (404, "收藏记录不存在")

    # 校验答案格式（空答案跳过，允许未作答）
    if user_answer.strip():
        valid, err_msg = _validate_answer_format(user_answer, fav.question_type)
        if not valid:
            return False, (400, err_msg)

    # 客观题用快照的正确答案判对错
    is_correct = None
    if fav.question_type in ('single', 'multi', 'judge'):
        if fav.question_type == 'multi':
            # 多选题：归一化后比较，避免 "B,A" vs "A,B" 误判
            is_correct = (
                _normalize_multi_answer(user_answer) == _normalize_multi_answer(fav.correct_answer or '')
            )
        else:
            # 单选题/判断题：直接去空格转大写后比较
            is_correct = (user_answer.strip().upper() == (fav.correct_answer or '').strip().upper())

    return True, {
        'favorite_id': fav.id,
        'is_correct': is_correct,
        'correct_answer': fav.correct_answer or '',
        'question_title': fav.question_title or '',
        'question_type': fav.question_type or '',
    }


# ============================================================
# 4. 多人逐个练习模式
# ============================================================

def start_batch_practice(user_id, advisor_name, count=10):
    """
    4.1 开始多人逐个练习
    随机选取指定数量的学生，按顺序逐个出题
    参数:
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容）
        count: 练习人数（默认10，不足则取实际人数）
    返回值: (success, data_or_error)
    """
    # 获取该辅导员名下的所有学生
    all_students = list(Student.objects.filter(advisor_id=user_id))
    if not all_students:
        return False, (4001, "您名下暂无学生，无法开始练习")

    # 获取所有启用的题目模板
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    if not templates:
        return False, (4002, "暂无启用的题目模板，无法开始练习")

    # 随机选取指定数量的学生（不足则全选）
    actual_count = min(count, len(all_students))
    selected_students = random.sample(all_students, actual_count)

    # 构建学生列表（有序，供逐个遍历）
    student_list = [
        {'student_xid': s.id, 'student_name': s.name}
        for s in selected_students
    ]

    # 为第1个学生生成题目
    first_student = selected_students[0]
    questions = _generate_questions(first_student, templates, all_students)

    # 生成唯一会话ID
    session_id = _next_session_id()

    # 会话数据存入 Redis（TTL=4小时，多人练习时间更长）
    session_data = {
        'user_id': user_id,
        'mode': 'batch',
        'student_list': student_list,
        'current_index': 0,
        'template_ids': [t.id for t in templates],
    }
    _save_session_data(session_id, session_data, ttl=14400)

    progress = _calc_progress(user_id)

    return True, {
        'session_id': session_id,
        'current_index': 0,
        'total_count': actual_count,
        'student_xid': first_student.id,
        'student_name': first_student.name,
        'questions': questions,
        'progress': progress,
    }


def next_person(session_id, user_id, advisor_name):
    """
    4.2 切换到下一个人
    在同一会话中推进 current_index，为下一个学生生成题目
    参数:
        session_id: 练习会话ID
        user_id: 辅导员用户ID
        advisor_name: 辅导员姓名（保留兼容）
    返回值: (success, data_or_error)
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")
    # 校验会话模式
    if session.get('mode') != 'batch':
        return False, (400, "该接口仅适用于多人逐个练习模式")

    # 推进到下一个人
    current_index = session.get('current_index', 0) + 1
    student_list = session.get('student_list', [])

    # 所有人已练习完毕
    if current_index >= len(student_list):
        progress = _calc_progress(user_id)
        return True, {
            'session_id': session_id,
            'current_index': current_index,
            'total_count': len(student_list),
            'student_xid': 0,
            'student_name': '',
            'questions': [],
            'progress': progress,
            'is_finished': True,
        }

    # 获取下一个学生信息
    next_student_info = student_list[current_index]
    next_student_xid = next_student_info['student_xid']

    # 获取学生对象
    try:
        next_student = Student.objects.get(id=next_student_xid)
    except Student.DoesNotExist:
        return False, (404, f"学生{next_student_xid}不存在")

    # 获取题目模板和同辅导员所有学生
    templates = list(QuestionTemplate.objects.filter(is_active=True))
    all_students = list(Student.objects.filter(advisor_id=user_id))

    # 为下一个学生生成题目
    questions = _generate_questions(next_student, templates, all_students)

    # 更新会话中的 current_index
    session['current_index'] = current_index
    _save_session_data(session_id, session, ttl=14400)

    progress = _calc_progress(user_id)

    return True, {
        'session_id': session_id,
        'current_index': current_index,
        'total_count': len(student_list),
        'student_xid': next_student_xid,
        'student_name': next_student_info['student_name'],
        'questions': questions,
        'progress': progress,
        'is_finished': False,
    }


def get_batch_progress(session_id, user_id):
    """
    4.3 查询多人逐个练习的整体进度
    参数:
        session_id: 练习会话ID
        user_id: 辅导员用户ID
    返回值: (success, data_or_error)
    """
    # 校验会话是否存在
    session = _get_session_data(session_id)
    if not session:
        return False, (4034, "练习会话不存在或已过期")
    # 校验会话归属
    if session.get('user_id') != user_id:
        return False, (403, "无权操作此会话")
    # 校验会话模式
    if session.get('mode') != 'batch':
        return False, (400, "该接口仅适用于多人逐个练习模式")

    current_index = session.get('current_index', 0)
    student_list = session.get('student_list', [])

    # 已完成的学生列表
    finished_students = [
        student_list[i]['student_name']
        for i in range(min(current_index, len(student_list)))
    ]

    # 当前学生姓名
    current_student_name = ''
    if current_index < len(student_list):
        current_student_name = student_list[current_index]['student_name']

    return True, {
        'current_index': current_index,
        'total_count': len(student_list),
        'current_student_name': current_student_name,
        'finished_students': finished_students,
        'is_finished': current_index >= len(student_list),
    }
