# -*- coding: utf-8 -*-
# 简答题批改模块 - 业务逻辑层
# 处理待批改列表、分数提交、进度统计、批改日志等核心功能
# 已适配新数据库模型结构：
#   old ExamPaper → new ExamQuestion (考题)
#   old UserExam → new ExamPaper (考试记录)
#   old StudentInfo → new Student

import re
from math import ceil
from functools import reduce
from operator import or_
from django.db.models import Sum, Count, Q
from django.utils import timezone

# 新模型导入
from django.contrib.auth import get_user_model
User = get_user_model()
from apps.exam.models import Exam, ExamQuestion, ExamAnswer, ExamPaper, GradePublish
from apps.system.models import Student, QuestionTemplate, SystemLog
from apps.correct.ai_grader import STUDENT_FIELD_LABELS, ai_grade_batch_for_exam, ai_grade_one_answer
from apps.correct.models import AIGradeConfig, AIGradeLog

# 主观题类型常量
SUBJECTIVE_TYPE = 'essay'



def _get_standard_answer(question_item):
    """
    获取简答题的标准答案 - 返回对应学生信息表中文字段键值对
    排除辅导员名字、辅导员电话、辅导员ID、照片地址
    参数：
        question_item: ExamQuestion 实例
    返回：学生信息中文字段键值对字典，无学生时返回空字典
    """
    student = question_item.student
    if not student:
        return {}

    result = {}
    for field, label in STUDENT_FIELD_LABELS.items():
        value = getattr(student, field, None)
        if field in ('is_academic_difficulty', 'is_financial_difficulty'):
            # 布尔字段转为"是"/"否"
            value = '是' if value else '否'
        elif value is None:
            value = ''
        else:
            value = str(value)
        result[label] = value
    return result


def _check_grader_allocation(question_item, grader_user):
    """
    检查批改分配权限
    规则：
      1. 优先检查试卷是否在考试创建时已分配批改员
      2. 若已分配且当前用户不是分配批改员，拒绝批改
      3. 若未分配（旧数据兼容），则检查是否已被其他批改员批改（先到先得）
    参数：
        question_item: ExamQuestion 实例
        grader_user: 当前登录的批改员 (User 实例)
    返回：(is_allowed, error_tuple_or_none)
    """
    # 查询该考生的试卷记录
    try:
        paper = ExamPaper.objects.get(
            exam_id=question_item.exam_id,
            user_id=question_item.user_id,
        )
    except ExamPaper.DoesNotExist:
        return False, (404, "考试记录不存在")

    # 若试卷已分配批改员且当前用户不是该批改员，拒绝
    if paper.assigned_grader_id is not None:
        if paper.assigned_grader_id != grader_user.id:
            return False, (4031, "该试卷未分配给您批改")
        return True, None

    # 旧数据兼容：未分配批改员时，检查是否已被其他批改员抢先批改
    existing = ExamAnswer.objects.filter(
        question_id__in=ExamQuestion.objects.filter(
            exam_id=question_item.exam_id,
            user_id=question_item.user_id,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True),
        graded_by_id__isnull=False,
    ).exclude(graded_by_id=grader_user.id).first()

    if existing is not None:
        return False, (4031, "该考生考题已被其他批改员批改，不可重复批改")

    return True, None


