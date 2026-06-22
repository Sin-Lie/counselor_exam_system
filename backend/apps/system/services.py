# -*- coding: utf-8 -*-
# 系统管理模块 - 业务逻辑层

import json
import math
import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from .models import Student, SystemLog, ImportRecord, QuestionTemplate
from apps.exam.models import Exam, ExamQuestion, ExamPaper, ExamAnswer, CheatLog, ExamStatus, GradePublish
from apps.auth.models import UserRole, UserStatus
from apps.exam.services import SUBJECTIVE_TYPES

User = get_user_model()

# 学生照片支持的扩展名（按常见度排序）
PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']


def resolve_student_photo_path(photo_url):
    """
    根据数据库中存储的 photo_url 解析实际照片文件路径
    支持有扩展名和无扩展名两种情况：
      - '2021001.jpg' → 直接拼接目录
      - '2021001'     → 遍历 PHOTO_EXTENSIONS 查找实际存在的文件
    返回: (full_path, exists) — exists 表示文件是否实际存在
    """
    from django.conf import settings
    import os

    # 如果已有扩展名，直接返回
    name, ext = os.path.splitext(photo_url)
    if ext:
        full = os.path.join(settings.STUDENT_PHOTO_DIR, photo_url)
        return full, os.path.isfile(full)

    # 无扩展名，遍历常见格式查找
    for ext in PHOTO_EXTENSIONS:
        full = os.path.join(settings.STUDENT_PHOTO_DIR, f'{photo_url}{ext}')
        if os.path.isfile(full):
            return full, True

    # 都不存在，返回默认路径（但标记不存在）
    default = os.path.join(settings.STUDENT_PHOTO_DIR, f'{photo_url}.jpg')
    return default, False


def _write_log(operator_id, module, action, target, content=''):
    """写入系统操作日志，失败不影响主业务"""
    try:
        SystemLog.objects.create(
            operator_id=operator_id,
            module=module,
            action=action,
            target=target,
            content=content,
        )
    except Exception:
        pass


# ============================================================
# 7.1 导入辅导员
# ============================================================

def import_users(excel_file, operator_id):
    """
    导入辅导员 Excel
    通过表头名称匹配列位置，不依赖固定列顺序。
    必填列：工号, 姓名, 密码
    返回 {(success, data_or_error)}
    """
    try:
        from utils.excel import read_excel_with_headers, build_column_map, safe_cell_str
        headers, rows = read_excel_with_headers(excel_file)
    except Exception as e:
        return False, (500, f"Excel 文件读取失败：{str(e)}")

    # 字段名 → 可能的表头名称列表（越靠前优先级越高）
    field_mapping = {
        'username': ['工号', '用户名','username', '账号'],
        'name': ['姓名', 'name', '辅导员姓名','名字','辅导员名字'],
        'password': ['密码', 'password'],
        'role': ['角色', 'role'],
        'phone': ['电话', '手机', 'phone', '联系电话'],
    }
    col_map = build_column_map(headers, field_mapping)

    # 检查必填列是否存在
    required_fields = ['username', 'name', 'password']
    for field in required_fields:
        if field not in col_map:
            field_names = '/'.join(field_mapping[field])
            return False, (500, f"未找到必填列「{field_names}」，请检查表头名称")

    success_num = 0
    fail_reasons = []

    for i, row in enumerate(rows, start=2):
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue
        try:
            username = safe_cell_str(row, col_map['username'])
            name = safe_cell_str(row, col_map['name'])
            password = safe_cell_str(row, col_map['password'])
            role_str = safe_cell_str(row, col_map.get('role', -1))
            phone = safe_cell_str(row, col_map.get('phone', -1))

            if not username:
                fail_reasons.append({'row': i, 'msg': '工号为空'})
                continue
            if not name:
                fail_reasons.append({'row': i, 'msg': '姓名为空'})
                continue
            if not password:
                fail_reasons.append({'row': i, 'msg': '密码为空'})
                continue

            try:
                role = int(role_str)
            except ValueError:
                role = 1

            if User.objects.filter(username=username).exists():
                fail_reasons.append({'row': i, 'msg': '工号重复'})
                continue

            # name 参数传入 display_name 字段
            User.objects.create(
                username=username,
                password=password,
                display_name=name,
                role=role,
                phone=phone,
            )
            success_num += 1
        except Exception as e:
            fail_reasons.append({'row': i, 'msg': str(e)})

    fail_num = len(fail_reasons)
    ImportRecord.objects.create(
        file_name=excel_file.name,
        import_type='teacher',
        total_rows=len(rows),
        success_rows=success_num,
        fail_rows=fail_num,
        error_detail=json.dumps(fail_reasons[:100], ensure_ascii=False),
    )
    _write_log(operator_id, '用户管理', '批量导入', '辅导员', f'成功{success_num}条，失败{fail_num}条')
    return True, {
        'success_num': success_num,
        'fail_num': fail_num,
        'fail_reason': fail_reasons,
    }


# ============================================================
# 7.2 导入学生信息
# ============================================================

