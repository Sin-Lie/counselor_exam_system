# -*- coding: utf-8 -*-
# 成绩与统计模块 - 视图层
# 提供我的成绩、试卷详情、考试统计、未参考清单、Excel导出等API接口

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.permissions import (
    IsCounselor,
    IsSuperAdmin,
    IsAdminOrSuperAdmin,
)
from .serializers import ExportScopeSerializer
from .services import (
    get_my_score,
    get_my_paper_detail,
    get_paper_detail,
    get_exam_statistics,
    get_unattended_list,
    export_exam_scores,
)
from utils.response import ApiResponseSuccess, ApiResponseError


class MyScoreView(APIView):
    """
    我的成绩接口
    GET /api/score/my/{exam_id}/
    权限：辅导员（role=1）
    """
    permission_classes = [IsAuthenticated, IsCounselor]

    def get(self, request, exam_id):
        # 使用用户ID（原工号username）作为查询参数
        user_id = request.user.id
        success, result = get_my_score(exam_id, user_id)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class MyPaperDetailView(APIView):
    """
    我的考试试卷详情接口
    GET /api/score/my-paper/{paper_id}/
    权限：辅导员（role=1），且 paper_id 必须属于当前用户
    """
    permission_classes = [IsAuthenticated, IsCounselor]

    def get(self, request, paper_id):
        # 使用用户ID（原工号username）作为查询参数
        user_id = request.user.id
        success, result = get_my_paper_detail(paper_id, user_id)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class PaperDetailView(APIView):
    """
    查看任意考生试卷详情接口
    GET /api/score/paper-detail/{paper_id}/    —— 通过试卷ID查询
    GET /api/score/paper-detail/?exam_id=X&user_id=Y   —— 通过考试ID+用户ID查询
    权限：批改员（role=2）需有批改关系，超级管理员（role=3）可查看任意
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request, paper_id=None):
        # 传递当前登录用户对象，由 service 层进行权限细粒度校验
        success, result = get_paper_detail(paper_id, request.user, request.query_params)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class ExamStatisticsView(APIView):
    """
    考试整体统计接口
    GET /api/score/statistics/{exam_id}/
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, exam_id):
        success, result = get_exam_statistics(exam_id)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class UnattendedListView(APIView):
    """
    未参考人员清单接口
    GET /api/score/unattended/{exam_id}/
    权限：超级管理员（role=3）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, exam_id):
        success, result = get_unattended_list(exam_id)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        return ApiResponseSuccess(data=result, msg='查询成功')


class ExportScoresView(APIView):
    """
    导出成绩Excel接口
    GET /api/score/export/{exam_id}/
    权限：超级管理员（role=3）
    参数：export_scope（可选，all=全部，graded_only=仅已出成绩，默认all）
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, exam_id):
        # 参数校验
        serializer = ExportScopeSerializer(data=request.query_params)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=list(serializer.errors.values())[0][0])

        export_scope = serializer.validated_data.get('export_scope', 'all')

        success, result = export_exam_scores(exam_id, export_scope)

        if not success:
            return ApiResponseError(code=result[0], msg=result[1])

        # result 是 HttpResponse 文件流，直接返回
        return result
