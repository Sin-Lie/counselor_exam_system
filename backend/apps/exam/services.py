# -*- coding: utf-8 -*-
# 考试模块 - 业务逻辑层
# 处理考试列表、进入考试、答题保存、交卷判分、防作弊等核心功能

import base64
import json
import os
import random
import re
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Exam, ExamQuestion, ExamAnswer, ExamPaper, CheatLog, ExamStatus
from apps.system.models import Student
from utils.redis_client import RedisClient

# 图片文件扩展名正则（用于判断选项值是否为图片路径）
IMAGE_EXT_PATTERN = re.compile(r'\.(jpg|jpeg|png|gif|webp|bmp)$', re.IGNORECASE)

NO_DORM_ADDRESS_VALUES = {
    '',
    '-',
    '--',
    '/',
    'na',
    'n/a',
    'none',
    'null',
    '无',
    '暂无',
    '没有',
    '无寝室',
    '无宿舍',
    '无住宿',
    '没有寝室',
    '没有宿舍',
    '未安排',
    '未安排寝室',
    '未安排宿舍',
    '未分配',
    '未分配寝室',
    '未分配宿舍',
    '未入住',
    '不住校',
    '不住宿',
    '校外住宿',
    '走读',
}

# 图片扩展名 → MIME 类型映射
MIME_TYPE_MAP = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
}

# 考试状态 → 接口枚举字符串的映射
STATUS_MAP = {
    ExamStatus.NOT_PUBLISHED: 'not_started',
    ExamStatus.IN_PROGRESS: 'normal',
    ExamStatus.ENDED: 'ended',
    ExamStatus.CLOSED: 'closed',
}

# 客观题类型：单选、多选、判断（交卷时自动判分）
OBJECTIVE_TYPES = ('single', 'multi', 'judge')

# 主观题类型：简答题（需人工批改）
SUBJECTIVE_TYPES = ('essay',)

# 学生信息字段中文映射 — 用于生成简答题参考答案
STUDENT_FIELD_LABELS = {
    'id': '学号',
    'name': '姓名',
    'gender': '性别',
    'college': '学院',
    'grade': '年级',
    'class_name': '班级',
    'ethnicity': '民族',
    'native_place': '籍贯',
    'origin_place': '生源地',
    'family_address': '家庭所在地',
    'household_address': '户籍所在地',
    'is_academic_difficulty': '是否学业困难',
    'religion': '宗教信仰',
    'dorm_address': '住宿地址',
    'off_campus_address': '校外住宿地址',
    'is_financial_difficulty': '是否经济困难',
    'enrollment_status': '学籍状态',
}

# 防作弊阈值配置
MAX_CHEAT_COUNT = 3        # 切屏累计超过3次强制交卷
MAX_CHEAT_DURATION = 10    # 单次切出超过10秒强制交卷
CHEAT_COUNTER_TTL = 7200   # 防作弊计数器过期时间（2小时）


def _normalize_native_place(value):
    if not value:
        return value
    value = str(value).strip()

    if '浙江' in value:
        match = re.search(r'浙江(?:省)?(.{2,3}市)', value)
        if match:
            return '浙江省' + match.group(1)
        if value.startswith('浙江省'):
            return value
        return value

    match = re.search(
        r'^(.{2,3}省|.+?自治区|香港|澳门|北京|天津|上海|重庆)',
        value,
    )
    if match:
        return match.group(1)

    return value


def _auto_transition_exam_status(exam):
    """
    根据当前时间自动流转考试状态
    若考试已过结束时间但状态仍为「进行中」，自动标记为「已结束」
    返回是否发生了状态变更
    """
    now = timezone.now()
    exam_end = exam.start_time + timedelta(minutes=exam.duration_minutes)

    if exam.status == ExamStatus.NOT_PUBLISHED and now >= exam.start_time and now < exam_end:
        # 未发布但已到开始时间 → 自动发布为进行中（管理员未手动发布时兜底）
        exam.status = ExamStatus.IN_PROGRESS
        exam.save(update_fields=['status'])
        return True

    if exam.status == ExamStatus.IN_PROGRESS and now >= exam_end:
        # 进行中但已过结束时间 → 自动标记为已结束
        exam.status = ExamStatus.ENDED
        exam.save(update_fields=['status'])

        # 触发 AI 自动批改（在状态变更后执行）
        _trigger_ai_grading_if_enabled(exam)

        return True

    return False


def get_exam_list(user_id=None):
    """
    获取考试列表
    接口：GET /api/exam/list/
    权限：辅导员（role=1）
    返回未删除的考试（排除状态为3=已关闭/已删除的考试），按发布日期倒序
    user_id 不为空时，结合 exam_papers 表判断考生个人的考试状态
    """
    # 排除已删除(status=3)的考试
    exams = Exam.objects.exclude(status=ExamStatus.CLOSED).order_by('-release_date')

    # 一次查询获取该用户所有考试的 ExamPaper 状态和paper_id，避免 N+1 查询
    paper_status_map = {}
    paper_id_map = {}
    if user_id is not None:
        papers = ExamPaper.objects.filter(
            exam__in=exams, user_id=user_id
        ).values('id', 'exam_id', 'status')
        paper_status_map = {p['exam_id']: p['status'] for p in papers}
        paper_id_map = {p['exam_id']: p['id'] for p in papers}

    exam_list = []
    for exam in exams:
        # 自动流转状态后再返回给前端
        _auto_transition_exam_status(exam)

        # 综合 exam_papers.status 和 exams.status 判断考试状态
        exam_status = STATUS_MAP.get(exam.status, 'not_started')
        paper_status = paper_status_map.get(exam.id)
        if paper_status in (ExamPaper.Status.SUBMITTED, ExamPaper.Status.ABNORMAL):
            exam_status = 'submitted'

        exam_list.append({
            'exam_id': exam.id,
            'exam_name': exam.name,
            'exam_status': exam_status,
            'paper_id': paper_id_map.get(exam.id),  # 考生试卷ID，未进入考试时为null
        })
    return exam_list


def get_exam_info(exam_id, user_id=None):
    """
    获取考试详情
    接口：GET /api/exam/info/{exam_id}/
    权限：辅导员（role=1）
    返回考试基础信息：名称、时长、起止时间、状态、剩余时间（秒）
    所有时间均转换为上海时区（Asia/Shanghai）显示
    user_id 不为空时，结合 exam_papers 表判断考生个人的考试状态
    返回 None 表示考试不存在
    """
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return None

    # 已删除/已关闭的考试不返回
    if exam.status == ExamStatus.CLOSED:
        return None

    # 自动流转状态
    _auto_transition_exam_status(exam)

    # 将 UTC 时间转换为本地时区用于显示
    exam_start_utc = exam.start_time
    exam_start_local = timezone.localtime(exam_start_utc)
    exam_duration = exam.duration_minutes
    exam_end_utc = exam_start_utc + timedelta(minutes=exam_duration)
    exam_end_local = timezone.localtime(exam_end_utc)

    # 计算剩余时间（秒），基于 UTC 时间比较
    now = timezone.now()
    if now < exam_start_utc:
        remaining_time = exam_duration * 60
    elif now < exam_end_utc:
        remaining_time = int((exam_end_utc - now).total_seconds())
    else:
        remaining_time = 0

    # 综合 exam_papers.status 和 exams.status 判断考试状态
    # 考生已交卷（含异常交卷）→ submitted；否则使用考试级别状态
    exam_status = STATUS_MAP.get(exam.status, 'not_started')
    if user_id is not None:
        try:
            paper = ExamPaper.objects.get(exam_id=exam_id, user_id=user_id)
            if paper.status in (ExamPaper.Status.SUBMITTED, ExamPaper.Status.ABNORMAL):
                exam_status = 'submitted'
        except ExamPaper.DoesNotExist:
            pass  # 没有 ExamPaper 记录时使用考试级别状态

    # 查询用户在该考试中的 paper_id
    paper_id = None
    if user_id is not None:
        try:
            paper = ExamPaper.objects.get(exam_id=exam_id, user_id=user_id)
            paper_id = paper.id
        except ExamPaper.DoesNotExist:
            pass

    return {
        'exam_name': exam.name,
        'duration': exam_duration,
        'start_time': exam_start_local.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': exam_end_local.strftime('%Y-%m-%d %H:%M:%S'),
        'exam_status': exam_status,
        'remaining_time': remaining_time,
        'paper_id': paper_id,
    }