def get_correct_list(exam_id=None, page=1, size=10, grader_user=None):
    """
    获取待批改列表（支持分页）
    接口：GET /api/correct/list/
    权限：批改员（role=2）、超级管理员（role=3）
    批改员仅能看到分配给自己批改的题目，超管可以看到所有题目
    参数：
        exam_id: 可选，按考试筛选
        page: 页码，默认1
        size: 每页条数，默认10，最大50
        grader_user: 当前登录用户（用于角色判断和分配过滤）
    返回：
        (success, data_or_error)
    """
    # 查询已交卷的试卷记录
    paper_qs = ExamPaper.objects.filter(status=2)

    # 批改员（role=2）仅能看到分配给自己批改的试卷
    if grader_user and grader_user.role == 2:
        paper_qs = paper_qs.filter(assigned_grader_id=grader_user.id)

    # 排除批改员已发布成绩的考试（未传exam_id时）
    if grader_user and grader_user.role == 2 and not exam_id:
        published_exam_ids = set(
            GradePublish.objects.filter(
                grader_id=grader_user.id,
            ).values_list('exam_id', flat=True)
        )
        if published_exam_ids:
            paper_qs = paper_qs.exclude(exam_id__in=published_exam_ids)

    if exam_id:
        paper_qs = paper_qs.filter(exam_id=exam_id)

        # 批改员已发布则不再返回该考试的待批改列表
        if grader_user and grader_user.role == 2:
            if GradePublish.objects.filter(
                exam_id=exam_id,
                grader_id=grader_user.id,
            ).exists():
                return True, {
                    'list': [],
                    'total': 0,
                    'pages': 0,
                }

    # 获取已交卷试卷对应的(exam_id, user_id)键值对
    paper_pairs = list(paper_qs.values_list('exam_id', 'user_id'))
    if not paper_pairs:
        return True, {
            'list': [],
            'total': 0,
            'pages': 0,
        }

    # 构建 OR 条件匹配(exam_id, user_id)对，找到对应简答题
    pair_conditions = reduce(or_, (
        Q(exam_id=eid, user_id=uid) for eid, uid in paper_pairs
    ))
    essay_questions = ExamQuestion.objects.filter(
        pair_conditions,
        question_type=SUBJECTIVE_TYPE,
    )

    # 旧: paper_id → 新: id
    essay_question_ids = essay_questions.values_list('id', flat=True)

    # 查询所有答案（含已批改和未批改），发布前可修改分数
    queryset = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
    )

    # 统计总数
    total = queryset.count()
    pages = ceil(total / size) if total > 0 else 0

    # 分页（旧: answer_id → 新: id）
    offset = (page - 1) * size
    answer_list = list(queryset.order_by('id')[offset:offset + size])

    if not answer_list:
        return True, {
            'list': [],
            'total': total,
            'pages': pages,
        }

    # 批量查询 ExamQuestion 数据，构建 id -> question 映射
    # 使用 select_related 预加载 User 信息，避免 N+1 查询
    # 旧: paper_id → 新: id；旧: ExamPaper → 新: ExamQuestion
    question_ids = [a.question_id for a in answer_list]
    question_map = {
        q.id: q
        for q in ExamQuestion.objects.filter(id__in=question_ids).select_related('user', 'student')
    }

    # 收集所有考生 user_id，用于批量查询 ExamPaper
    # 旧: teacher_gh → 新: user_id
    user_id_set = set()
    for question in question_map.values():
        user_id_set.add(question.user_id)

    # 批量查询 ExamPaper（旧: UserExam），构建 (exam_id, user_id) -> exam_paper 映射
    # 旧: teacher_gh → 新: user_id
    exam_paper_map = {}
    if user_id_set:
        exam_ids_set = set(q.exam_id for q in question_map.values())
        for ep in ExamPaper.objects.filter(
            exam_id__in=exam_ids_set,
            user_id__in=user_id_set,
        ):
            # 旧: (ue.exam_id, ue.teacher_gh) → 新: (ep.exam_id, ep.user_id)
            exam_paper_map[(ep.exam_id, ep.user_id)] = ep

    # 批量查询已批改主观题得分：按 (exam_id, user_id) 聚合
    # 旧: key_set = (exam_id, teacher_gh)；新: key_set = (exam_id, user_id)
    key_set = set()
    for a in answer_list:
        q = question_map.get(a.question_id)
        if q:
            key_set.add((q.exam_id, q.user_id))

    graded_score_map = {}
    if key_set:
        # 按 (exam_id, user_id) 分组：构建 OR 条件一次性查询所有相关考题
        # 旧: teacher_gh → 新: user_id
        conditions = reduce(or_, (
            Q(exam_id=exam_id_val, user_id=user_id_val)
            for exam_id_val, user_id_val in key_set
        ))
        # 旧: ExamPaper → 新: ExamQuestion；旧: paper_id → 新: id
        all_essay_questions = ExamQuestion.objects.filter(
            conditions,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True)

        if all_essay_questions:
            # 旧: paper_id__in → 新: question_id__in；旧: score_got → 新: score
            graded_scores = ExamAnswer.objects.filter(
                question_id__in=all_essay_questions,
                score__isnull=False,
            ).values_list('question_id', 'score')
            # 构建 question_id -> (exam_id, user_id) 映射用于分组聚合
            # 旧: paper_id → 新: id；旧: teacher_gh → 新: user_id
            question_to_key = {}
            for q in ExamQuestion.objects.filter(id__in=all_essay_questions):
                question_to_key[q.id] = (q.exam_id, q.user_id)
            for gs_question_id, gs_score in graded_scores:
                key = question_to_key.get(gs_question_id)
                if key:
                    graded_score_map[key] = graded_score_map.get(key, 0) + gs_score

    # 构建返回数据
    result_list = []
    for answer in answer_list:
        question_item = question_map.get(answer.question_id)
        if not question_item:
            continue

        # 获取考生姓名（从预加载的 User 对象中取）
        # 旧: user_map.get(teacher_gh) → 新: question_item.user.display_name
        examiner_name = question_item.user.display_name or question_item.user.username if question_item.user else ''

        # 计算当前总得分
        # 旧: (exam_id, teacher_gh) → 新: (question_item.exam_id, question_item.user_id)
        key = (question_item.exam_id, question_item.user_id)
        ep = exam_paper_map.get(key)
        # 旧: obj_score → 新: objective_score
        obj_score = ep.objective_score if ep else 0
        subj_score = graded_score_map.get(key, 0)
        current_total_score = float(obj_score + subj_score)

        # 获取标准答案
        standard_answer = _get_standard_answer(question_item)

        result_list.append({
            'answer_id': answer.id,                          # 旧: answer.answer_id
            'question_title': question_item.question_text,
            'user_answer': answer.content or '',             # 旧: answer.answer_content
            'standard_answer': standard_answer,
            'examiner_name': examiner_name,
            'current_total_score': current_total_score,
            'existing_score': answer.score,                  # 已批改分数（null表示未批改）
            'existing_remark': answer.remark or '',          # 已批改备注
        })

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def submit_score(answer_id, score, remark, grader_user):
    """
    提交/修改批改分数（合并接口，幂等）
    接口：PUT /api/correct/score/{answer_id}/
    权限：批改员（role=2）、超级管理员（role=3）
    参数：
        answer_id: 答案ID
        score: 批改分数
        remark: 批改备注（可选）
        grader_user: 当前登录的批改员 (User 实例)
    返回：
        (success, data_or_error)
    """
    # 1. 校验 answer_id 存在且为简答题
    # 旧: answer_id=answer_id → 新: id=answer_id
    try:
        answer = ExamAnswer.objects.get(id=answer_id)
    except ExamAnswer.DoesNotExist:
        return False, (404, "答案记录不存在")

    # 旧: ExamPaper → 新: ExamQuestion；旧: paper_id → 新: id
    try:
        question_item = ExamQuestion.objects.get(id=answer.question_id)
    except ExamQuestion.DoesNotExist:
        return False, (404, "试卷题目不存在")

    if question_item.question_type != SUBJECTIVE_TYPE:
        return False, (400, "该题目不是简答题，无法批改")

    # 2. 校验该考生考试状态为已交卷
    # 旧: UserExam → 新: ExamPaper；旧: teacher_gh → 新: user_id
    try:
        exam_paper = ExamPaper.objects.get(
            exam_id=question_item.exam_id,
            user_id=question_item.user_id,
        )
    except ExamPaper.DoesNotExist:
        return False, (404, "考试记录不存在")

    if exam_paper.status != 2:
        return False, (400, "该考生尚未交卷，无法批改")

    # 3. 检查批改分配权限（超管可绕过分配限制）
    if grader_user.role != 3:
        is_allowed, alloc_error = _check_grader_allocation(question_item, grader_user)
        if not is_allowed:
            return False, alloc_error

    # 3.5 已发布成绩后禁止修改分数（超管除外）
    if grader_user.role != 3:
        if GradePublish.objects.filter(
            exam_id=question_item.exam_id,
            grader_id=grader_user.id,
        ).exists():
            return False, (403, "已发布成绩，无法修改批改分数")

    # 4. 校验分数不超过题目分值
    if score < 0:
        return False, (400, "分数不能为负数")
    if score > question_item.score:
        return False, (400, f"分数不能超过题目分值({question_item.score}分)")

    # 5. 更新批改记录（含批改备注）
    # 旧: score_got → 新: score；旧: grader_id → 新: graded_by
    # 旧: grade_time → 新: graded_at
    answer.score = int(score)
    answer.graded_by = grader_user
    answer.graded_at = timezone.now()
    answer.remark = remark or ''
    answer.save(update_fields=['score', 'graded_by', 'graded_at', 'remark'])

    # 6. 写入批改日志到 system_log
    # 旧: user_id → 新: operator
    SystemLog.objects.create(
        operator=grader_user,
        module='correct',
        action='grade',
        target=f"answer_id={answer_id}",
        content=f"批改员 {grader_user.username} 批改答案 {answer_id}，"
                f"得分 {score}，备注：{remark or '无'}",
    )

    # 7. 重新计算该学生主观题总分和总成绩
    # 旧: paper_id__in + ExamPaper → 新: question_id__in + ExamQuestion
    # 旧: teacher_gh → 新: user_id；旧: score_got → 新: score
    subj_result = ExamAnswer.objects.filter(
        question_id__in=ExamQuestion.objects.filter(
            exam_id=question_item.exam_id,
            user_id=question_item.user_id,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True),
        score__isnull=False,
    ).aggregate(total=Sum('score'))

    subj_total = subj_result['total'] or 0
    # 旧: subj_score → 新: subjective_score；旧: obj_score → 新: objective_score
    exam_paper.subjective_score = subj_total
    exam_paper.total_score = exam_paper.objective_score + subj_total

    # 8. 检查是否所有简答题都已批改完成
    # 旧: score_got__isnull → 新: score__isnull
    ungraded_essay_count = ExamAnswer.objects.filter(
        question_id__in=ExamQuestion.objects.filter(
            exam_id=question_item.exam_id,
            user_id=question_item.user_id,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True),
        score__isnull=True,
    ).count()

    exam_paper.is_graded = 1 if ungraded_essay_count == 0 else 0
    exam_paper.save(update_fields=['subjective_score', 'total_score', 'is_graded'])

    return True, {}