def import_students(excel_file, operator_id):
    """
    导入学生信息 Excel
    通过表头名称匹配列位置，不依赖固定列顺序。
    必填列：学号, 姓名, 辅导员姓名
    其余字段可选，无则留空
    返回 {(success, data_or_error)}
    """
    try:
        from utils.excel import read_excel_with_headers, safe_cell_str, build_column_map
        headers, rows = read_excel_with_headers(excel_file)
    except Exception as e:
        return False, (500, f"Excel 文件读取失败：{str(e)}")

    # 字段名 → 可能的表头名称列表（越靠前优先级越高）
    field_mapping = {
        'student_id': ['学号', '学生学号','学生编号', 'student_id', 'id'],
        'student_name': ['姓名', '学生姓名', 'name'],
        'advisor_name': ['辅导员姓名', '辅导员', 'advisor_name'],
        'advisor_username': ['辅导员工号', '工号', 'advisor_username'],
        'gender': ['性别', 'gender'],
        'grade': ['年级', 'grade'],
        'college': ['学院', '院系', 'college'],
        'class_name': ['班级', '班', 'class_name', 'class'],
        'major': ['专业','学生专业', 'major'],
        'ethnicity': ['民族', 'ethnicity', 'ethnic'],
        'native_place': ['籍贯', 'native_place'],
        'origin_place': ['生源地', 'origin_place'],
        'family_address': ['家庭所在地', '家庭住址', 'family_address'],
        'household_address': ['户籍所在地', '户籍地址', 'household_address'],
        'dorm_address': ['住宿地址', '宿舍地址', '宿舍', 'dorm_address'],
        'off_campus_address': ['校外住址', '校外住宿地址', '校外地址', 'off_campus_address'],
        'is_financial_difficulty': ['是否经济困难', '经济困难', 'is_financial_difficulty'],
        'is_academic_difficulty': ['是否学业困难', '学业困难', 'is_academic_difficulty'],
        'religion': ['宗教信仰', 'religion'],
        'enrollment_status': ['学籍状态', 'enrollment_status'],
        'photo_url': ['照片', '照片路径', 'photo_url', 'photo'],
    }
    col_map = build_column_map(headers, field_mapping)

    # 检查必填列是否存在
    required_fields = ['student_id', 'student_name', 'advisor_name']
    for field in required_fields:
        if field not in col_map:
            field_names = '/'.join(field_mapping[field])
            return False, (500, f"未找到必填列「{field_names}」，请检查表头名称")

    success_num = 0
    fail_reasons = []

    for i, row in enumerate(rows, start=2):
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue
        try:
            sid = safe_cell_str(row, col_map['student_id'])
            sname = safe_cell_str(row, col_map['student_name'])
            tgh = safe_cell_str(row, col_map['advisor_name'])
            advisor_username = safe_cell_str(row, col_map.get('advisor_username', -1))
            gender = safe_cell_str(row, col_map.get('gender', -1))
            grade = safe_cell_str(row, col_map.get('grade', -1))
            college_val = safe_cell_str(row, col_map.get('college', -1))
            class_name = safe_cell_str(row, col_map.get('class_name', -1))
            major = safe_cell_str(row, col_map.get('major', -1))
            ethnic = safe_cell_str(row, col_map.get('ethnicity', -1))
            hometown = safe_cell_str(row, col_map.get('native_place', -1))
            origin_place = safe_cell_str(row, col_map.get('origin_place', -1))
            family_address = safe_cell_str(row, col_map.get('family_address', -1))
            household_address = safe_cell_str(row, col_map.get('household_address', -1))
            addr = safe_cell_str(row, col_map.get('dorm_address', -1))
            outaddr = safe_cell_str(row, col_map.get('off_campus_address', -1))
            isfinancial = safe_cell_str(row, col_map.get('is_financial_difficulty', -1))
            isstudy = safe_cell_str(row, col_map.get('is_academic_difficulty', -1))
            religion = safe_cell_str(row, col_map.get('religion', -1))
            enrollment_status = safe_cell_str(row, col_map.get('enrollment_status', -1))
            photo_path = safe_cell_str(row, col_map.get('photo_url', -1))

            if not sid:
                fail_reasons.append({'row': i, 'msg': '学号为空'})
                continue
            if not sname:
                fail_reasons.append({'row': i, 'msg': '学生姓名为空'})
                continue
            if not tgh:
                fail_reasons.append({'row': i, 'msg': '辅导员姓名为空'})
                continue

            try:
                xid = int(sid)
            except ValueError:
                fail_reasons.append({'row': i, 'msg': '学号格式错误'})
                continue

            # ---- 辅导员查找逻辑 ----
            # 优先级 1：Excel 提供了辅导员工号 → 直接用工号精确匹配
            if advisor_username:
                advisor_user = User.objects.filter(
                    username=advisor_username, role=UserRole.COUNSELOR
                ).first()
            # 优先级 2：仅用辅导员姓名匹配（向后兼容）
            else:
                advisor_user = User.objects.filter(
                    Q(display_name=tgh) | Q(username=tgh), role=UserRole.COUNSELOR
                ).first()

            # ---- 照片路径默认值 ----
            # 若 Excel 未提供照片路径，默认使用学号（无扩展名，查找时自动匹配实际格式）
            if not photo_path:
                photo_path = str(xid)

            # 构建要更新的字段字典（仅非空值才写入）
            defaults = {
                'name': sname,
                'advisor_name': tgh,
            }
            if advisor_user:
                defaults['advisor_id'] = advisor_user.id
                defaults['advisor_phone'] = advisor_user.phone or ''
                if advisor_username:
                    defaults['advisor_username'] = advisor_username
            # 旧字段名到新字段名的映射（已删除的字段不再映射）
            field_map = {
                'gender': gender,
                'grade': grade,
                'college': college_val,
                'class_name': class_name,
                'major': major,
                'ethnicity': ethnic,
                'native_place': hometown,
                'origin_place': origin_place,
                'family_address': family_address,
                'household_address': household_address,
                'dorm_address': addr,
                'off_campus_address': outaddr,
                'is_financial_difficulty': isfinancial,
                'is_academic_difficulty': isstudy,
                'religion': religion,
                'enrollment_status': enrollment_status,
                'photo_url': photo_path,
            }
            for field, value in field_map.items():
                if value:
                    # 布尔字段转换："是" 或 "1" → True
                    if field in ('is_financial_difficulty', 'is_academic_difficulty'):
                        if value in ('是', '1', 'True', 'true', 'TRUE'):
                            defaults[field] = True
                        else:
                            defaults[field] = False
                    else:
                        defaults[field] = value

            # 使用 update_or_create，通过学号(id) 匹配
            Student.objects.update_or_create(
                id=xid,
                defaults=defaults,
            )
            success_num += 1
        except Exception as e:
            fail_reasons.append({'row': i, 'msg': str(e)})

    fail_num = len(fail_reasons)
    ImportRecord.objects.create(
        file_name=excel_file.name,
        import_type='student',
        total_rows=len(rows),
        success_rows=success_num,
        fail_rows=fail_num,
        error_detail=json.dumps(fail_reasons[:100], ensure_ascii=False),
    )
    _write_log(operator_id, '学生管理', '批量导入', '学生信息', f'成功{success_num}条，失败{fail_num}条')
    return True, {
        'success_num': success_num,
        'fail_num': fail_num,
        'fail_reason': fail_reasons,
    }


# ============================================================
# 7.3 用户管理
# ============================================================

def get_user_list(page=1, size=10, role=None, keyword=''):
    """用户列表（分页）"""
    qs = User.objects.all().order_by('-created_at')
    if role is not None:
        qs = qs.filter(role=role)
    if keyword:
        qs = qs.filter(Q(username__icontains=keyword) | Q(display_name__icontains=keyword))

    total = qs.count()
    pages = max(1, math.ceil(total / size))
    users = qs[(page - 1) * size: page * size]

    return True, {
        'list': [{
            'user_id': u.id,
            'username': u.username,
            'name': u.display_name or '',
            'role': u.role,
            'status': u.status,
            'phone': u.phone or '',
        } for u in users],
        'total': total,
        'pages': pages,
    }


