# -*- coding: utf-8 -*-
# 系统管理模块 - 视图层

from rest_framework.views import APIView

from utils.permissions import IsSuperAdmin, IsAdminOrSuperAdmin
from .services import (
    import_users,
    import_students,
    get_user_list,
    set_user_status,
    reset_user_password,
    edit_user_info,
    create_admin,
    get_question_list,
    add_question,
    edit_question,
    delete_question,
    set_question_status,
    create_exam,
    edit_exam,
    delete_exam,
    set_exam_status,
    preview_exam,
    get_abnormal_list,
    get_user_status_list,
    get_exam_list_for_admin,
    get_log_list,
)
from .serializers import (
    UserListSerializer,
    SetStatusSerializer,
    ResetPasswordSerializer,
    EditUserSerializer,
    CreateAdminSerializer,
    QuestionAddSerializer,
    QuestionEditSerializer,
    CreateExamSerializer,
    SetExamStatusSerializer,
    EditExamSerializer,
    ExamAbnormalListSerializer,
    ExamListSerializer,
    ExamUserStatusSerializer,
    LogListSerializer,
    QuestionListSerializer,
)
from utils.response import ApiResponseSuccess, ApiResponseError, ApiResponseServerError


def _get_validated(serializer_cls, data_source):
    """统一参数校验辅助函数"""
    ser = serializer_cls(data=data_source)
    if not ser.is_valid():
        code = 400
        # 从 DRF 校验错误中提取第一条错误消息，兼容嵌套 ListField 的 dict 结构
        msg = _extract_first_error(ser.errors)
        return None, (code, msg)
    return ser.validated_data, None


def _extract_first_error(errors):
    """递归提取 DRF errors 中的第一条错误消息"""
    if isinstance(errors, list):
        for item in errors:
            result = _extract_first_error(item)
            if result:
                return result
    elif isinstance(errors, dict):
        for key in sorted(errors.keys(), key=lambda k: str(k)):
            result = _extract_first_error(errors[key])
            if result:
                return result
    else:
        # ErrorDetail 或普通字符串
        return str(errors)
    return ""


# ============================================================
# 7.1-7.2 导入
# ============================================================

class ImportUsersView(APIView):
    """导入辅导员 Excel"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return ApiResponseError(code=400, msg="请上传 Excel 文件")
        try:
            success, result = import_users(file, request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=f"导入失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='导入完成')


class ImportStudentsView(APIView):
    """导入学生信息 Excel"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return ApiResponseError(code=400, msg="请上传 Excel 文件")
        try:
            success, result = import_students(file, request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=f"导入失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='导入完成')


# ============================================================
# 7.3 用户管理
# ============================================================

class UserListView(APIView):
    """用户列表"""
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data, err = _get_validated(UserListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_user_list(**data)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


class SetUserStatusView(APIView):
    """启用/禁用用户"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(SetStatusSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = set_user_status(data['user_id'], data['status'],
                                              operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='操作成功')


class ResetPasswordView(APIView):
    """重置用户密码"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(ResetPasswordSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = reset_user_password(data['user_id'], data['new_password'],
                                                   operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='密码重置成功')


class EditUserView(APIView):
    """编辑用户信息"""
    permission_classes = [IsSuperAdmin]

    def put(self, request, user_id):
        data, err = _get_validated(EditUserSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            kwargs = {}
            if 'name' in data:
                kwargs['name'] = data['name']
            if 'phone' in data:
                kwargs['phone'] = data['phone']
            if not kwargs:
                return ApiResponseError(code=400, msg="无修改内容")
            success, result = edit_user_info(user_id, operator_id=request.user.id, **kwargs)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='编辑成功')


# ============================================================
# 7.4 管理员创建
# ============================================================

class CreateAdminView(APIView):
    """创建管理员/超管"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(CreateAdminSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        if data['role'] not in (2, 3):
            return ApiResponseError(code=400, msg="角色只能为2(批改员)或3(超管)")
        try:
            success, result = create_admin(
                data['username'], data['password'], data['name'], data['role'],
                operator_id=request.user.id
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='创建成功')


# ============================================================
# 7.5 题库管理
# ============================================================

class QuestionListView(APIView):
    """题库列表"""
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data, err = _get_validated(QuestionListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_question_list(
                page=data.get('page', 1),
                size=data.get('size', 10),
                q_type=data.get('type') or None,
                keyword=data.get('keyword', ''),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


class AddQuestionView(APIView):
    """新增题目"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(QuestionAddSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = add_question(
                title=data['title'],
                q_type=data['type'],
                param_field=data.get('param_field', ''),
                analysis=data.get('analysis', ''),
                operator_id=request.user.id,
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='添加成功')