def get_correct_progress(exam_id=None, grader_user=None):
    """
    批改进度统计
    接口：GET /api/correct/progress/
    权限：批改员（role=2）、超级管理员（role=3）
    批改员仅统计分配给自己批改的试卷
    参数：
        exam_id: 可选，按考试筛选
        grader_user: 当前登录用户（用于角色判断和分配过滤）
    返回：
        (success, data_or_error)
        data: {total, corrected, progress, corrector_progress, uncorrected_preview}
    """
    # 查询所有已交卷考试中的简答题
    paper_qs = ExamPaper.objects.filter(status=2)

    # 批改员（role=2）仅统计分配给自己批改的试卷
    if grader_user and grader_user.role == 2:
        paper_qs = paper_qs.filter(assigned_grader_id=grader_user.id)

    if exam_id:
        paper_qs = paper_qs.filter(exam_id=exam_id)

    paper_pairs = list(paper_qs.values_list('exam_id', 'user_id'))
    if not paper_pairs:
        return True, {
            'total': 0,
            'corrected': 0,
            'progress': 0.0,
            'corrector_progress': {},
            'uncorrected_preview': [],
        }

    # 构建 OR 条件匹配(exam_id, user_id)对，找到对应简答题
    pair_conditions = reduce(or_, (
        Q(exam_id=eid, user_id=uid) for eid, uid in paper_pairs
    ))
    essay_questions = ExamQuestion.objects.filter(
        pair_conditions,
        question_type=SUBJECTIVE_TYPE,
    )

    # 旧: paper_id → 新: id
    essay_question_ids = list(essay_questions.values_list('id', flat=True))

    if not essay_question_ids:
        return True, {
            'total': 0,
            'corrected': 0,
            'progress': 0.0,
            'corrector_progress': {},
            'uncorrected_preview': [],
        }

    # 统计总数和已批改数
    # 旧: paper_id__in → 新: question_id__in；旧: score_got__isnull → 新: score__isnull
    total = ExamAnswer.objects.filter(question_id__in=essay_question_ids).count()
    corrected = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
        score__isnull=False,
    ).count()

    progress = round(corrected / total, 2) if total > 0 else 0.0

    # 按批改员统计进度
    # 旧: grader_id → 新: graded_by_id；旧: answer_id → 新: id
    grader_stats = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
        score__isnull=False,
        graded_by_id__isnull=False,
    ).values('graded_by_id').annotate(
        corrected_count=Count('id'),
    )

    corrector_progress = {}
    for stat in grader_stats:
        grader_id_val = stat['graded_by_id']  # 旧: stat['grader_id']
        try:
            # 旧: user_id → 新: id
            grader_user_obj = User.objects.get(id=grader_id_val)
            grader_name = grader_user_obj.username
        except User.DoesNotExist:
            grader_name = str(grader_id_val)
        corrector_progress[grader_name] = round(stat['corrected_count'] / total, 2) if total > 0 else 0.0

    # 未批改预览（最多返回5条）
    ungraded_preview = []
    # 旧: paper_id__in → 新: question_id__in；旧: score_got__isnull → 新: score__isnull
    # 旧: order_by('answer_id') → 新: order_by('id')
    ungraded_answers = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
        score__isnull=True,
    ).order_by('id')[:5]

    for answer in ungraded_answers:
        try:
            # 旧: ExamPaper → 新: ExamQuestion；旧: paper_id → 新: id
            # 使用 select_related 预加载 User 避免 N+1 查询
            question_item = ExamQuestion.objects.select_related('user').get(id=answer.question_id)
            # 旧: teacher_gh → 新: user (FK)，直接访问 user.display_name
            examiner_name = ''
            if question_item.user:
                # 旧: name → 新: display_name
                examiner_name = question_item.user.display_name or question_item.user.username
            ungraded_preview.append({
                'answer_id': answer.id,  # 旧: answer.answer_id
                'question_title': question_item.question_text[:100],
                'examiner_name': examiner_name,
            })
        except ExamQuestion.DoesNotExist:
            continue

    return True, {
        'total': total,
        'corrected': corrected,
        'progress': progress,
        'corrector_progress': corrector_progress,
        'uncorrected_preview': ungraded_preview,
    }