def set_user_status(user_id, status, operator_id=None):
    """启用/禁用用户"""
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False, (404, "用户不存在")
    u.status = status
    u.save(update_fields=['status'])
    if operator_id:
        action_text = '启用' if status == 1 else '禁用'
        _write_log(operator_id, '用户管理', action_text, str(user_id))
    return True, {}


def reset_user_password(user_id, new_password, operator_id=None):
    """重置密码"""
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False, (404, "用户不存在")
    u.password = new_password
    u.save(update_fields=['password'])
    if operator_id:
        _write_log(operator_id, '用户管理', '重置密码', str(user_id))
    return True, {}


def edit_user_info(user_id, name=None, phone=None, operator_id=None):
    """编辑用户信息"""
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False, (404, "用户不存在")
    updates = {}
    if name is not None:
        updates['display_name'] = name
    if phone is not None:
        updates['phone'] = phone
    if updates:
        for k, v in updates.items():
            setattr(u, k, v)
        u.save(update_fields=list(updates.keys()))
        if operator_id:
            _write_log(operator_id, '用户管理', '编辑信息', str(user_id),
                       ', '.join(f'{k}={v}' for k, v in updates.items()))
    return True, {}


# ============================================================
# 7.4 管理员账号创建
# ============================================================

def create_admin(username, password, name, role, operator_id=None):
    """创建管理员（role=2批改员 或 role=3超管）"""
    if role not in (UserRole.GRADER, UserRole.SUPER_ADMIN):
        return False, (400, "角色无效，只能创建批改员或超管")
    if User.objects.filter(username=username).exists():
        return False, (400, "账号已存在")
    user = User.objects.create(
        username=username,
        password=password,
        display_name=name,
        role=role,
    )
    if operator_id:
        _write_log(operator_id, '账号管理', '创建管理员', username, f'角色={role}')
    return True, {'user_id': user.id}


# ============================================================
# 7.5 题库管理
# ============================================================

def get_question_list(page=1, size=10, q_type=None, keyword=''):
    """题库列表（分页）"""
    qs = QuestionTemplate.objects.all().order_by('-id')
    if q_type:
        qs = qs.filter(question_type=q_type)
    if keyword:
        qs = qs.filter(stem__icontains=keyword)

    total = qs.count()
    pages = max(1, math.ceil(total / size))
    questions = qs[(page - 1) * size: page * size]

    return True, {
        'list': [{
            'template_id': q.id,
            'title': q.stem,
            'type': q.question_type,
            'param_field': q.param_field or '',
            'analysis': q.explanation or '',
            'status': 1 if q.is_active else 0,
        } for q in questions],
        'total': total,
        'pages': pages,
    }


# ============================================================
# param_field 校验辅助
# ============================================================

def _get_valid_student_fields():
    """获取 students 表中所有有效字段名（含特殊关键字 roommates、classmates）"""
    from django.db.models.fields import Field as DjangoField
    valid_fields = set()
    for field in Student._meta.get_fields():
        # 只取模型上的具体字段（排除反向关系、OneToOneRel 等）
        if isinstance(field, DjangoField):
            valid_fields.add(field.name)
    # 特殊关键字：多选室友/同班同学（不映射到具体字段，由业务逻辑处理）
    valid_fields.update(['roommates', 'classmates'])
    return valid_fields


def _get_student_boolean_fields():
    """获取 students 表中的布尔类型字段名"""
    from django.db.models.fields import BooleanField
    boolean_fields = set()
    for field in Student._meta.get_fields():
        if isinstance(field, BooleanField):
            boolean_fields.add(field.name)
    return boolean_fields


def _validate_param_field(q_type, param_field):
    """
    校验 param_field 是否指向 students 表的有效字段
    返回 (is_valid, error_tuple) — is_valid=True 时 error_tuple 为 None
    """
    if q_type == 'essay':
        # 简答题不依赖 param_field，允许为空
        return True, None

    field_str = (param_field or '').strip()
    if not field_str:
        return False, (400, f"题型'{q_type}'的参数字段不能为空")

    valid_fields = _get_valid_student_fields()
    boolean_fields = _get_student_boolean_fields()

    if q_type == 'single':
        # 单选题：param_field 为单个字段名
        if field_str == 'classmates':
            return False, (400, "同班同学题仍为多选题，请选择多选题类型")
        if field_str not in valid_fields:
            return False, (400, f"参数字段'{field_str}'不在students表有效字段中")
        return True, None

    if q_type == 'judge':
        # 判断题：param_field 为单个字段名，且必须是布尔类型字段
        if field_str not in boolean_fields:
            return False, (400, f"参数字段'{field_str}'不是students表的布尔类型字段")
        return True, None

    if q_type == 'multi':
        # 多选题：特殊关键字 roommates/classmates，或 4 个及以上 field:value 条目
        if field_str == 'roommates':
            return False, (400, "室友题已改为单选题，请选择单选题类型")
        if field_str == 'classmates':
            return True, None
        entries = [e.strip() for e in field_str.split(',') if e.strip()]
        if len(entries) < 4:
            return False, (400, f"多选题参数字段至少需要4个条目，当前仅{len(entries)}个")
        for entry in entries:
            field_name = entry.split(':')[0].strip() if ':' in entry else entry.strip()
            if field_name not in valid_fields:
                return False, (400, f"参数字段'{field_name}'不在students表有效字段中")
        return True, None

    return True, None


def _get_available_templates_for_type(q_type):
    qs = QuestionTemplate.objects.filter(is_active=True)
    if q_type == 'single':
        return qs.filter(Q(question_type='single') | Q(param_field='roommates'))
    if q_type == 'multi':
        return qs.filter(question_type='multi').exclude(param_field='roommates')
    return qs.filter(question_type=q_type)


def add_question(title, q_type, param_field='', analysis='', operator_id=None):
    """新增题目（param_field 为指向 student 表的字段名或特殊关键字）"""
    if q_type not in ('single', 'multi', 'judge', 'essay'):
        return False, (400, "无效的题型")
    # 校验 param_field 是否指向 students 表有效字段
    ok, err = _validate_param_field(q_type, param_field)
    if not ok:
        return False, err
    qt = QuestionTemplate.objects.create(
        stem=title,
        question_type=q_type,
        param_field=param_field or None,
        explanation=analysis,
    )
    if operator_id:
        _write_log(operator_id, '题库管理', '新增题目', str(qt.id), title)
    return True, {'template_id': qt.id}


