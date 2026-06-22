# -*- coding: utf-8 -*-
# 简答题批改模块 - 视图层
# 提供待批改列表、分数提交、进度统计、批改日志等API接口

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.permissions import IsAdminOrSuperAdmin, IsSuperAdmin
from .serializers import (
    ScoreSubmitSerializer,
    CorrectListSerializer,
    CorrectProgressSerializer,
    LogListSerializer,
    AIGradeConfigSerializer,
    AIGradeToggleSerializer,
    AIGradeLogListSerializer,
)
from .services import (
    get_correct_list, submit_score, get_correct_progress, get_correct_logs, publish_scores,
    get_ai_config, update_ai_config, test_ai_config, toggle_exam_ai_grade, get_ai_grade_logs,
)
from utils.response import ApiResponseSuccess, ApiResponseError


class CorrectListView(APIView):
    """
    待批改列表接口
    GET /api/correct/list/
    权限：管理员（role=2）、超级管理员（role=3）
    参数：exam_id（可选）、page、size
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        # 参数校验
        serializer = CorrectListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        exam_id = serializer.validated_data.get('exam_id')
        page = serializer.validated_data.get('page', 1)
        size = serializer.validated_data.get('size', 10)

        # 调用业务层，传入当前用户用于权限过滤
        success, result = get_correct_list(
            exam_id=exam_id,
            page=page,
            size=size,
            grader_user=request.user,
        )

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class CorrectScoreView(APIView):
    """
    提交/修改批改分数接口
    PUT /api/correct/score/{answer_id}/
    权限：管理员（role=2）、超级管理员（role=3）
    幂等性：重复提交覆盖原分数
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def put(self, request, answer_id):
        # 参数校验
        serializer = ScoreSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        score = serializer.validated_data['score']
        remark = serializer.validated_data.get('remark', '')

        # 调用业务层
        success, result = submit_score(
            answer_id=answer_id,
            score=score,
            remark=remark,
            grader_user=request.user,
        )

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(msg='批改成功')


class CorrectProgressView(APIView):
    """
    批改进度统计接口
    GET /api/correct/progress/
    权限：管理员（role=2）、超级管理员（role=3）
    参数：exam_id（可选）
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        # 参数校验
        serializer = CorrectProgressSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        exam_id = serializer.validated_data.get('exam_id')

        # 调用业务层，传入当前用户用于权限过滤
        success, result = get_correct_progress(
            exam_id=exam_id,
            grader_user=request.user,
        )

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class CorrectLogListView(APIView):
    """
    批改日志查询接口
    GET /api/correct/log/list/
    权限：仅超级管理员（role=3）
    参数：exam_id（可选）、grader_id（可选）、page、size
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        # 参数校验
        serializer = LogListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        exam_id = serializer.validated_data.get('exam_id')
        grader_id = serializer.validated_data.get('grader_id')
        page = serializer.validated_data.get('page', 1)
        size = serializer.validated_data.get('size', 10)

        # 调用业务层
        success, result = get_correct_logs(
            exam_id=exam_id,
            grader_id=grader_id,
            page=page,
            size=size,
        )

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class PublishScoresView(APIView):
    """
    发布批改成绩接口
    POST /api/correct/publish/{exam_id}/
    权限：管理员（role=2）、超级管理员（role=3）
    - role=2：改完自己负责的全部试卷后才能发布，仅发布自己的批改记录
    - role=3：可一键发布所有成绩，直接替该考试所有批改员发布，即使试卷未全部改完也能发布
    所有批改员都发布后辅导员才能查看成绩
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, exam_id):
        success, result = publish_scores(
            exam_id=exam_id,
            grader_user=request.user,
        )
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='发布成功')


# ==================== AI 批改 API 视图 ====================

class AIGradeConfigView(APIView):
    """
    AI 批改配置管理接口
    GET /api/correct/ai-config/  — 获取配置
    PUT /api/correct/ai-config/  — 更新配置
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        """获取 AI 批改全局配置"""
        success, result = get_ai_config()
        return ApiResponseSuccess(data=result, msg='查询成功')

    def put(self, request):
        """更新 AI 批改全局配置"""
        serializer = AIGradeConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        success, result = update_ai_config(serializer.validated_data)
        return ApiResponseSuccess(msg='保存成功')


class AIGradeTestView(APIView):
    """
    测试 AI 连接
    POST /api/correct/ai-config/test/
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        success, result = test_ai_config()
        if result['success']:
            return ApiResponseSuccess(data=result, msg='测试成功')
        else:
            return ApiResponseSuccess(data=result, msg='测试失败')


class AIGradeToggleView(APIView):
    """
    考试 AI 批改开关
    PUT /api/correct/ai-grade/toggle/{exam_id}/
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def put(self, request, exam_id):
        serializer = AIGradeToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        enabled = serializer.validated_data['enabled']
        success, result = toggle_exam_ai_grade(exam_id, enabled)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(msg=result[1])


class AIGradeLogListView(APIView):
    """
    AI 批改日志查询
    GET /api/correct/ai-grade/logs/
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        serializer = AIGradeLogListSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        exam_id = serializer.validated_data.get('exam_id')
        status = serializer.validated_data.get('status')
        page = serializer.validated_data.get('page', 1)
        size = serializer.validated_data.get('size', 10)

        success, result = get_ai_grade_logs(
            exam_id=exam_id,
            status=status,
            page=page,
            size=size,
        )
        return ApiResponseSuccess(data=result, msg='查询成功')