def get_correct_logs(exam_id=None, grader_id=None, page=1, size=10):
    """
    批改日志查询
    接口：GET /api/correct/log/list/
    权限：仅超级管理员（role=3）
    参数：
        exam_id: 可选，按考试筛选
        grader_id: 可选，按批改员筛选
        page: 页码，默认1
        size: 每页条数，默认10，最大50
    返回：
        (success, data_or_error)
        data: {list, total, pages}
    """
    # 查询批改相关日志
    queryset = SystemLog.objects.filter(module='correct', action='grade')

    # 旧: user_id → 新: operator_id
    if grader_id:
        queryset = queryset.filter(operator_id=grader_id)

    # exam_id 筛选：通过日志内容中的 answer_id 关联查询
    # 日志 target 字段存储 "answer_id=xxx"
    if exam_id:
        # 查询该考试下所有简答题的 ID
        # 旧: ExamPaper → 新: ExamQuestion；旧: paper_id → 新: id
        essay_question_ids = ExamQuestion.objects.filter(
            exam_id=exam_id,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True)
        # 查询这些考题对应的答案 ID
        # 旧: paper_id__in → 新: question_id__in；旧: answer_id → 新: id
        matching_answer_ids = ExamAnswer.objects.filter(
            question_id__in=essay_question_ids,
        ).values_list('id', flat=True)

        # 构建 target 筛选条件
        target_filters = [f"answer_id={aid}" for aid in matching_answer_ids]
        if target_filters:
            queryset = queryset.filter(target__in=target_filters)
        else:
            return True, {
                'list': [],
                'total': 0,
                'pages': 0,
            }

    # 统计总数
    total = queryset.count()
    pages = ceil(total / size) if total > 0 else 0

    # 分页
    # 旧: create_time → 新: created_at
    offset = (page - 1) * size
    log_list = queryset.order_by('-created_at')[offset:offset + size]

    # 构建返回数据
    result_list = []
    for log in log_list:
        # 用正则从 target 字段提取 answer_id，格式 "answer_id=301"（兼容格式变化）
        answer_id = None
        if log.target:
            match = re.search(r'answer_id=(\d+)', log.target)
            if match:
                try:
                    answer_id = int(match.group(1))
                except ValueError:
                    pass

        # 用正则从 content 中提取备注（格式 "...备注：xxx"，兼容中英文冒号）
        remark = ''
        if log.content:
            remark_match = re.search(r'备注[：:](.*)', log.content)
            if remark_match:
                remark = remark_match.group(1).strip()

        # 获取批改员名称
        # 旧: user_id → 新: operator_id
        grader_name = ''
        if log.operator_id:
            try:
                # 旧: user_id → 新: id
                grader_user = User.objects.get(id=log.operator_id)
                grader_name = grader_user.display_name or grader_user.username
            except User.DoesNotExist:
                grader_name = str(log.operator_id)

        # 获取实际得分
        score_value = None
        if answer_id:
            try:
                # 旧: answer_id → 新: id
                answer = ExamAnswer.objects.get(id=answer_id)
                # 旧: score_got → 新: score
                score_value = answer.score
            except ExamAnswer.DoesNotExist:
                pass

        result_list.append({
            'log_id': log.id,
            'answer_id': answer_id,
            'grader_name': grader_name,
            'score': score_value,
            'remark': remark,
            # 旧: create_time → 新: created_at
            'grade_time': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
        })

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def publish_scores(exam_id, grader_user):
    """
    批改员发布某场考试的成绩
    接口：POST /api/correct/publish/{exam_id}/
    权限：批改员（role=2）、超管（role=3）
    role=2: 检查是否还有分配给该批改员且已交卷的试卷中未批改的主观题，全部改完才能发布
    role=3: 超管可以一键发布所有成绩，直接替所有批改员发布，即使试卷未全部改完也能发布
    已发布则返回 400（幂等）
    """
    # 检查考试是否存在
    if not Exam.objects.filter(id=exam_id).exists():
        return False, (404, "考试不存在")

    grader_name = grader_user.display_name or grader_user.username

    # ===== 超级管理员（role=3）：一键发布所有批改员的成绩 =====
    if grader_user.role == 3:
        # 获取该考试所有已分配的批改员
        grader_ids = set(
            ExamPaper.objects.filter(exam_id=exam_id)
            .exclude(assigned_grader__isnull=True)
            .values_list('assigned_grader_id', flat=True)
        )
        if not grader_ids:
            return False, (400, "该考试没有分配批改员，无需发布")

        # 获取已发布的批改员
        published_ids = set(
            GradePublish.objects.filter(exam_id=exam_id)
            .values_list('grader_id', flat=True)
        )

        # 所有批改员都已发布 → 幂等
        if grader_ids == published_ids:
            return False, (400, "该考试所有批改员均已发布成绩，无需重复发布")

        # 为尚未发布的批改员创建发布记录
        unpublished_ids = grader_ids - published_ids
        GradePublish.objects.bulk_create([
            GradePublish(exam_id=exam_id, grader_id=gid)
            for gid in unpublished_ids
        ])

        SystemLog.objects.create(
            operator=grader_user,
            module='correct',
            action='publish',
            target=f'exam_id={exam_id}',
            content=f'超级管理员 {grader_name} 一键发布了考试{exam_id}的全部成绩（共替{len(unpublished_ids)}位批改员发布）',
        )
        return True, {}

    # ===== 管理员（role=2）：检查是否还有未批改的题目 =====

    # 幂等检查：该批改员是否已发布
    if GradePublish.objects.filter(exam_id=exam_id, grader_id=grader_user.id).exists():
        return False, (400, "已发布过成绩，无需重复发布")

    paper_qs = ExamPaper.objects.filter(
        exam_id=exam_id,
        assigned_grader_id=grader_user.id,
        status=2,
    )
    if not paper_qs.exists():
        return False, (400, "您在该考试中没有需要批改的试卷")
    paper_pairs = list(paper_qs.values_list('exam_id', 'user_id'))

    # 构建 OR 条件查询未批改主观题
    or_conditions = [Q(exam_id=eid, user_id=uid) for eid, uid in paper_pairs]
    essay_question_ids = ExamQuestion.objects.filter(
        reduce(or_, or_conditions),
        question_type=SUBJECTIVE_TYPE,
    ).values_list('id', flat=True)

    ungraded_count = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
        score__isnull=True,
    ).count()

    if ungraded_count > 0:
        return False, (400, f"还有{ungraded_count}道题目未批改，请批改完成后再发布")

    # 创建发布记录
    GradePublish.objects.create(exam_id=exam_id, grader_id=grader_user.id)

    # 记录操作日志
    SystemLog.objects.create(
        operator=grader_user,
        module='correct',
        action='publish',
        target=f'exam_id={exam_id}',
        content=f'批改员 {grader_name} 发布了考试{exam_id}的成绩',
    )

    return True, {}