def _render_question_stem(stem, student_name):
    """
    渲染题干中的占位符
    将 {name} 替换为实际学生姓名，{该生} 作为兜底
    """
    try:
        return stem.replace('{name}', student_name or '该生')
    except Exception:
        return stem


def _parse_options(options):
    """
    解析选项为字典
    options 在 JSONField 反序列化后已是 dict，直接返回即可
    """
    if not options:
        return None
    if isinstance(options, dict):
        return options
    return None


def _normalize_multi_answer(answer):
    """
    归一化多选题答案：排序、去空格、转大写
    将 "B,A" → "A,B"，确保比对不受顺序影响
    """
    if not answer:
        return ''
    parts = [p.strip().upper() for p in answer.replace('，', ',').split(',') if p.strip()]
    parts.sort()
    return ','.join(parts)


def _validate_answer_format(user_answer, question_type):
    """
    校验答案格式是否符合题型要求
    - 单选题：只能为 A/B/C/D 之一
    - 判断题：只能为 A/B 之一
    - 多选题：只能为 ABCD 的组合，逗号分隔（如 "A,C"）
    - 简答题：不校验
    返回: (is_valid, error_message)
    """
    valid_labels = {'A', 'B', 'C', 'D'}
    user_answer = (user_answer or '').strip()
    if not user_answer:
        return True, ''

    if question_type == 'single':
        if user_answer.upper() in valid_labels:
            return True, ''
        return False, '单选题答案只能为A、B、C、D中的一个'

    if question_type == 'judge':
        if user_answer.upper() in {'A', 'B'}:
            return True, ''
        return False, '判断题答案只能为A或B'

    if question_type == 'multi':
        parts = [p.strip().upper() for p in user_answer.replace('，', ',').split(',') if p.strip()]
        if not parts:
            return True, ''  # 空答案（全逗号等）允许保存
        for p in parts:
            if p not in valid_labels:
                return False, f'多选题选项"{p}"无效，只能为A、B、C、D，多个选项用逗号分隔'
        return True, ''

    # essay 不校验格式
    return True, ''


# 字段 → 选项文本模板映射（用于 multi 模式三动态渲染选项文本）
FIELD_OPTION_TEMPLATES = {
    # 文本/枚举字段：{value} 会被替换为具体值
    'ethnicity': '{name}是{value}族',
    'class_name': '{name}的班级是{value}',
    'college': '{name}属于{value}',
    'native_place': '{name}来自{value}',
    'dorm_address': '{name}住在{value}',
    'gender': '{name}的性别是{value}',
    'grade': '{name}是{value}年级',
    'religion': '{name}信仰{value}',
    'off_campus_address': '{name}的校外住址是{value}',
    'family_address': '{name}的家庭位于{value}',
    'household_address': '{name}的户籍在{value}',
    # 布尔字段：无 {value} 占位，固定句式
    'is_financial_difficulty': '{name}是经济困难学生',
    'is_academic_difficulty': '{name}是学业困难学生',
}

# 布尔字段在 student 表中的"真"值表示（用于 _parse_bool 兼容旧数据）
BOOLEAN_TRUE_VALUES = ('是', '1', 'true', 'yes')
BOOLEAN_FALSE_VALUES = ('否', '0', 'false', 'no')

# 布尔字段为假时的多选题兜底文案
BOOLEAN_FALSE_OPTION_TEMPLATES = {
    'is_financial_difficulty': '{name}不是经济困难学生',
    'is_academic_difficulty': '{name}不是学业困难学生',
}