def edit_question(template_id, title=None, q_type=None, param_field=None,
                   analysis=None, operator_id=None):
    """编辑题目"""
    try:
        qt = QuestionTemplate.objects.get(id=template_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, "题目不存在")

    # 若题型或参数字段发生变化，校验最终组合是否合法
    if q_type is not None or param_field is not None:
        effective_type = q_type if q_type is not None else qt.question_type
        effective_param_field = param_field if param_field is not None else qt.param_field
        ok, err = _validate_param_field(effective_type, effective_param_field)
        if not ok:
            return False, err

    updates = {}
    if title is not None:
        updates['stem'] = title
    if q_type is not None:
        updates['question_type'] = q_type
    if param_field is not None:
        updates['param_field'] = param_field
    if analysis is not None:
        updates['explanation'] = analysis

    if updates:
        for k, v in updates.items():
            setattr(qt, k, v)
        qt.save(update_fields=list(updates.keys()))
        if operator_id:
            _write_log(operator_id, '题库管理', '编辑题目', str(template_id))
    return True, {}


def delete_question(template_id, operator_id=None):
    """删除题目（软删除，将 is_active 置为 False）"""
    try:
        qt = QuestionTemplate.objects.get(id=template_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, "题目不存在")

    # 软删除：将 is_active 置为 False
    qt.is_active = False
    qt.save(update_fields=['is_active'])
    if operator_id:
        _write_log(operator_id, '题库管理', '删除题目', str(template_id))
    return True, {}


def set_question_status(template_id, status, operator_id=None):
    """启用/禁用题目（status: 1=启用, 0=禁用）"""
    try:
        qt = QuestionTemplate.objects.get(id=template_id)
    except QuestionTemplate.DoesNotExist:
        return False, (404, "题目不存在")

    if status not in (0, 1):
        return False, (400, "状态值无效，仅支持0(禁用)或1(启用)")

    # 将整数 status 转换为布尔值写入 is_active 字段
    qt.is_active = bool(status)
    qt.save(update_fields=['is_active'])
    if operator_id:
        _write_log(operator_id, '题库管理', '启禁题目', str(template_id), f'状态={status}')
    return True, {}


# ============================================================
# 7.6 考试管理
# ============================================================

def get_exam_list_for_admin(page=1, size=10):
    """
    管理员/超管考试列表（含统计信息）
    返回所有考试，按发布日期倒序，每项包含考生总数、已交卷数、已批改数
    """
    exams = Exam.objects.all().order_by('-release_date')
    total = exams.count()
    pages = max(1, math.ceil(total / size))
    page_exams = exams[(page - 1) * size: page * size]

    if not page_exams:
        return True, {
            'list': [],
            'total': 0,
            'pages': 0,
        }

    # 批量查询所有相关考试的 ExamPaper 统计，避免 N+1
    exam_ids = [e.id for e in page_exams]
    # 获取每个考试的考生总数和已交卷数
    from django.db.models import Count, Q
    paper_stats = ExamPaper.objects.filter(exam_id__in=exam_ids).values('exam_id').annotate(
        total_counselors=Count('id'),
        submitted_count=Count('id', filter=Q(status=ExamPaper.Status.SUBMITTED)),
        graded_count=Count('id', filter=Q(is_graded=True)),
    )
    stats_map = {s['exam_id']: s for s in paper_stats}

    # 考试状态文字映射
    STATUS_TEXT = {
        ExamStatus.NOT_PUBLISHED: 'not_started',
        ExamStatus.IN_PROGRESS: 'normal',
        ExamStatus.ENDED: 'ended',
        ExamStatus.CLOSED: 'closed',
    }

    result_list = []
    for exam in page_exams:
        # 自动流转状态
        from apps.exam.services import _auto_transition_exam_status
        _auto_transition_exam_status(exam)

        stats = stats_map.get(exam.id, {})
        result_list.append({
            'exam_id': exam.id,
            'exam_name': exam.name,
            'exam_status': STATUS_TEXT.get(exam.status, 'not_started'),
            'release_date': exam.release_date.strftime('%Y-%m-%d') if exam.release_date else '',
            'start_time': timezone.localtime(exam.start_time).strftime('%Y-%m-%d %H:%M:%S') if exam.start_time else '',
            'duration': exam.duration_minutes,
            'total_counselors': stats.get('total_counselors', 0),
            'submitted_count': stats.get('submitted_count', 0),
            'graded_count': stats.get('graded_count', 0),
        })

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def _validate_exam_generation(question_configs):
    """
    考试创建前校验：检查模板库是否满足题型配置，以及各辅导员是否有学生
    返回 (is_valid, error_list)
      is_valid: True=通过，False=不通过
      error_list: 不通过时包含所有错误原因的字符串列表
    """
    errors = []

    # 1. 检查是否有在职辅导员
    counselors = User.objects.filter(role=UserRole.COUNSELOR, status=UserStatus.ENABLED)
    if not counselors.exists():
        errors.append("暂无在职辅导员账号，无法生成试卷")
        return False, errors

    # 2. 逐题型检查题库是否为空
    TYPE_NAMES = {'single': '单选题', 'multi': '多选题', 'judge': '判断题', 'essay': '简答题'}
    for qc in question_configs:
        q_type = qc.get('type', 'single')
        q_count = qc.get('count', 0)
        if q_count <= 0:
            continue
        available_count = QuestionTemplate.objects.filter(
            question_type=q_type, is_active=True
        ).count()
        if available_count == 0:
            type_name = TYPE_NAMES.get(q_type, q_type)
            errors.append(f"题库中无启用的{type_name}模板，无法生成{q_count}道{type_name}")

    # 3. 逐辅导员检查是否有学生
    for counselor in counselors:
        student_count = Student.objects.filter(advisor=counselor).count()
        if student_count == 0:
            errors.append(
                f"辅导员{counselor.display_name or counselor.username}"
                f"({counselor.username})名下无学生，无法为其生成试卷"
            )

    return (len(errors) == 0, errors)