# ==================== AI 批改业务函数 ====================

def get_ai_config():
    """
    获取 AI 批改全局配置
    接口：GET /api/correct/ai-config/
    权限：超级管理员（role=3）
    返回：
        (True, config_dict) — 包含当前配置（不存在则返回空默认值）
    """
    config = AIGradeConfig.objects.first()
    if not config:
        return True, {
            'id': None,
            'provider_name': '',
            'api_url': '',
            'api_key': '',
            'model_name': '',
            'temperature': 0.1,
            'max_tokens': 2000,
            'system_prompt': '',
            'is_active': False,
        }

    return True, {
        'id': config.id,
        'provider_name': config.provider_name,
        'api_url': config.api_url,
        'api_key': config.api_key,
        'model_name': config.model_name,
        'temperature': config.temperature,
        'max_tokens': config.max_tokens,
        'system_prompt': config.system_prompt,
        'is_active': config.is_active,
    }


def update_ai_config(data):
    """
    更新 AI 批改全局配置
    接口：PUT /api/correct/ai-config/
    权限：超级管理员（role=3）
    若不存在配置则创建，若存在则更新
    参数：
        data: dict，含可选的配置字段
    返回：
        (True, {})
    """
    config = AIGradeConfig.objects.first()
    if not config:
        AIGradeConfig.objects.create(
            provider_name=data.get('provider_name', ''),
            api_url=data.get('api_url', ''),
            api_key=data.get('api_key', ''),
            model_name=data.get('model_name', ''),
            temperature=data.get('temperature', 0.1),
            max_tokens=data.get('max_tokens', 2000),
            system_prompt=data.get('system_prompt', ''),
            is_active=data.get('is_active', False),
        )
        return True, {}

    # 更新已有配置
    updatable_fields = [
        'provider_name', 'api_url', 'api_key', 'model_name',
        'temperature', 'max_tokens', 'system_prompt', 'is_active',
    ]
    for field in updatable_fields:
        if field in data:
            setattr(config, field, data[field])
    config.save(update_fields=[f for f in updatable_fields if f in data])
    return True, {}


