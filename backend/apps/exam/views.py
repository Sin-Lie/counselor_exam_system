# -*- coding: utf-8 -*-
# 考试模块 - 视图层
# 负责 HTTP 请求处理、参数提取、调用业务层、返回序列化响应

from rest_framework.views import APIView

from utils.permissions import IsCounselor, IsSuperAdmin
from .services import (
    get_exam_list,
    get_exam_info,
    enter_exam,
    get_saved_answers,
    save_answer,
    submit_exam,
    report_abnormal,
    get_paper_review,
    preload_exam_images,
)
from .serializers import (
    ExamItemSerializer,
    ExamInfoSerializer,
    QuestionSerializer,
    SavedAnswersSerializer,
    SaveAnswerSerializer,
    ReportAbnormalSerializer,
)
from utils.response import (
    ApiResponseSuccess,
    ApiResponseNotFound,
    ApiResponseError,
    ApiResponseServerError,
)


class ExamListView(APIView):
    """
    获取考试列表接口
    GET /api/exam/list/
    权限：仅辅导员（role=1）可访问
    返回所有考试的名称和状态（按发布日期倒序）
    """

    permission_classes = [IsCounselor]

    def get(self, request):
        try:
            exam_list = get_exam_list(user_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=f"获取考试列表失败：{str(e)}")

        # 序列化输出，确保字段格式符合接口文档
        serializer = ExamItemSerializer(data=exam_list, many=True)
        serializer.is_valid(raise_exception=True)

        return ApiResponseSuccess(
            data={'list': serializer.data},
            msg='查询成功'
        )


class ExamInfoView(APIView):
    """
    获取考试详情接口
    GET /api/exam/info/{exam_id}/
    权限：仅辅导员（role=1）可访问
    返回考试时长、起止时间、状态、剩余时间（秒）
    """

    permission_classes = [IsCounselor]

    def get(self, request, exam_id):
        try:
            exam_info = get_exam_info(exam_id, user_id=request.user.id)
        except Exception as e:
            return ApiResponseServerError(msg=f"获取考试详情失败：{str(e)}")

        if exam_info is None:
            return ApiResponseNotFound(msg="考试不存在")

        serializer = ExamInfoSerializer(data=exam_info)
        serializer.is_valid(raise_exception=True)

        return ApiResponseSuccess(data=serializer.data, msg='查询成功')