def _generate_exam_papers(exam):
    """
    为考试预生成所有辅导员的考试题目（根据 generate_mode 分发到不同策略）
    在考试创建 / 编辑时调用，按 question_config 配置随机抽题、渲染题干
    使用 bulk_create 批量写入 ExamQuestion 表，减少数据库往返

    注意：调用前应确保已通过 _validate_exam_generation 校验，否则会抛出异常
    """
    config = exam.question_config if isinstance(exam.question_config, dict) else (json.loads(exam.question_config) if isinstance(exam.question_config, str) else {})
    generate_mode = config.get('generate_mode', 'by_type')

    if generate_mode == 'by_student':
        _generate_by_student(exam)
    else:
        _generate_by_type(exam)


def _generate_by_type(exam):
    """
    按题型出题（原有逻辑，完整保留）
    每个辅导员一套题，每道题从名下学生中随机分配一个学生
    sort_order 全局递增，题目按题型顺序排列
    """
    config = exam.question_config if isinstance(exam.question_config, dict) else (json.loads(exam.question_config) if isinstance(exam.question_config, str) else {})
    question_configs = config.get('questions', [])
    if not question_configs:
        raise ValueError("考试题型配置为空")

    # 获取所有在职辅导员
    counselors = User.objects.filter(role=UserRole.COUNSELOR, status=UserStatus.ENABLED)
    if not counselors.exists():
        raise ValueError("暂无在职辅导员账号")

    TYPE_NAMES = {'single': '单选题', 'multi': '多选题', 'judge': '判断题', 'essay': '简答题'}

    paper_items = []
    for counselor in counselors:
        # 通过辅导员外键匹配所带学生
        students = list(Student.objects.filter(advisor=counselor))
        if not students:
            raise ValueError(
                f"辅导员{counselor.display_name or counselor.username}"
                f"({counselor.username})名下无学生，无法生成试卷"
            )

        sort_order = 0
        for qc in question_configs:
            q_type = qc.get('type', 'single')
            q_count = qc.get('count', 0)
            q_score = qc.get('score', 0)
            if q_count <= 0:
                continue

            # 从题库中随机抽取该类型启用题目
            available = list(_get_available_templates_for_type(q_type))
            if len(available) == 0:
                type_name = TYPE_NAMES.get(q_type, q_type)
                raise ValueError(
                    f"题库中无启用的{type_name}模板，"
                    f"辅导员{counselor.display_name or counselor.username}无法生成{q_count}道{type_name}"
                )

            # 允许模板复用：若需题数 > 可用模板数，循环选取
            if q_count <= len(available):
                selected = random.sample(available, q_count)
            else:
                # 模板不足时循环复用：先用全部模板，再从模板池中随机补足差额
                selected = list(available)
                selected.extend(random.choices(available, k=q_count - len(available)))

            # 同一模板已分配的学生学号集合，避免同一考卷中出现相同的(模板, 学生)组合
            template_used_students = {}

            for template in selected:
                sort_order += 1

                # 为该模板优先选取未被分配过的学生，每个学生只出现一次
                student_name = '该生'
                student = None
                used_ids = template_used_students.get(template.id, set())
                available_students = [s for s in students if s.id not in used_ids]
                if available_students:
                    student = random.choice(available_students)
                else:
                    # 该模板所有学生都已用过，随机选一个（兜底）
                    student = random.choice(students)
                student_name = student.name
                template_used_students.setdefault(template.id, set()).add(student.id)

                # 渲染题干模板，替换占位符
                rendered_stem = template.stem.replace('{name}', student_name)

                # 动态生成选项和正确答案（基于学生真实数据）
                from apps.exam.services import _generate_dynamic_options, _resolve_generated_question_type
                options_json, correct_answer = _generate_dynamic_options(
                    template, student, students
                )
                question_type = _resolve_generated_question_type(template)

                # ExamQuestion 的 options 字段为 JSONField，直接传 dict 即可
                paper_items.append(ExamQuestion(
                    exam=exam,
                    user=counselor,
                    template=template,
                    student=student,
                    question_text=rendered_stem,
                    question_type=question_type,
                    options=options_json,
                    correct_answer=correct_answer,
                    score=q_score,
                    sort_order=sort_order,
                ))

    if paper_items:
        ExamQuestion.objects.bulk_create(paper_items)

    _create_paper_records(exam)


def _generate_by_student(exam):
    """
    按学生出题（新增模式）
    每个辅导员随机选 N 个学生，每个学生一套完整题目（所有题型各若干题）
    同一学生的所有题目都关联该学生，student_sort_order 学生组内递增
    总分 = 每道题分数相加，不强制=100
    """
    config = exam.question_config if isinstance(exam.question_config, dict) else (json.loads(exam.question_config) if isinstance(exam.question_config, str) else {})
    question_configs = config.get('questions', [])
    student_count = config.get('student_count', 0)
    if not question_configs:
        raise ValueError("考试题型配置为空")

    counselors = User.objects.filter(role=UserRole.COUNSELOR, status=UserStatus.ENABLED)
    if not counselors.exists():
        raise ValueError("暂无在职辅导员账号")

    TYPE_NAMES = {'single': '单选题', 'multi': '多选题', 'judge': '判断题', 'essay': '简答题'}

    paper_items = []
    for counselor in counselors:
        all_students = list(Student.objects.filter(advisor=counselor))
        if not all_students:
            raise ValueError(
                f"辅导员{counselor.display_name or counselor.username}"
                f"({counselor.username})名下无学生，无法生成试卷"
            )

        actual_count = student_count if student_count > 0 else len(all_students)
        actual_count = min(actual_count, len(all_students))

        difficulty_students = [
            s for s in all_students
            if s.is_academic_difficulty or s.is_financial_difficulty
        ]
        normal_students = [
            s for s in all_students
            if not s.is_academic_difficulty and not s.is_financial_difficulty
        ]

        difficulty_count = min(
            int(actual_count * 0.5),  ###########################
            len(difficulty_students),
        )
        normal_count = min(
            actual_count - difficulty_count,
            len(normal_students),
        )
        if difficulty_count + normal_count < actual_count:
            shortage = actual_count - difficulty_count - normal_count
            if len(difficulty_students) > difficulty_count:
                difficulty_count = min(difficulty_count + shortage, len(difficulty_students))
            elif len(normal_students) > normal_count:
                normal_count = min(normal_count + shortage, len(normal_students))

        selected_from_difficulty = random.sample(difficulty_students, difficulty_count) if difficulty_count > 0 else []
        selected_from_normal = random.sample(normal_students, normal_count) if normal_count > 0 else []
        selected_students = selected_from_difficulty + selected_from_normal
        random.shuffle(selected_students)

        sort_order = 0
        for student in selected_students:
            student_sort_order = 0
            for qc in question_configs:
                q_type = qc.get('type', 'single')
                q_count = qc.get('count', 0)
                q_score = qc.get('score', 0)
                if q_count <= 0:
                    continue

                available = list(_get_available_templates_for_type(q_type))
                if len(available) == 0:
                    type_name = TYPE_NAMES.get(q_type, q_type)
                    raise ValueError(
                        f"题库中无启用的{type_name}模板，"
                        f"辅导员{counselor.display_name or counselor.username}无法生成{q_count}道{type_name}"
                    )

                if q_count <= len(available):
                    selected_templates = random.sample(available, q_count)
                else:
                    selected_templates = list(available)
                    selected_templates.extend(random.choices(available, k=q_count - len(available)))

                for template in selected_templates:
                    sort_order += 1
                    student_sort_order += 1

                    rendered_stem = template.stem.replace('{name}', student.name)

                    from apps.exam.services import _generate_dynamic_options, _resolve_generated_question_type
                    options_json, correct_answer = _generate_dynamic_options(
                        template, student, all_students
                    )
                    question_type = _resolve_generated_question_type(template)

                    paper_items.append(ExamQuestion(
                        exam=exam,
                        user=counselor,
                        template=template,
                        student=student,
                        question_text=rendered_stem,
                        question_type=question_type,
                        options=options_json,
                        correct_answer=correct_answer,
                        score=q_score,
                        sort_order=sort_order,
                        student_sort_order=student_sort_order,
                    ))

    if paper_items:
        ExamQuestion.objects.bulk_create(paper_items)

    _create_paper_records(exam)