def _parse_bool(value):
    """判断布尔值为真（兼容 BooleanField 和旧 CharField 数据）"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in BOOLEAN_TRUE_VALUES


def _parse_expected_bool(value):
    """将多选配置中的期望值转换为布尔值。"""
    normalized = str(value or '').strip().lower()
    if normalized in BOOLEAN_TRUE_VALUES:
        return True
    if normalized in BOOLEAN_FALSE_VALUES:
        return False
    return value == '是'


def _get_student_field_value(student, field_name):
    """获取学生字段值，并对部分字段做与选项生成一致的归一化。"""
    value = str(getattr(student, field_name, '') or '').strip()
    if field_name == 'native_place':
        value = _normalize_native_place(value)
    return value


def _render_multi_option_text(student, field_name, expected_value):
    """根据字段和值生成多选题选项文本。"""
    student_name = student.name or '该生'

    if field_name in ('is_financial_difficulty', 'is_academic_difficulty'):
        expected_bool = _parse_expected_bool(expected_value)
        template_str = (
            FIELD_OPTION_TEMPLATES.get(field_name)
            if expected_bool
            else BOOLEAN_FALSE_OPTION_TEMPLATES.get(field_name)
        )
        if template_str:
            return template_str.replace('{name}', student_name)

    template_str = FIELD_OPTION_TEMPLATES.get(field_name)
    if template_str:
        option_text = template_str.replace('{name}', student_name)
        if '{value}' in template_str:
            option_text = option_text.replace('{value}', str(expected_value))
        return option_text
    return f'{student_name}的{field_name}是{expected_value}'


def _is_multi_option_match(student, field_name, expected_value):
    """判断一个多选选项是否符合学生真实信息。"""
    if field_name in ('is_financial_difficulty', 'is_academic_difficulty'):
        return _parse_bool(getattr(student, field_name, None)) == _parse_expected_bool(expected_value)

    actual_value = _get_student_field_value(student, field_name)
    return actual_value.lower() == str(expected_value or '').strip().lower()


def _parse_multi_entry(entry, student):
    """解析多选配置项，返回字段名和该选项声明的期望值。"""
    if ':' in entry:
        field_name, expected_value = entry.split(':', 1)
        return field_name.strip(), expected_value.strip()

    field_name = entry.strip()
    if field_name in ('is_financial_difficulty', 'is_academic_difficulty'):
        return field_name, '是'

    expected_value = _get_student_field_value(student, field_name)
    return field_name, expected_value or '未知'


def _build_true_multi_option_text(student, entries):
    """
    为全不匹配的普通多选题构造一个必然正确的选项。
    优先使用模板中已有字段，避免生成与题意完全无关的内容。
    """
    for entry in entries:
        field_name = entry.split(':', 1)[0].strip() if ':' in entry else entry.strip()
        if not field_name:
            continue

        if field_name in ('is_financial_difficulty', 'is_academic_difficulty'):
            expected_value = '是' if _parse_bool(getattr(student, field_name, None)) else '否'
            return _render_multi_option_text(student, field_name, expected_value)

        actual_value = _get_student_field_value(student, field_name)
        if actual_value:
            return _render_multi_option_text(student, field_name, actual_value)

    return ''


def _build_none_of_above_options(values):
    """构造包含“以上都不是”的四个选项，并返回正确答案字母。"""
    option_values = [str(v or '').strip() for v in values if str(v or '').strip()]
    option_values = option_values[:3]
    while len(option_values) < 3:
        option_values.append(f'学生{len(option_values) + 1}')
    option_values.append('以上都不是')

    random.shuffle(option_values)
    labels = ['A', 'B', 'C', 'D']
    options = {}
    correct_label = ''
    for i, value in enumerate(option_values):
        label = labels[i]
        options[label] = value
        if value == '以上都不是':
            correct_label = label
    return options, correct_label


def _normalize_dorm_address_value(value):
    normalized = str(value or '').strip()
    compact = re.sub(r'\s+', '', normalized).lower()
    if compact in NO_DORM_ADDRESS_VALUES:
        return ''
    return normalized


def _normalize_special_match_value(student, field_name):
    value = getattr(student, field_name, '')
    if field_name == 'dorm_address':
        return _normalize_dorm_address_value(value)
    return str(value or '').strip()


def _student_display_name(student, fallback):
    return str(getattr(student, 'name', '') or '').strip() or fallback


def _format_student_group(students, fallback_prefix='学生'):
    names = [
        _student_display_name(student, f'{fallback_prefix}{index + 1}')
        for index, student in enumerate(students)
    ]
    # 只有当 fallback_prefix 不为空时才添加占位符
    if fallback_prefix:
        while len(names) < 2:
            names.append(f'{fallback_prefix}{len(names) + 1}')
    return '、'.join(names[:3])


def _pop_student_group(pool):
    group_size = random.randint(2, 3)
    group = []
    while pool and len(group) < group_size:
        group.append(pool.pop())
    return group


def _build_roommate_none_options(student, candidates):
    """无有效寝室时，A/B/C 只放随机学生组，D 固定为正确答案。"""
    pool = []
    seen_names = set()
    for candidate in candidates:
        if candidate.id == student.id:
            continue
        name = _student_display_name(candidate, '')
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        pool.append(candidate)

    random.shuffle(pool)
    options = {}
    for label in ['A', 'B', 'C']:
        group = _pop_student_group(pool)
        options[label] = _format_student_group(group, fallback_prefix='学生')

    options['D'] = '以上都不是'
    return options, 'D'


def _resolve_generated_question_type(template):
    if (template.param_field or '').strip() == 'roommates':
        return 'single'
    return template.question_type


def _resolve_photo_url(photo_url):
    """
    将数据库中存储的 photo_url（可能无扩展名）转换为 Web 可访问的图片 URL
    例如: "2021001" → "/media/students_photo/2021001.jpg"
           "2021001.jpg" → "/media/students_photo/2021001.jpg"
    """
    if not photo_url:
        return ''

    from django.conf import settings
    import os

    # 已有扩展名，直接构造 URL
    name, ext = os.path.splitext(photo_url)
    if ext:
        return f"{settings.MEDIA_URL}students_photo/{photo_url}"

    # 无扩展名，遍历常见格式查找实际文件
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
        path = os.path.join(settings.STUDENT_PHOTO_DIR, f'{photo_url}{ext}')
        if os.path.isfile(path):
            return f"{settings.MEDIA_URL}students_photo/{photo_url}{ext}"

    # 找不到实际文件，默认用 .jpg（前端可显示默认占位图）
    return f"{settings.MEDIA_URL}students_photo/{photo_url}.jpg"


def _generate_photo_options(student, all_students):
    """
    模式五：图片选择题 — param_field='photo_url'
    选项存储图片路径（URL），正确选项为当前学生的照片，干扰项为其他学生的照片
    返回: (options_dict, correct_label) 与单选题模式一致
    """
    # 解析目标学生的照片 URL
    correct_url = _resolve_photo_url(student.photo_url)
    if not correct_url:
        return None, ''

    # 从其他同性别学生收集照片 URL 作为干扰项（去重）
    student_gender = (student.gender or '').strip()
    other_urls = []
    seen = {correct_url}
    for s in all_students:
        if s.id == student.id:
            continue
        if student_gender:
            s_gender = (s.gender or '').strip()
            if s_gender != student_gender:
                continue
        url = _resolve_photo_url(s.photo_url)
        if url and url not in seen:
            other_urls.append(url)
            seen.add(url)

    # 随机取 3 个干扰项
    random.shuffle(other_urls)
    distractors = other_urls[:3]

    # 不足 3 个时用空字符串填充（前端展示默认占位图）
    while len(distractors) < 3:
        distractors.append('')

    # 正确答案 + 干扰项随机排列，映射 A/B/C/D
    all_options = [correct_url] + distractors
    random.shuffle(all_options)

    labels = ['A', 'B', 'C', 'D']
    options = {}
    correct_label = None
    for i, val in enumerate(all_options):
        label = labels[i]
        options[label] = val
        if val == correct_url:
            correct_label = label

    return options, correct_label


def _generate_dynamic_options(template, student, all_students):
    """
    根据模板 param_field 和学生真实数据动态生成选项和正确答案
    返回: (options_dict, correct_answer)
      - options_dict: {"A":"...","B":"...","C":"...","D":"..."} 或 None（essay）
      - correct_answer: "A" / "A,C" / ""（essay）
    """
    param_field = (template.param_field or '').strip()
    if not param_field:
        return None, ''

    # 模式五：图片选择题 — 选项存储图片 URL
    if param_field == 'photo_url':
        return _generate_photo_options(student, all_students)

    # 逗号分隔 → 模式三 multi
    if ',' in param_field:
        entries = [e.strip() for e in param_field.split(',') if e.strip()]
        if len(entries) > 4:
            # param_field 超过 4 个条目时，随机抽取 4 个
            entries = random.sample(entries, 4)
            param_field = ','.join(entries)
        return _generate_multi_options(template, student, all_students, param_field)

    if param_field == 'roommates':
        return _generate_roommate_single_options(template, student, all_students)

    # 特殊关键字 → 模式四
    if param_field == 'classmates':
        return _generate_special_multi_options(template, student, all_students, param_field)

    # 布尔字段 → 模式二 judge
    if param_field in ('is_financial_difficulty', 'is_academic_difficulty'):
        return _generate_judge_options(student, param_field)

    # 文本字段 → 模式一 single
    return _generate_single_options(template, student, all_students, param_field)


def _generate_single_options(template, student, all_students, field_name):
    """模式一：单选题 — 从学生真实数据取正确答案 + 其他学生数据取干扰项"""
    correct_value = str(getattr(student, field_name, '') or '').strip()
    if field_name == 'native_place':
        correct_value = _normalize_native_place(correct_value)
    if not correct_value:
        correct_value = '未知'

    other_values = []
    seen = {correct_value}
    for s in all_students:
        if s.id == student.id:
            continue
        val = str(getattr(s, field_name, '') or '').strip()
        if field_name == 'native_place':
            val = _normalize_native_place(val)
        if val and val not in seen:
            other_values.append(val)
            seen.add(val)

    # 随机取 3 个干扰项
    random.shuffle(other_values)
    distractors = other_values[:3]

    # 不足 3 个时用占位符填充
    while len(distractors) < 3:
        distractors.append(f'其他选项{len(distractors) + 1}')

    # 正确答案 + 干扰项随机排列，映射 A/B/C/D
    all_options = [correct_value] + distractors
    random.shuffle(all_options)

    labels = ['A', 'B', 'C', 'D']
    options = {}
    correct_label = None
    for i, val in enumerate(all_options):
        label = labels[i]
        options[label] = val
        if val == correct_value:
            correct_label = label

    return options, correct_label


def _generate_judge_options(student, field_name):
    """模式二：判断题 — 选项固定 正确/错误，correct_answer 取决于学生实际值"""
    options = {'A': '正确', 'B': '错误'}
    is_true = _parse_bool(getattr(student, field_name, None))
    correct_answer = 'A' if is_true else 'B'
    return options, correct_answer


def _generate_multi_options(template, student, all_students, param_field):
    """模式三：多选题 — 逗号分隔字段=值对，每个条目一个选项"""
    # 解析 param_field：如 "ethnicity:汉族,is_academic_difficulty,college:计算机,is_financial_difficulty"
    entries = [e.strip() for e in param_field.split(',') if e.strip()]
    if len(entries) != 4:
        # 字段数量不是4时回退到 single 模式
        return _generate_single_options(template, student, all_students, param_field)

    # 构建选项：每个条目生成一条陈述
    option_texts = []       # 顺序与 entries 一致
    is_correct_list = []    # 每个选项对该生是否正确

    for entry in entries:
        field_name, expected_value = _parse_multi_entry(entry, student)
        option_texts.append(_render_multi_option_text(student, field_name, expected_value))
        is_correct_list.append(_is_multi_option_match(student, field_name, expected_value))

    # 若模板配置的四个断言对该学生全部为假，则强制替换一个选项为真实断言。
    # 多选题没有正确答案会导致展示和自动判分都失效，因此这里兜底保证至少一个正确项。
    if not any(is_correct_list):
        fallback_text = _build_true_multi_option_text(student, entries)
        if fallback_text:
            option_texts[-1] = fallback_text
            is_correct_list[-1] = True
        else:
            option_texts[-1] = '以上都不正确'
            is_correct_list[-1] = True

    # 4 个选项随机 shuffle，记录正确选项的字母
    indices = list(range(4))
    random.shuffle(indices)

    labels = ['A', 'B', 'C', 'D']
    options = {}
    correct_labels = []
    for new_i, old_i in enumerate(indices):
        label = labels[new_i]
        options[label] = option_texts[old_i]
        if is_correct_list[old_i]:
            correct_labels.append(label)

    correct_labels.sort()
    correct_answer = ','.join(correct_labels) if correct_labels else ''

    return options, correct_answer


def _generate_roommate_single_options(template, student, all_students):
    """室友单选题：A/B/C 为学生分组，D 固定为“以上都不是”。"""
    match_field = 'dorm_address'
    student_value = _normalize_special_match_value(student, match_field)

    student_gender = (student.gender or '').strip()
    if student_gender:
        all_students = [
            s for s in all_students
            if (s.gender or '').strip() == student_gender
        ]

    candidate_students = [
        s for s in all_students
        if s.id != student.id
    ]

    if not student_value:
        return _build_roommate_none_options(student, candidate_students)

    known_students = [
        s for s in candidate_students
        if _normalize_special_match_value(s, match_field)
    ]
    matches = [
        s for s in known_students
        if _normalize_special_match_value(s, match_field) == student_value
    ]
    non_matches = [
        s for s in known_students
        if _normalize_special_match_value(s, match_field) != student_value
    ]

    if len(matches) < 2:
        return _build_roommate_none_options(student, non_matches or candidate_students)

    labels = ['A', 'B', 'C']
    random.shuffle(matches)
    correct_count = min(random.randint(2, 3), len(matches))
    correct_group = matches[:correct_count]
    correct_label = random.choice(labels)

    random.shuffle(non_matches)
    options = {}
    available_students = list(non_matches)

    for label in labels:
        if label == correct_label:
            group = correct_group
        else:
            group = _pop_student_group(available_students)

        options[label] = _format_student_group(group, fallback_prefix='学生')

    options['D'] = '以上都不是'
    return options, correct_label


def _generate_special_multi_options(template, student, all_students, keyword):
    """模式四：特殊匹配关键字 — 查同宿舍/同班级学生生成选项"""
    if keyword == 'roommates':
        return _generate_roommate_single_options(template, student, all_students)

    if keyword == 'classmates':
        match_field = 'class_name'
    else:
        return None, ''

    student_value = _normalize_special_match_value(student, match_field)

    # 室友题：宿舍男女分开，全体学生先按同性别过滤，保证所有选项性别一致
    if keyword == 'roommates':
        student_gender = (student.gender or '').strip()
        if student_gender:
            all_students = [s for s in all_students
                            if (s.gender or '').strip() == student_gender]

    # 匹配学生列表（同宿舍/同班级且非本人）→ 正确选项来源
    known_students = [
        s for s in all_students
        if s.id != student.id and _normalize_special_match_value(s, match_field)
    ]

    if not student_value:
        random.shuffle(known_students)
        return _build_none_of_above_options([s.name for s in known_students])

    matches = [
        s for s in known_students
        if _normalize_special_match_value(s, match_field) == student_value
    ]
    # 不匹配学生列表 → 干扰项来源
    non_matches = [
        s for s in known_students
        if _normalize_special_match_value(s, match_field) != student_value
    ]

    if not matches:
        random.shuffle(non_matches)
        return _build_none_of_above_options([s.name for s in non_matches])

    # 随机取 2~3 个匹配学生为正确选项
    random.shuffle(matches)
    correct_count = min(random.randint(2, 3), len(matches))
    correct_students = matches[:correct_count]

    # 从不匹配学生中随机取干扰项
    distractor_count = 4 - correct_count
    random.shuffle(non_matches)
    distractor_students = non_matches[:distractor_count]

    # 不足时用占位符填充
    while len(distractor_students) < distractor_count:
        distractor_students.append(None)

    # 合并 + shuffle + 映射 A/B/C/D
    all_student_names = [s.name if s else f'学生{i+1}' for i, s in enumerate(correct_students + distractor_students)]
    is_correct_flags = [True] * len(correct_students) + [False] * len(distractor_students)

    indices = list(range(4))
    random.shuffle(indices)

    labels = ['A', 'B', 'C', 'D']
    options = {}
    correct_labels = []
    for new_i, old_i in enumerate(indices):
        label = labels[new_i]
        options[label] = all_student_names[old_i]
        if is_correct_flags[old_i]:
            correct_labels.append(label)

    correct_labels.sort()
    correct_answer = ','.join(correct_labels) if correct_labels else ''

    return options, correct_answer


def _build_question_list(questions_qs, generate_mode='by_type', config=None):
    """
    从 ExamQuestion 查询集构建题目列表（含已保存答案回填）
    by_type 模式：返回扁平列表
    by_student 模式：按学生分组返回（question_groups）
    """
    question_ids = [q.id for q in questions_qs]
    answers_map = {}
    if question_ids:
        saved = ExamAnswer.objects.filter(question_id__in=question_ids).only('question_id', 'content')
        for ans in saved:
            answers_map[str(ans.question_id)] = ans.content

    if generate_mode == 'by_student':
        return _build_student_groups(questions_qs, answers_map)

    questions = []
    for q in questions_qs:
        item = {
            'question_id': q.id,
            'title': q.question_text,
            'question_type': q.question_type,
            'score': q.score,
            'user_answer': answers_map.get(str(q.id)),
        }
        if q.options:
            item['options'] = _parse_options(q.options)
        questions.append(item)
    return questions


def _build_student_groups(questions_qs, answers_map):
    """
    按学生分组构建题目列表（by_student 模式）
    返回: [{student_xid, student_name, questions: [...]}, ...]
    """
    groups = {}
    for q in questions_qs:
        sid = q.student_id
        if sid not in groups:
            groups[sid] = {
                'student_xid': sid,
                'student_name': q.student.name if q.student_id else '未知',
                'questions': [],
            }
        item = {
            'question_id': q.id,
            'title': q.question_text,
            'question_type': q.question_type,
            'score': q.score,
            'user_answer': answers_map.get(str(q.id)),
            'sort_order': q.student_sort_order or 0,
        }
        if q.options:
            item['options'] = _parse_options(q.options)
        groups[sid]['questions'].append(item)

    result = sorted(groups.values(), key=lambda g: g['student_xid'])
    return result


def enter_exam(exam_id, user_id, user_display_name):
    """
    进入考试（支持断线恢复）
    接口：POST /api/exam/enter/{exam_id}/
    权限：辅导员（role=1）

    核心流程：
        1. 校验考试存在且状态为「进行中」，且在时间窗口内
        2. 检查是否已有进行中的考试记录 → 有则断线恢复
        3. 检查是否已交卷（status=2）或异常交卷（status=3）→ 拒绝
        4. 首次进入：直接从预生成的 exam_questions 表读取试卷题目
        5. 断线恢复：回填已保存的答案

    注意：考卷在考试创建 / 编辑时已预生成至 exam_questions 表，此处不再查询
          question_templates 表，也不动态生成 ExamQuestion 记录。

    返回值：
        (success, data_or_error)
        by_type 模式: {paper_id, is_resumed, questions: [...], exam_status}
        by_student 模式: {paper_id, is_resumed, generate_mode, student_count, question_groups: [...], exam_status}
        error: (code, msg) 如 (4032, "不在考试时间内或考试已关闭")
    """
    # 1. 校验考试存在
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    # 读取出题模式和配置
    config = exam.question_config if isinstance(exam.question_config, dict) else {}
    generate_mode = config.get('generate_mode', 'by_type')
    student_count = config.get('student_count', 0)

    # 自动流转状态
    _auto_transition_exam_status(exam)

    # 2. 校验考试时间与状态：仅 status=进行中且在时间窗口内
    now = timezone.now()
    exam_end = exam.start_time + timedelta(minutes=exam.duration_minutes)

    if exam.status != ExamStatus.IN_PROGRESS:
        return False, (4032, "不在考试时间内或考试已关闭")
    if now < exam.start_time or now > exam_end:
        return False, (4032, "不在考试时间内或考试已关闭")

    # 3. 检查是否已有考试记录（exam_papers 记录对应 API 中的 paper_id）
    try:
        paper = ExamPaper.objects.get(exam_id=exam_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        paper = None

    # 已交卷(status=2)不可再次进入
    if paper and paper.status == ExamPaper.Status.SUBMITTED:
        return False, (4033, "考试已交卷，不可重复进入")

    # 异常交卷(status=3)不可再次进入（已触发防作弊被强制交卷）
    if paper and paper.status == ExamPaper.Status.ABNORMAL:
        return False, (4033, "考试已因异常行为被强制交卷，不可重复进入")

    # 构建排序（by_student 模式按学生+组内排序，by_type 按全局排序）
    if generate_mode == 'by_student':
        order_fields = ['student_id', 'student_sort_order']
    else:
        order_fields = ['sort_order']

    # 4. 断线恢复：已有进行中的试卷，直接从 exam_questions 读取并回填答案
    if paper and paper.status == ExamPaper.Status.IN_PROGRESS:
        questions_qs = ExamQuestion.objects.filter(
            exam_id=exam_id, user_id=user_id
        ).select_related('student').order_by(*order_fields)

        if not questions_qs.exists():
            return False, (500, "试卷数据异常，请联系管理员")

        questions = _build_question_list(questions_qs, generate_mode)
        result = {
            'paper_id': paper.id,
            'is_resumed': True,
            'exam_status': STATUS_MAP.get(exam.status, 'normal'),
        }
        if generate_mode == 'by_student':
            result['generate_mode'] = 'by_student'
            result['student_count'] = student_count
            result['question_groups'] = questions
        else:
            result['questions'] = questions
        return True, result

    # 5. 首次进入：创建 / 更新 ExamPaper 记录，从预生成的 exam_questions 读取试卷
    with transaction.atomic():
        if paper and paper.status == ExamPaper.Status.NOT_STARTED:
            paper.status = ExamPaper.Status.IN_PROGRESS
            paper.started_at = now
            paper.save(update_fields=['status', 'started_at'])
        elif not paper:
            paper = ExamPaper.objects.create(
                exam_id=exam_id,
                user_id=user_id,
                started_at=now,
                status=ExamPaper.Status.IN_PROGRESS,
            )

        questions_qs = ExamQuestion.objects.filter(
            exam_id=exam_id, user_id=user_id
        ).select_related('student').order_by(*order_fields)

        if not questions_qs.exists():
            raise Exception("未找到您的试卷，请联系管理员重新生成")

        questions = _build_question_list(questions_qs, generate_mode)

    result = {
        'paper_id': paper.id,
        'is_resumed': False,
        'exam_status': STATUS_MAP.get(exam.status, 'normal'),
    }
    if generate_mode == 'by_student':
        result['generate_mode'] = 'by_student'
        result['student_count'] = student_count
        result['question_groups'] = questions
    else:
        result['questions'] = questions
    return True, result


def get_saved_answers(paper_id, user_id):
    """
    获取已保存的答案（断线快速恢复专用）
    接口：GET /api/exam/saved-answers/{paper_id}/
    权限：辅导员（role=1）

    注意：URL 中的 paper_id 对应 ExamPaper.id（考生试卷ID），
          非 ExamQuestion.id（题目ID）。

    返回值：
        (success, data_or_error)
        data: {answers: {question_id: user_answer}}
    """
    # 校验 paper_id 归属于当前用户
    try:
        paper = ExamPaper.objects.get(id=paper_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 查询该考试下所有已保存的答案
    questions = ExamQuestion.objects.filter(
        exam_id=paper.exam_id,
        user_id=user_id,
    )
    question_ids = [q.id for q in questions]

    answers = {}
    if question_ids:
        saved = ExamAnswer.objects.filter(question_id__in=question_ids)
        for ans in saved:
            answers[str(ans.question_id)] = ans.content or ''

    return True, {'answers': answers}


def _check_save_rate_limit(user_id):
    """
    检查保存答案的频率限制
    使用 Redis 做简易限流：首次保存设置 1 秒过期 key，后续保存在此窗口内被拦截
    返回 True 表示允许保存，False 表示频率过高
    """
    try:
        redis_client = RedisClient()
        rate_key = f"exam_save_rate:{user_id}"
        count = redis_client.get(rate_key)
        if count is not None:
            return False  # 1 秒内已有保存操作
        redis_client.setex(rate_key, "1", 1)  # 1 秒过期
        return True
    except Exception:
        # Redis 不可用时默认放行，避免阻塞正常考试
        return True


def _process_single_exam_answer(paper, question_id, user_answer, user_id):
    """
    处理考试单题保存的核心逻辑（提取为内部函数，供单题和批量模式复用）
    参数:
        paper: 已校验的试卷对象
        question_id: 题目ID（ExamQuestion.id）
        user_answer: 用户提交的答案
        user_id: 考生ID
    返回值: (success, data_or_error)
    """
    # 校验 question_id 属于该考试且属于该考生
    try:
        question = ExamQuestion.objects.get(
            id=question_id,
            exam_id=paper.exam_id,
            user_id=user_id,
        )
    except ExamQuestion.DoesNotExist:
        return False, (404, f"题目{question_id}不存在")

    # 校验答案格式是否符合题型要求（空答案跳过校验，允许保存未作答状态）
    if user_answer.strip():
        valid, err_msg = _validate_answer_format(user_answer, question.question_type)
        if not valid:
            return False, (400, err_msg)

    # 覆盖保存答案（幂等操作）
    # 使用 filter().first() 而非 update_or_create，避免 question_id 存在重复记录时
    # 抛出 MultipleObjectsReturned 导致更新失败
    existing = ExamAnswer.objects.filter(question_id=question_id).first()
    if existing:
        existing.content = user_answer
        existing.save(update_fields=['content'])
    else:
        ExamAnswer.objects.create(question_id=question_id, content=user_answer)
    return True, {}


def save_answer(paper_id, question_id, user_answer, save_time, user_id, reconnect=False, answers=None):
    """
    实时保存答案（支持单题/批量两种模式）
    接口：POST /api/exam/save/
    权限：辅导员（role=1）
    频率限制：每秒最多 1 次

    注意：paper_id 对应 ExamPaper.id，question_id 对应 ExamQuestion.id。
          reconnect=true 时标记断线重连保存，不影响正常流程。

    单题模式: 传 question_id + user_answer（兼容旧版）
    批量模式: 传 answers=[{question_id, user_answer}, ...]

    返回值：
        (success, data_or_error)
        data: {save_status: "success"} 或 {results: [...]}
    """
    # 1. 频率限制检查
    if not _check_save_rate_limit(user_id):
        return False, (400, "保存过于频繁，请稍后再试")

    # 2. 校验 paper_id 归属
    try:
        paper = ExamPaper.objects.get(id=paper_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 3. 检查考试状态：进行中或异常交卷（允许断线重连时保存）
    if paper.status not in (ExamPaper.Status.IN_PROGRESS, ExamPaper.Status.ABNORMAL):
        return False, (4033, "考试已交卷，不可保存答案")

    # 4. 批量模式
    if answers:
        for item in answers:
            success, result = _process_single_exam_answer(
                paper, item['question_id'], item.get('user_answer', ''), user_id,
            )
            if not success:
                return False, result  # 批量中任一题目校验失败，整体返回错误
        return True, {'save_status': 'success'}

    # 5. 单题模式（兼容旧版）
    success, result = _process_single_exam_answer(
        paper, question_id, user_answer, user_id,
    )
    if not success:
        return False, result
    return True, {'save_status': 'success'}


def _judge_objective_answer(user_answer, correct_answer, question_type):
    """
    判断客观题答案是否正确
    单选题/判断题：直接比较（忽略大小写和空格）
    多选题：归一化后比较（排序、去空格、转大写后比对）
    """
    if not user_answer:
        return False

    if question_type in ('multi',):
        # 多选题：归一化后比较，避免 "B,A" vs "A,B" 误判
        normalized_user = _normalize_multi_answer(user_answer)
        normalized_correct = _normalize_multi_answer(correct_answer)
        return normalized_user == normalized_correct
    else:
        # 单选题、判断题：直接去空格转大写后比较
        return user_answer.strip().upper() == (correct_answer or '').strip().upper()


def submit_exam(paper_id, user_id):
    """
    交卷
    接口：POST /api/exam/submit/{paper_id}/
    权限：辅导员（role=1）
    幂等控制：1 用户 1 考试仅可提交 1 次
    自动批改客观题并计算得分

    注意：URL 中 paper_id 对应 ExamPaper.id

    返回值：
        (success, data_or_error)
    """
    # 1. 校验试卷归属与状态
    try:
        paper = ExamPaper.objects.get(id=paper_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 已交卷不可重复提交
    if paper.status == ExamPaper.Status.SUBMITTED:
        return False, (4033, "考试已交卷，不可重复提交")

    # 仅进行中或异常交卷可交卷
    if paper.status not in (ExamPaper.Status.IN_PROGRESS, ExamPaper.Status.ABNORMAL):
        return False, (4033, "当前状态不可交卷")

    # 2. 获取试卷所有题目
    questions_qs = ExamQuestion.objects.filter(
        exam_id=paper.exam_id,
        user_id=user_id,
    ).order_by('sort_order')

    if not questions_qs.exists():
        return False, (500, "试卷为空")

    # 3. 批量预加载：获取所有已保存的答案和已存在的 ExamAnswer 记录
    question_ids = [q.id for q in questions_qs]
    saved_answers = {}       # question_id → user_answer_content
    existing_answers = {}    # question_id → ExamAnswer 实例
    if question_ids:
        for ans in ExamAnswer.objects.filter(question_id__in=question_ids):
            saved_answers[ans.question_id] = ans.content or ''
            existing_answers[ans.question_id] = ans

    # 4. 自动批改客观题并写入判断结果
    obj_total_score = 0

    for q in questions_qs:
        user_ans = saved_answers.get(q.id, '') or ''

        if q.question_type in SUBJECTIVE_TYPES:
            # 主观题（简答题）不自动判分，等待管理员批改
            existing = existing_answers.get(q.id)
            if existing:
                existing.content = user_ans
                existing.is_correct = None
                existing.score = None
                existing.graded_by = None
                existing.graded_at = None
                existing.save(update_fields=['content', 'is_correct', 'score', 'graded_by', 'graded_at'])
            else:
                ExamAnswer.objects.create(
                    question_id=q.id, content=user_ans,
                    is_correct=None, score=None,
                )
        else:
            # 客观题自动判分（单选/多选/判断）
            is_correct = _judge_objective_answer(user_ans, q.correct_answer, q.question_type)
            score_got = q.score if is_correct else 0

            existing = existing_answers.get(q.id)
            if existing:
                existing.content = user_ans
                existing.is_correct = is_correct
                existing.score = score_got
                existing.save(update_fields=['content', 'is_correct', 'score'])
            else:
                ExamAnswer.objects.create(
                    question_id=q.id, content=user_ans,
                    is_correct=is_correct, score=score_got,
                )
            obj_total_score += score_got

    # 5. 更新 ExamPaper 状态
    paper.status = ExamPaper.Status.SUBMITTED
    paper.submitted_at = timezone.now()
    paper.objective_score = obj_total_score
    paper.total_score = obj_total_score  # 主观题未批改前先用客观题分数
    paper.save(update_fields=['status', 'submitted_at', 'objective_score', 'total_score'])

    # 返回客观题得分数据，供前端展示
    return True, {
        'objective_score': obj_total_score,
        'total_score': obj_total_score,
    }


def _check_abnormal_rate_limit(user_id):
    """
    检查异常上报的频率限制
    每秒最多 1 次，使用 Redis 做简易限流
    """
    try:
        redis_client = RedisClient()
        rate_key = f"exam_abnormal_rate:{user_id}"
        count = redis_client.get(rate_key)
        if count is not None:
            return False
        redis_client.setex(rate_key, "1", 1)
        return True
    except Exception:
        return True


def _incr_cheat_counter(exam_id, user_id):
    """
    递增 Redis 中的防作弊累计切屏次数（原子操作 INCR）
    每次切屏上报时计数 +1，返回递增后的计数值
    首次设置 2 小时过期时间
    """
    try:
        redis_client = RedisClient()
        key = f"cheat_counter:{exam_id}:{user_id}"
        new_val = redis_client.incr(key)
        redis_client.expire(key, CHEAT_COUNTER_TTL)
        return new_val
    except Exception:
        return 1  # Redis 不可用时返回安全默认值


def report_abnormal(paper_id, exam_id, user_id, abnormal_type, duration, screen_out_count):
    """
    考试异常日志上报（含强制交卷判断）
    接口：POST /api/exam/report-abnormal/
    权限：辅导员（role=1）
    频率限制：每秒最多 1 次

    防作弊规则：
        - 后端 Redis 独立累计切屏次数（不依赖前端传入的 screen_out_count）
        - 后端累计次数 > MAX_CHEAT_COUNT（3次）或单次切出 > MAX_CHEAT_DURATION（10秒）→ 强制交卷
        - 仅 screen_out 类型递增计数器，其他异常类型（timeout/abnormal_operation）记录日志
        - 前端上报值仅作参考记录，不作为强制交卷判断依据

    注意：paper_id 对应 ExamPaper.id

    返回值：
        (success, data_or_error)
        data: {force_submit: bool, backend_count: int}
    """
    # 1. 校验 paper_id 归属当前用户
    try:
        paper = ExamPaper.objects.get(id=paper_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 2. 校验 exam_id 与 paper 中的 exam_id 一致
    if paper.exam_id != exam_id:
        return False, (400, "考试ID与试卷不匹配")

    # 3. 频率限制
    if not _check_abnormal_rate_limit(user_id):
        return False, (400, "上报过于频繁，请稍后再试")

    # 4. 后端 Redis 独立累计切屏次数（原子递增，不依赖前端数据）
    backend_count = 0
    if abnormal_type == 'screen_out':
        backend_count = _incr_cheat_counter(exam_id, user_id)

    # 5. 记录异常日志（JSON格式存储，便于解析和排查）
    CheatLog.objects.create(
        exam_id=exam_id,
        user_id=user_id,
        action_type=abnormal_type,
        occurred_at=timezone.now(),
        detail=json.dumps({
            'paper_id': paper_id,
            'duration': duration,
            'backend_count': backend_count,
            'frontend_count': screen_out_count,
        }, ensure_ascii=False),
    )

    # 6. 判断是否触发强制交卷（以后端独立计数器为主要依据）
    force_submit = (backend_count > MAX_CHEAT_COUNT or duration > MAX_CHEAT_DURATION)

    if force_submit:
        # 标记 ExamPaper 为异常交卷状态（复用已校验的 paper 对象）
        if paper.status == ExamPaper.Status.IN_PROGRESS:
            paper.status = ExamPaper.Status.ABNORMAL
            paper.cheat_flag = True
            paper.save(update_fields=['status', 'cheat_flag'])

    return True, {'force_submit': force_submit, 'backend_count': backend_count}


def _build_essay_reference_answer(question):
    """
    构建简答题的参考答案（学生信息键值对）
    参数：
        question: ExamQuestion 实例
    返回：学生信息中文字段键值对字典，无学生时返回空字典
    """
    student = question.student
    if not student:
        return {}
    result = {}
    for field, label in STUDENT_FIELD_LABELS.items():
        value = getattr(student, field, None)
        if field in ('is_academic_difficulty', 'is_financial_difficulty'):
            value = '是' if value else '否'
        elif value is None:
            value = ''
        else:
            value = str(value)
            if field == 'native_place':
                value = _normalize_native_place(value)
        result[label] = value
    return result


def get_paper_review(paper_id, viewer):
    """
    超管试卷检查：返回指定考生的完整试卷内容（不含答案回填）
    接口：GET /api/exam/paper-review/{paper_id}/
    权限：仅超级管理员（role=3）
    用途：试卷生成后、考试开考前，超管人工检查所有考生试卷是否正确生成

    参数：
        paper_id: 试卷ID（ExamPaper.id）
        viewer: 当前登录用户对象
    返回：
        (success, data_or_error)
        by_type: {paper_id, teacher_name, teacher_gh, questions: [...]}
        by_student: {paper_id, teacher_name, teacher_gh, generate_mode, question_groups: [...]}
    """
    # 1. 校验权限：仅超管
    if viewer.role != 3:
        return False, (403, "无权限，仅超级管理员可查看")

    # 2. 获取试卷记录
    try:
        paper = ExamPaper.objects.get(id=paper_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 3. 获取考生基本信息
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        exam_user = User.objects.get(id=paper.user_id)
    except User.DoesNotExist:
        return False, (404, "考生不存在")

    # 4. 读取出题模式
    config = paper.exam.question_config if isinstance(paper.exam.question_config, dict) else {}
    generate_mode = config.get('generate_mode', 'by_type')

    # 5. 从 exam_questions 表读取该考生的预生成试卷题目
    if generate_mode == 'by_student':
        order_fields = ['student_id', 'student_sort_order']
    else:
        order_fields = ['sort_order']

    questions_qs = ExamQuestion.objects.filter(
        exam_id=paper.exam_id,
        user_id=paper.user_id,
    ).select_related('student').order_by(*order_fields)

    if not questions_qs.exists():
        return False, (404, "该考生试卷题目不存在，可能尚未生成")

    base_result = {
        'paper_id': paper.id,
        'teacher_name': exam_user.display_name or exam_user.username,
        'teacher_gh': exam_user.username,
    }

    # 6. by_student 模式：按学生分组
    if generate_mode == 'by_student':
        groups = {}
        for q in questions_qs:
            sid = q.student_id
            if sid not in groups:
                groups[sid] = {
                    'student_xid': sid,
                    'student_name': q.student.name if q.student_id else '未知',
                    'questions': [],
                }
            if q.question_type == 'essay':
                correct_answer = _build_essay_reference_answer(q)
            else:
                correct_answer = q.correct_answer or ''
            item = {
                'question_id': q.id,
                'title': q.question_text,
                'question_type': q.question_type,
                'correct_answer': correct_answer,
                'sort_order': q.student_sort_order or 0,
            }
            if q.options:
                item['options'] = _parse_options(q.options)
            groups[sid]['questions'].append(item)

        question_groups = sorted(groups.values(), key=lambda g: g['student_xid'])
        return True, {
            **base_result,
            'generate_mode': 'by_student',
            'question_groups': question_groups,
        }

    # 7. by_type 模式：扁平列表
    questions = []
    for q in questions_qs:
        if q.question_type == 'essay':
            correct_answer = _build_essay_reference_answer(q)
        else:
            correct_answer = q.correct_answer or ''
        item = {
            'question_id': q.id,
            'title': q.question_text,
            'question_type': q.question_type,
            'correct_answer': correct_answer,
        }
        if q.options:
            item['options'] = _parse_options(q.options)
        questions.append(item)

    return True, {**base_result, 'questions': questions}


def _trigger_ai_grading_if_enabled(exam):
    """
    考试结束时检查是否触发 AI 批改
    条件：(1) 全局 AI 配置已启用 (2) 该考试 ai_grade_enabled=1
    参数：
        exam: Exam 实例
    """
    try:
        from apps.correct.services import trigger_ai_grading_for_exam
        trigger_ai_grading_for_exam(exam.id)
    except Exception:
        # AI 批改失败不影响考试状态流转
        pass


def preload_exam_images(paper_id, user_id, viewer_role=None):
    """
    预加载试卷中所有题目的选项图片（考前10分钟缓冲区）
    接口：GET /api/exam/preload-images/{paper_id}/
    权限：辅导员（role=1）和超级管理员（role=3）

    核心流程：
        1. 校验试卷归属：超管可查看任意试卷，辅导员只能看自己的
        2. 校验时间窗口（仅辅导员）：考试开始前10分钟 ~ 考试结束
        3. 遍历该试卷所有题目，从 options JSON 中识别图片路径
        4. 读取图片文件并 base64 编码，返回给前端缓存

    参数：
        paper_id: 试卷ID（ExamPaper.id）
        user_id: 请求用户ID
        viewer_role: 请求用户角色（1=辅导员, 3=超管），超管跳过归属和时间校验
    返回值：
        (success, data_or_error)
        data: {paper_id, images: [{question_id, option_key, filename, mime_type, base64}]}
        无图片时 data 为 None
        error: (code, msg) 如 (4032, "不在预加载时间内")
    """
    is_admin = (viewer_role == 3)

    # 1. 获取试卷记录
    if is_admin:
        # 超管可查看任意试卷
        try:
            paper = ExamPaper.objects.get(id=paper_id)
        except ExamPaper.DoesNotExist:
            return False, (404, "试卷不存在")
        actual_user_id = paper.user_id
    else:
        # 辅导员只能看自己的试卷
        try:
            paper = ExamPaper.objects.get(id=paper_id, user_id=user_id)
        except ExamPaper.DoesNotExist:
            return False, (404, "试卷不存在")
        actual_user_id = user_id

    # 2. 校验时间窗口（仅辅导员需要校验，超管阅卷不受时间限制）
    if not is_admin:
        exam = paper.exam
        now = timezone.now()
        preload_start = exam.start_time - timedelta(minutes=10)
        exam_end = exam.start_time + timedelta(minutes=exam.duration_minutes)

        if now < preload_start or now > exam_end:
            return False, (4032, "不在预加载时间内，请在考试开始前10分钟内入场预加载")

    # 3. 遍历该试卷所有题目，从 options 中收集图片路径
    media_root = str(settings.STUDENT_PHOTO_DIR)
    # 学生照片实际存放在 STUDENT_PHOTO_DIR，不经过 MEDIA_ROOT
    photo_url_prefix = settings.MEDIA_URL + 'students_photo/'
    questions = ExamQuestion.objects.filter(
        exam_id=paper.exam_id,
        user_id=actual_user_id,
    ).order_by('sort_order')

    images = []
    for q in questions:
        options = q.options
        if not isinstance(options, dict):
            continue

        for option_key, option_value in options.items():
            value_str = str(option_value)
            # 判断选项值是否为图片文件路径（以图片扩展名结尾）
            if not IMAGE_EXT_PATTERN.search(value_str):
                continue

            # 选项中存储的是完整 URL 路径（如 /media/students_photo/xxx.jpg）
            # 需要提取相对于 STUDENT_PHOTO_DIR 的文件名部分
            relative_path = value_str.replace(photo_url_prefix, '', 1)
            file_path = os.path.join(media_root, relative_path)
            if not os.path.isfile(file_path):
                continue

            # 获取文件扩展名和对应 MIME 类型
            ext = os.path.splitext(value_str)[1].lower()
            mime_type = MIME_TYPE_MAP.get(ext, 'application/octet-stream')
            # 命名规则：q{题目ID}_{选项key}{扩展名}
            filename = f"q{q.id}_{option_key}{ext}"

            # 读取文件并 base64 编码
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                b64_data = base64.b64encode(file_bytes).decode('ascii')
                images.append({
                    'question_id': q.id,
                    'option_key': option_key,
                    'filename': filename,
                    'mime_type': mime_type,
                    'base64': b64_data,
                })
            except Exception:
                # 单个图片文件读取失败不阻塞整体加载流程
                continue

    # 4. 无图片时返回 None，前端据此跳过缓存步骤
    if not images:
        return True, None

    return True, {
        'paper_id': paper_id,
        'images': images,
    }


def export_exam_students(exam_id):
    """
    导出一次考试中所有辅导员试卷抽取到的所有学生信息
    收集所有 ExamQuestion.student_id → Student 全字段 → Excel
    """
    # 查询该考试所有题目关联的学生ID（去重）
    student_ids = list(
        ExamQuestion.objects
        .filter(exam_id=exam_id, student__isnull=False)
        .values_list('student_id', flat=True)
        .distinct()
    )

    if not student_ids:
        return False, (404, "该考试未关联任何学生")

    # 查询学生完整信息
    students = Student.objects.filter(id__in=student_ids)

    # 准备 Excel 数据
    headers = [
        '学号', '姓名', '性别', '学院', '年级', '班级', '专业',
        '辅导员姓名', '辅导员电话', '辅导员工号',
        '民族', '籍贯', '生源地', '家庭所在地', '户籍所在地',
        '是否学业困难', '宗教信仰', '住宿地址', '校外住宿地址',
        '是否经济困难', '学籍状态', '照片地址',
    ]

    rows = []
    for s in students:
        rows.append([
            s.id, s.name, s.gender or '', s.college or '', s.grade or '',
            s.class_name or '', s.major or '',
            s.advisor_name or '', s.advisor_phone or '', s.advisor_username or '',
            s.ethnicity or '', s.native_place or '', s.origin_place or '',
            s.family_address or '', s.household_address or '',
            '是' if s.is_academic_difficulty else '否',
            s.religion or '', s.dorm_address or '', s.off_campus_address or '',
            '是' if s.is_financial_difficulty else '否',
            s.enrollment_status or '', s.photo_url or '',
        ])

    # 使用已有的 Excel 工具生成响应
    from utils.excel import create_excel_response
    response = create_excel_response(
        filename=f"考试{exam_id}_学生信息",
        sheet_title='学生信息',
        headers=headers,
        rows=rows,
    )
    return True, response