def test_ai_config():
    """
    测试 AI 连接
    接口：POST /api/correct/ai-config/test/
    权限：超级管理员（role=3）
    使用当前保存的配置发送一条简单的测试请求
    返回：
        (True, {'success': True, 'message': str})
        (True, {'success': False, 'message': str})
    """
    config = AIGradeConfig.objects.first()
    if not config or not config.api_url or not config.api_key:
        return True, {'success': False, 'message': 'AI配置未完成：请先设置 API 地址和密钥'}

    import httpx
    import json

    test_payload = {
        'model': config.model_name,
        'messages': [
            {'role': 'system', 'content': '你是一个测试助手。'},
            {'role': 'user', 'content': '请回复 "OK" 表示连接正常。'},
        ],
        'temperature': 0.0,
        'max_tokens': 50,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                config.api_url,
                headers={
                    'Authorization': f'Bearer {config.api_key}',
                    'Content-Type': 'application/json',
                },
                json=test_payload,
            )
            if response.status_code == 200:
                return True, {'success': True, 'message': 'AI 连接测试成功'}
            else:
                return True, {'success': False, 'message': f'API 返回 HTTP {response.status_code}: {response.text[:300]}'}
    except httpx.RequestError as e:
        return True, {'success': False, 'message': f'网络请求失败: {str(e)}'}
    except Exception as e:
        return True, {'success': False, 'message': f'测试异常: {str(e)}'}