def _create_paper_records(exam):
    """
    为所有在职辅导员创建 ExamPaper 记录 + 分配批改员（两种模式共用）
    """
    counselors = User.objects.filter(role=UserRole.COUNSELOR, status=UserStatus.ENABLED)

    paper_records = []
    for counselor in counselors:
        paper_records.append(ExamPaper(
            exam=exam,
            user=counselor,
            status=ExamPaper.Status.NOT_STARTED,
        ))

    # 主观题批改分配：将试卷尽量平均随机分配给所有在职批改员
    if paper_records:
        graders = list(User.objects.filter(role=UserRole.GRADER, status=UserStatus.ENABLED))
        if graders:
            random.shuffle(paper_records)
            num_graders = len(graders)
            for i, paper in enumerate(paper_records):
                paper.assigned_grader = graders[i % num_graders]

        ExamPaper.objects.bulk_create(paper_records, ignore_conflicts=True)

        # 考试编辑场景：已有试卷需更新批改员分配
        # bulk_create 中 ignore_conflicts=True 会跳过已存在记录，需额外更新
        existing_papers = list(ExamPaper.objects.filter(exam_id=exam.id).order_by('id'))
        if graders and existing_papers:
            random.shuffle(existing_papers)
            for i, paper in enumerate(existing_papers):
                paper.assigned_grader = graders[i % num_graders]
            ExamPaper.objects.bulk_update(existing_papers, ['assigned_grader'])


def create_exam(exam_name, release_time, exam_start, exam_duration, questions, operator_id,
                 ai_grade_enabled=False, generate_mode='by_type', student_count=0):
    """
    创建考试，校验总分=100 与时间逻辑（by_student 模式总分=每题分数相加）
    创建前先校验模板库和学生数据是否满足条件，全部通过后在事务中创建考试并生成试卷
    """
    # 校验 student_count 范围（by_student 模式）
    if generate_mode == 'by_student' and student_count < 0:
        return False, (400, "学生人数不能为负数")

    # 发布日期不应晚于考试开始日期
    if isinstance(release_time, date) and not isinstance(release_time, datetime):
        if release_time > exam_start.date():
            return False, (400, "发布日期不能晚于考试开始日期")

    total_score = sum(q.get('score', 0) * q.get('count', 0) for q in questions)
    if generate_mode != 'by_student' and total_score != 100:
        return False, (4003, f"考试总分必须等于100分，当前配置总分为{total_score}")

    if exam_duration > 1440:
        return False, (400, "考试时长不能超过1440分钟（24小时）")

    exam_start_utc = exam_start
    if timezone.is_naive(exam_start_utc):
        exam_start_utc = timezone.make_aware(exam_start_utc)

    exam_end = exam_start_utc + timedelta(minutes=exam_duration)
    if exam_end < timezone.now():
        return False, (4004, "考试时长配置错误：考试结束时间已过")

    # 前置校验：模板库和学生数据是否满足题型配置
    is_valid, validation_errors = _validate_exam_generation(questions)
    if not is_valid:
        error_detail = "；".join(validation_errors)
        return False, (4005, f"试卷生成条件不满足：{error_detail}")

    # 在事务中创建考试并生成所有辅导员试卷，任意一步失败则回滚
    try:
        with transaction.atomic():
            config = {
                'questions': questions,
                'generate_mode': generate_mode,
                'student_count': student_count,
            }
            exam = Exam.objects.create(
                name=exam_name,
                release_date=release_time,
                start_time=exam_start_utc,
                duration_minutes=exam_duration,
                status=ExamStatus.NOT_PUBLISHED,
                question_config=config,
                created_by_id=operator_id,
                ai_grade_enabled=ai_grade_enabled,
            )

            # 同步预生成所有辅导员的考试题目
            _generate_exam_papers(exam)

    except ValueError as e:
        # _generate_exam_papers 抛出的业务异常
        return False, (4005, f"试卷生成失败：{str(e)}")
    except Exception as e:
        return False, (500, f"创建考试失败：{str(e)}")

    _write_log(operator_id, '考试管理', '创建考试', str(exam.id), exam_name)
    return True, {'exam_id': exam.id}


def set_exam_status(exam_id, status, operator_id=None):
    """考试发布/关闭 publish→status=1, close→status=3"""
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    if status == 'publish':
        exam.status = ExamStatus.IN_PROGRESS
    elif status == 'close':
        exam.status = ExamStatus.CLOSED
    else:
        return False, (400, "无效的状态参数")

    exam.save(update_fields=['status'])
    if operator_id:
        _write_log(operator_id, '考试管理', '状态变更', str(exam_id), f'状态={status}')
    return True, {}