class EditQuestionView(APIView):
    """编辑题目"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, template_id):
        data, err = _get_validated(QuestionEditSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = edit_question(
                template_id,
                title=data.get('title'),
                q_type=data.get('type'),
                param_field=data.get('param_field'),
                analysis=data.get('analysis'),
                operator_id=request.user.id,
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='编辑成功')


class DeleteQuestionView(APIView):
    """删除题目"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, template_id):
        try:
            success, result = delete_question(template_id, operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='删除成功')


class SetQuestionStatusView(APIView):
    """启用/禁用题目"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, template_id):
        status = request.data.get('status')
        try:
            status = int(status)
        except (TypeError, ValueError):
            return ApiResponseError(code=400, msg="状态值无效")
        try:
            success, result = set_question_status(template_id, status, operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='操作成功')


# ============================================================
# 7.6 考试管理
# ============================================================

class AdminExamListView(APIView):
    """
    管理员/超管考试列表（含统计信息）
    GET /api/system/exam/list/
    权限：管理员（role=2）或超级管理员（role=3）
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        data, err = _get_validated(ExamListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_exam_list_for_admin(
                page=data.get('page', 1),
                size=data.get('size', 10),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


class CreateExamView(APIView):
    """创建考试"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(CreateExamSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = create_exam(
                exam_name=data['exam_name'],
                release_time=data['release_time'],
                exam_start=data['exam_start'],
                exam_duration=data['exam_duration'],
                questions=data['questions'],
                operator_id=request.user.id,
                ai_grade_enabled=data.get('ai_grade_enabled', False),
                generate_mode=data.get('generate_mode', 'by_type'),
                student_count=data.get('student_count', 0),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='创建成功')


class SetExamStatusView(APIView):
    """考试发布/关闭"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        data, err = _get_validated(SetExamStatusSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = set_exam_status(data['exam_id'], data['status'],
                                               operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='操作成功')


class EditExamView(APIView):
    """编辑考试信息"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, exam_id):
        data, err = _get_validated(EditExamSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = edit_exam(
                exam_id,
                operator_id=request.user.id,
                ai_grade_enabled=data.get('ai_grade_enabled'),
                **{k: v for k, v in data.items() if v is not None and k != 'ai_grade_enabled'},
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='编辑成功')


class DeleteExamView(APIView):
    """删除考试（软删除，将考试状态置为已关闭）"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, exam_id):
        try:
            success, result = delete_exam(exam_id, operator_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='删除成功')


class ExamPreviewView(APIView):
    """考卷预览"""
    permission_classes = [IsSuperAdmin]

    def get(self, request, exam_id):
        try:
            success, result = preview_exam(exam_id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='预览生成成功')


class ExamAbnormalListView(APIView):
    """考试异常记录查看"""
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data, err = _get_validated(ExamAbnormalListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_abnormal_list(
                exam_id=data.get('exam_id'),
                page=data.get('page', 1),
                size=data.get('size', 10),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


class ExamUserStatusView(APIView):
    """考生状态列表 (7.6.5 - 路由在 exam 模块)"""
    permission_classes = [IsSuperAdmin]

    def get(self, request, exam_id):
        data, err = _get_validated(ExamUserStatusSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_user_status_list(
                exam_id,
                page=data.get('page', 1),
                size=data.get('size', 10),
                status=data.get('status'),
                keyword=data.get('keyword', ''),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


# ============================================================
# 7.7 系统日志
# ============================================================

class LogListView(APIView):
    """系统日志查询"""
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data, err = _get_validated(LogListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        try:
            success, result = get_log_list(
                page=data.get('page', 1),
                size=data.get('size', 10),
                module=data.get('module', ''),
                start_time=data.get('start_time', ''),
                end_time=data.get('end_time', ''),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')