class EnterExamView(APIView):
    """
    进入考试接口（支持断线恢复）
    POST /api/exam/enter/{exam_id}/
    权限：仅辅导员（role=1）可访问

    首次进入：按题型配置随机抽题生成试卷，每题关联随机学生
    断线恢复：返回已有试卷及答案回填

    注意：返回的 paper_id 为考试记录ID（UserExam.record_id），
          题目级别的 question_id 对应 ExamPaper.paper_id
    """

    permission_classes = [IsCounselor]

    def post(self, request, exam_id):
        user_id = request.user.id
        user_display_name = request.user.display_name or request.user.username

        try:
            success, result = enter_exam(exam_id, user_id, user_display_name)
        except Exception as e:
            return ApiResponseServerError(msg=f"进入考试失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        data = result
        # by_student 模式返回分组结构
        if data.get('question_groups'):
            return ApiResponseSuccess(
                data={
                    'paper_id': data['paper_id'],
                    'is_resumed': data['is_resumed'],
                    'generate_mode': 'by_student',
                    'student_count': data.get('student_count', 0),
                    'question_groups': data['question_groups'],
                    'exam_status': data['exam_status'],
                },
                msg='恢复考试成功' if data['is_resumed'] else '进入考试成功'
            )

        questions_serializer = QuestionSerializer(data=data['questions'], many=True)
        questions_serializer.is_valid(raise_exception=True)

        return ApiResponseSuccess(
            data={
                'paper_id': data['paper_id'],
                'is_resumed': data['is_resumed'],
                'questions': questions_serializer.data,
                'exam_status': data['exam_status'],
            },
            msg='恢复考试成功' if data['is_resumed'] else '进入考试成功'
        )


class SavedAnswersView(APIView):
    """
    获取已保存答案接口（断线快速恢复专用）
    GET /api/exam/saved-answers/{paper_id}/
    权限：仅辅导员（role=1）可访问
    返回所有题目已保存的答案键值对，避免重新拉取整份试卷
    """

    permission_classes = [IsCounselor]

    def get(self, request, paper_id):
        user_id = request.user.id

        try:
            success, result = get_saved_answers(paper_id, user_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"获取已保存答案失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        serializer = SavedAnswersSerializer(data=result)
        serializer.is_valid(raise_exception=True)

        return ApiResponseSuccess(data=serializer.data, msg='查询成功')


class SaveAnswerView(APIView):
    """
    实时保存答案接口
    POST /api/exam/save/
    权限：仅辅导员（role=1）可访问
    频率限制：每秒最多 1 次
    支持 reconnect 参数标记断线重连保存
    """

    permission_classes = [IsCounselor]

    def post(self, request):
        # 请求参数校验
        req_serializer = SaveAnswerSerializer(data=request.data)
        if not req_serializer.is_valid():
            return ApiResponseError(
                code=400,
                msg=list(req_serializer.errors.values())[0][0]
            )

        user_id = request.user.id
        paper_id = req_serializer.validated_data['paper_id']
        question_id = req_serializer.validated_data.get('question_id')
        user_answer = req_serializer.validated_data.get('user_answer', '') or ''
        save_time = req_serializer.validated_data['save_time']
        reconnect = req_serializer.validated_data.get('reconnect', False)
        answers = req_serializer.validated_data.get('answers')

        try:
            success, result = save_answer(
                paper_id, question_id, user_answer, save_time,
                user_id, reconnect, answers=answers,
            )
        except Exception as e:
            return ApiResponseServerError(msg=f"保存答案失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        return ApiResponseSuccess(data=result, msg='保存成功')


class SubmitExamView(APIView):
    """
    交卷接口
    POST /api/exam/submit/{paper_id}/
    权限：仅辅导员（role=1）可访问
    幂等控制：1 用户 1 考试仅可提交 1 次
    客观题自动判分，主观题等待管理员批改
    """

    permission_classes = [IsCounselor]

    def post(self, request, paper_id):
        user_id = request.user.id

        try:
            success, result = submit_exam(paper_id, user_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"交卷失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        # result 为 dict，包含 objective_score、total_score
        return ApiResponseSuccess(data=result, msg='交卷成功')


class ReportAbnormalView(APIView):
    """
    考试异常日志上报接口（含强制交卷判断）
    POST /api/exam/report-abnormal/
    权限：仅辅导员（role=1）可访问
    频率限制：每秒最多 1 次

    后端独立判断强制交卷条件：
        - 切屏累计 > 3 次
        - 单次切出时长 > 10 秒
    前端上报值仅作参考，不作为判断依据
    """

    permission_classes = [IsCounselor]

    def post(self, request):
        # 请求参数校验
        req_serializer = ReportAbnormalSerializer(data=request.data)
        if not req_serializer.is_valid():
            return ApiResponseError(
                code=400,
                msg=list(req_serializer.errors.values())[0][0]
            )

        user_id = request.user.id
        paper_id = req_serializer.validated_data['paper_id']
        exam_id = req_serializer.validated_data['exam_id']
        abnormal_type = req_serializer.validated_data['type']
        duration = req_serializer.validated_data['duration']
        screen_out_count = req_serializer.validated_data['screen_out_count']

        try:
            success, result = report_abnormal(
                paper_id, exam_id, user_id,
                abnormal_type, duration, screen_out_count
            )
        except Exception as e:
            return ApiResponseServerError(msg=f"异常上报失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        if result.get('force_submit'):
            return ApiResponseSuccess(
                data=result,
                msg='异常次数过多，系统将强制交卷'
            )

        return ApiResponseSuccess(data=result, msg='上报成功')


class PaperReviewView(APIView):
    """
    超管试卷检查接口
    GET /api/exam/paper-review/{paper_id}/
    权限：仅超级管理员（role=3）
    用途：试卷生成后、考试开考前，超管人工检查所有考生试卷是否正确生成
    返回格式与进入考试（POST /api/exam/enter/{exam_id}/）一致，但不含 user_answer
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, paper_id):
        try:
            success, result = get_paper_review(paper_id, request.user)
        except Exception as e:
            return ApiResponseServerError(msg=f"获取试卷详情失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        return ApiResponseSuccess(data=result, msg='查询成功')


class PreloadImagesView(APIView):
    """
    预加载试卷图片接口
    GET /api/exam/preload-images/{paper_id}/
    权限：辅导员（role=1）和超级管理员（role=3）

    考生考试开始前10分钟入场，点击"进入考试"后调用本接口。
    超管阅卷时也调用本接口，确保学生照片正常显示。
    后端扫描该试卷所有题目选项中的图片路径，读取文件并 base64 编码返回。
    前端接收后解码缓存为 Blob URL，考试正式开始后直接从缓存渲染图片，
    避免考试开始瞬间大量并发请求图片造成服务器压力过大。
    """

    permission_classes = [IsCounselor | IsSuperAdmin]

    def get(self, request, paper_id):
        user_id = request.user.id
        user_role = request.user.role

        try:
            success, result = preload_exam_images(paper_id, user_id, viewer_role=user_role)
        except Exception as e:
            return ApiResponseServerError(msg=f"预加载图片失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        # 该试卷无图片可预加载，返回成功但 data 为 null
        if result is None:
            return ApiResponseSuccess(msg="该试卷无需预加载图片")

        return ApiResponseSuccess(data=result, msg="预加载成功")


class ExportStudentsView(APIView):
    """
    导出考试学生信息接口
    GET /api/exam/export-students/{exam_id}/
    权限：仅超级管理员（role=3）
    导出该考试所有辅导员试卷抽取到的学生的全部信息（Excel）
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request, exam_id):
        from .services import export_exam_students

        try:
            success, result = export_exam_students(exam_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"导出学生信息失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        # result 是 HttpResponse 文件流，直接返回
        return result