def edit_exam(exam_id, exam_name=None, release_time=None, exam_start=None,
              exam_duration=None, questions=None, operator_id=None, ai_grade_enabled=None,
              generate_mode=None, student_count=None):
    """
    编辑考试信息（部分更新，未传字段保留原值）
    若修改了questions配置 / 出题模式 / 学生人数，重新校验并重建所有考生的题目
    """
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    updates = {}
    need_regenerate = False  # 标记是否需要重建题目

    if exam_name is not None:
        updates['name'] = exam_name

    if release_time is not None:
        updates['release_date'] = release_time

    if exam_start is not None:
        exam_start_utc = exam_start
        if timezone.is_naive(exam_start_utc):
            exam_start_utc = timezone.make_aware(exam_start_utc)
        updates['start_time'] = exam_start_utc

    if exam_duration is not None:
        if exam_duration > 1440:
            return False, (400, "考试时长不能超过1440分钟（24小时）")
        updates['duration_minutes'] = exam_duration

    if ai_grade_enabled is not None:
        updates['ai_grade_enabled'] = ai_grade_enabled

    if student_count is not None and student_count < 0:
        return False, (400, "学生人数不能为负数")

    # 仅在考试已发布后才要求结束时间不早于现在（允许提前配置未来考试）
    if exam.status == 1:
        effective_start = updates.get('start_time', exam.start_time)
        effective_duration = updates.get('duration_minutes', exam.duration_minutes)
        exam_end = effective_start + timedelta(minutes=effective_duration)
        if exam_end < timezone.now():
            return False, (4004, "考试时长配置错误：考试结束时间已过")

    # 读取或构建 question_config
    current_config = exam.question_config if isinstance(exam.question_config, dict) else {}
    effective_mode = generate_mode if generate_mode is not None else current_config.get('generate_mode', 'by_type')
    effective_student_count = student_count if student_count is not None else current_config.get('student_count', 0)
    effective_questions = questions if questions is not None else current_config.get('questions', [])

    if questions is not None or generate_mode is not None or student_count is not None:
        total_score = sum(q.get('score', 0) * q.get('count', 0) for q in effective_questions)
        if effective_mode != 'by_student' and total_score != 100:
            return False, (4003, f"考试总分必须等于100分，当前配置总分为{total_score}")
        config = {
            'questions': effective_questions,
            'generate_mode': effective_mode,
            'student_count': effective_student_count,
        }
        updates['question_config'] = config
        need_regenerate = True

    # 先保存考试元数据
    if updates:
        for k, v in updates.items():
            setattr(exam, k, v)
        exam.save(update_fields=list(updates.keys()))

    # 题型配置变更时：在事务中完成校验+重建，避免竞态条件
    if need_regenerate:
        try:
            with transaction.atomic():
                # 校验放在事务内，确保校验和生成之间数据一致性
                is_valid, validation_errors = _validate_exam_generation(effective_questions)
                if not is_valid:
                    error_detail = "；".join(validation_errors)
                    raise ValueError(error_detail)
                # 删除该考试下所有旧答案
                old_question_ids = list(
                    ExamQuestion.objects.filter(exam_id=exam_id).values_list('id', flat=True)
                )
                if old_question_ids:
                    ExamAnswer.objects.filter(question_id__in=old_question_ids).delete()
                ExamQuestion.objects.filter(exam_id=exam_id).delete()
                # 清除批改发布记录（试卷已重建，需重新批改和发布）
                GradePublish.objects.filter(exam_id=exam_id).delete()
                # 重置所有考生的考试状态为未开始
                ExamPaper.objects.filter(exam_id=exam_id).update(status=ExamPaper.Status.NOT_STARTED)
                # 重新生成题目
                _generate_exam_papers(exam)
        except ValueError as e:
            return False, (4005, f"试卷重新生成失败：{str(e)}")
        except Exception as e:
            return False, (500, f"编辑考试失败：{str(e)}")

    if updates and operator_id:
        _write_log(operator_id, '考试管理', '编辑考试', str(exam_id))

    return True, {}


def delete_exam(exam_id, operator_id=None):
    """
    删除考试（软删除，将 exams.status 置为 3=已关闭）
    返回 (success, data_or_error)
    """
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    exam_name = exam.name

    # 软删除：将考试状态置为"已关闭"，不物理删除关联数据
    exam.status = ExamStatus.CLOSED
    exam.save(update_fields=['status'])

    if operator_id:
        _write_log(operator_id, '考试管理', '删除考试', str(exam_id), exam_name)
    return True, {}


def preview_exam(exam_id):
    """考卷预览：按配置随机生成样卷题目（不保存）"""
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    if not exam.question_config:
        return False, (500, "考试题型配置为空")

    # question_config 是 JSONField，直接读取已反序列化的 dict，兼容字符串格式
    try:
        config = exam.question_config if isinstance(exam.question_config, dict) else (json.loads(exam.question_config) if isinstance(exam.question_config, str) else {})
    except (json.JSONDecodeError, TypeError):
        return False, (500, "考试题型配置格式错误")

    if not config:
        return False, (500, "考试题型配置为空")
    question_configs = config.get('questions', [])

    questions = []
    for qc in question_configs:
        q_type = qc.get('type', 'single')
        q_count = qc.get('count', 0)
        q_score = qc.get('score', 0)
        available = list(_get_available_templates_for_type(q_type))
        if len(available) < q_count:
            selected = available
        else:
            selected = random.sample(available, q_count)
        for t in selected:
            from apps.exam.services import _resolve_generated_question_type
            item = {
                'question_type': _resolve_generated_question_type(t),
                'title': t.stem,
                'score': q_score,
                'param_field': t.param_field or '',
            }
            questions.append(item)

    return True, {
        'exam_name': exam.name,
        'questions': questions,
    }


def _parse_cheat_detail(detail):
    """
    从 cheat_log.detail 字段提取 duration、screen_out_count
    兼容新旧格式：
      新(JSON): {"paper_id": 1, "duration": 10, "backend_count": 3, "frontend_count": 3}
      旧(字符串): duration=10s, backend_count=3, frontend_count=3
    """
    result = {'duration': 0, 'screen_out_count': 0}
    if not detail:
        return result
    # 优先尝试 JSON 解析
    if isinstance(detail, str) and detail.strip().startswith('{'):
        try:
            data = json.loads(detail)
            if isinstance(data, dict):
                result['duration'] = int(data.get('duration', 0))
                result['screen_out_count'] = int(data.get('backend_count', data.get('screen_out_count', 0)))
                return result
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    # 旧格式兜底
    parts = detail.replace(' ', '').split(',')
    for p in parts:
        if '=' not in p:
            continue
        k, v = p.split('=', 1)
        try:
            if k == 'duration':
                result['duration'] = int(v.rstrip('s'))
            elif k == 'backend_count':
                result['screen_out_count'] = int(v)
            elif k == 'screen_out_count':
                result['screen_out_count'] = int(v)
        except ValueError:
            pass
    return result