def toggle_exam_ai_grade(exam_id, enabled):
    """
    开启/关闭某考试的 AI 批改
    接口：PUT /api/correct/ai-grade/toggle/{exam_id}/
    权限：超级管理员（role=3）
    参数：
        exam_id: 考试 ID
        enabled: True=开启, False=关闭
    返回：
        (success, (code, msg))
    """
    from apps.exam.models import Exam, ExamStatus

    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    if exam.status == ExamStatus.CLOSED:
        return False, (400, "考试已关闭，无法修改 AI 批改设置")

    exam.ai_grade_enabled = enabled
    exam.save(update_fields=['ai_grade_enabled'])

    # 若考试已结束且开启 AI 批改，立即触发
    if enabled and exam.status == ExamStatus.ENDED:
        total, success, failed = ai_grade_batch_for_exam(exam_id)
        return True, (200, f"AI 批改设置已开启，批改完成：共 {total} 题，成功 {success} 题，失败 {failed} 题")

    if enabled:
        return True, (200, "AI 批改已开启，考试结束后将自动执行")
    else:
        return True, (200, "AI 批改已关闭")


def get_ai_grade_logs(exam_id=None, status=None, page=1, size=10):
    """
    查询 AI 批改日志
    接口：GET /api/correct/ai-grade/logs/
    权限：超级管理员（role=3）
    参数：
        exam_id: 可选，按考试筛选
        status: 可选，success / failed
        page: 页码
        size: 每页条数
    返回：
        (True, {list, total, pages})
    """
    from math import ceil
    from apps.exam.models import ExamAnswer, ExamQuestion

    queryset = AIGradeLog.objects.all().order_by('-created_at')

    # 按考试筛选：通过 answer_id → question_id → exam_id
    if exam_id:
        essay_question_ids = ExamQuestion.objects.filter(
            exam_id=exam_id,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True)
        answer_ids = ExamAnswer.objects.filter(
            question_id__in=essay_question_ids,
        ).values_list('id', flat=True)
        queryset = queryset.filter(answer_id__in=answer_ids)

    # 按状态筛选
    if status:
        queryset = queryset.filter(status=status)

    total = queryset.count()
    pages = ceil(total / size) if total > 0 else 0

    offset = (page - 1) * size
    log_list = queryset[offset:offset + size]

    result_list = []
    for log in log_list:
        # 获取关联的题目信息
        question_title = ''
        examiner_name = ''
        try:
            answer = ExamAnswer.objects.select_related(
                'question__user'
            ).get(id=log.answer_id)
            question_title = answer.question.question_text[:100] if answer.question else ''
            if answer.question and answer.question.user:
                examiner_name = answer.question.user.display_name or answer.question.user.username
        except ExamAnswer.DoesNotExist:
            pass

        result_list.append({
            'log_id': log.id,
            'answer_id': log.answer_id,
            'question_title': question_title,
            'examiner_name': examiner_name,
            'model_name': log.model_name,
            'score_returned': log.score_returned,
            'remark_returned': log.remark_returned,
            'latency_ms': log.latency_ms,
            'status': log.status,
            'error_msg': log.error_msg[:200] if log.error_msg else '',
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
        })

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def trigger_ai_grading_for_exam(exam_id):
    """
    触发某考试的 AI 批改（供 exam 模块考试结束时调用）
    检查全局配置和考试开关后执行批改
    参数：
        exam_id: 考试 ID
    """
    # 检查全局配置是否启用
    config = AIGradeConfig.objects.first()
    if not config or not config.is_active:
        return

    # 检查考试开关是否启用
    from apps.exam.models import Exam, ExamStatus
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return

    if not exam.ai_grade_enabled:
        return

    # 只在考试已结束时触发
    if exam.status != ExamStatus.ENDED:
        return

    # 执行批改
    ai_grade_batch_for_exam(exam_id)