def get_abnormal_list(exam_id=None, page=1, size=10):
    """考试异常记录查看"""
    qs = CheatLog.objects.all().order_by('-occurred_at')
    if exam_id:
        qs = qs.filter(exam_id=exam_id)

    total = qs.count()
    pages = max(1, math.ceil(total / size))
    logs = qs[(page - 1) * size: page * size]

    # 提取 user_id 列表用于批量查姓名
    user_id_list = list(set(l.user_id for l in logs if l.user_id))
    name_map = {}
    if user_id_list:
        users = User.objects.filter(id__in=user_id_list).values('id', 'display_name', 'username')
        name_map = {u['id']: {'display_name': u['display_name'] or '', 'username': u['username']} for u in users}

    # 提取 exam_id 列表用于批量查考试名称
    exam_id_list = list(set(l.exam_id for l in logs if l.exam_id))
    exam_map = {}
    if exam_id_list:
        exams = Exam.objects.filter(id__in=exam_id_list).values('id', 'name')
        exam_map = {e['id']: e['name'] or '' for e in exams}

    result_list = []
    for l in logs:
        d = _parse_cheat_detail(l.detail)
        user_info = name_map.get(l.user_id, {})
        result_list.append({
            'id': l.id,
            'exam_id': l.exam_id,
            'exam_name': exam_map.get(l.exam_id, ''),
            'teacher_name': user_info.get('display_name', ''),
            'teacher_gh': user_info.get('username', ''),
            'type': l.action_type or '',
            'duration': d['duration'],
            'screen_out_count': d['screen_out_count'],
            'detail': l.detail or '',
            'action_time': timezone.localtime(l.occurred_at).strftime('%Y-%m-%d %H:%M:%S') if l.occurred_at else '',
        })

    return True, {
        'list': result_list,
        'total': total,
        'pages': pages,
    }


def get_user_status_list(exam_id, page=1, size=10, status=None, keyword=''):
    """
    7.6.5 考生状态列表
    返回每个考生状态、交卷时间、得分等
    """
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    # ExamPaper 替代了原 UserExam
    qs = ExamPaper.objects.filter(exam_id=exam_id).order_by('user_id')
    if status is not None:
        qs = qs.filter(status=status)

    # 按姓名或工号模糊查询
    if keyword:
        qs = qs.filter(user__username__icontains=keyword) | \
             qs.filter(user__display_name__icontains=keyword)

    total = qs.count()
    pages = max(1, math.ceil(total / size))
    records = qs[(page - 1) * size: page * size]

    # 通过 user_id 批量查询用户信息
    user_id_list = list(set(r.user_id for r in records))
    name_map = {}
    if user_id_list:
        users = User.objects.filter(id__in=user_id_list).values('id', 'display_name', 'username')
        name_map = {u['id']: {'display_name': u['display_name'] or '', 'username': u['username']} for u in users}

    # 映射到文档一.5 考试状态枚举: not_started / normal / submitted
    # ExamPaper.status: 0=未开始, 1=进行中, 2=已交卷, 3=异常交卷
    STATUS_TEXT = {
        ExamPaper.Status.NOT_STARTED: 'not_started',
        ExamPaper.Status.IN_PROGRESS: 'normal',
        ExamPaper.Status.SUBMITTED: 'submitted',
        ExamPaper.Status.ABNORMAL: 'submitted',
    }

    # ===== 判断已交卷的考生是否已全部批改 =====
    submitted_user_ids = set(
        r.user_id for r in records
        if r.status in (ExamPaper.Status.SUBMITTED, ExamPaper.Status.ABNORMAL)
    )
    fully_graded_user_ids = set()

    if submitted_user_ids:
        # 批量查询已交卷考生的所有主观题
        user_essay_qs = defaultdict(set)
        for eq in ExamQuestion.objects.filter(
            exam_id=exam_id,
            user_id__in=submitted_user_ids,
            question_type__in=SUBJECTIVE_TYPES,
        ).values('id', 'user_id'):
            user_essay_qs[eq['user_id']].add(eq['id'])

        # 查询已批改的主观题ID（score 不为空）
        all_essay_ids = [qid for ids in user_essay_qs.values() for qid in ids]
        if all_essay_ids:
            graded_ids = set(
                ExamAnswer.objects.filter(
                    question_id__in=all_essay_ids,
                    score__isnull=False,
                ).values_list('question_id', flat=True)
            )
            # 每位考生的主观题全部已批改 → 标记为已批改
            for uid, qids in user_essay_qs.items():
                if qids.issubset(graded_ids):
                    fully_graded_user_ids.add(uid)
        else:
            # 没有主观题 → 已交卷即视为已批改
            fully_graded_user_ids = submitted_user_ids

    return True, {
        'list': [{
            'paper_id': r.id,  # 试卷ID，用于跳转试卷详情/检查页
            'teacher_gh': name_map.get(r.user_id, {}).get('username', ''),
            'teacher_name': name_map.get(r.user_id, {}).get('display_name', ''),
            'status': 'graded' if r.user_id in fully_graded_user_ids
                      else STATUS_TEXT.get(r.status, str(r.status)),
            'submit_time': timezone.localtime(r.submitted_at).strftime('%Y-%m-%d %H:%M:%S') if r.submitted_at else '',
            'obj_score': r.objective_score,
            'subj_score': r.subjective_score,
            'total_score': r.total_score,
        } for r in records],
        'total': total,
        'pages': pages,
    }


# ============================================================
# 7.7 系统日志查询
# ============================================================

def get_log_list(page=1, size=10, module='', start_time='', end_time=''):
    """系统日志查询（分页）"""
    qs = SystemLog.objects.all().order_by('-created_at')
    if module:
        qs = qs.filter(module=module)
    if start_time:
        qs = qs.filter(created_at__gte=start_time)
    if end_time:
        qs = qs.filter(created_at__lte=end_time)

    total = qs.count()
    pages = max(1, math.ceil(total / size))
    logs = qs[(page - 1) * size: page * size]

    return True, {
        'list': [{
            'log_id': l.id,
            'user_id': l.operator_id,
            'module': l.module or '',
            'action': l.action or '',
            'target': l.target or '',
            'content': l.content or '',
            'create_time': timezone.localtime(l.created_at).strftime('%Y-%m-%d %H:%M:%S') if l.created_at else '',
        } for l in logs],
        'total': total,
        'pages': pages,
    }
