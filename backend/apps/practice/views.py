# -*- coding: utf-8 -*-
# 练习模块 - 视图层
# 适配新数据库模型：使用 request.user.id 和 request.user.display_name

from rest_framework.views import APIView

from utils.permissions import IsCounselor
from .services import (
    start_practice,
    submit_answer,
    view_answer,
    next_group,
    reset_progress,
    get_practice_result,
    get_favorites_list,
    add_favorite,
    remove_favorite,
    clear_favorites,
    replay_favorite,
    start_batch_practice,
    next_person,
    get_batch_progress,
)
from .serializers import (
    SubmitAnswerSerializer,
    ViewAnswerSerializer,
    NextGroupSerializer,
    FavoriteAddSerializer,
    FavoriteRemoveSerializer,
    FavoriteListSerializer,
    FavoriteReplaySerializer,
    StartBatchSerializer,
    NextPersonSerializer,
    BatchProgressSerializer,
)
from utils.response import ApiResponseSuccess, ApiResponseError, ApiResponseServerError


def _get_validated(serializer_cls, data_source):
    """通用序列化器校验辅助函数"""
    ser = serializer_cls(data=data_source)
    if not ser.is_valid():
        code = 400
        msg = _extract_first_error(ser.errors)
        return None, (code, msg)
    return ser.validated_data, None


def _extract_first_error(errors):
    """递归提取 DRF errors 中的第一条错误消息，兼容嵌套 ListField 的 dict 结构"""
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
        return str(errors)
    return ""


# ============================================================
# 2.1 开始练习 / 恢复练习
# ============================================================

class StartPracticeView(APIView):
    permission_classes = [IsCounselor]

    def post(self, request):
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = start_practice(user_id, advisor_name)
        except Exception as e:
            return ApiResponseServerError(msg=f"开始练习失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='开始练习成功')


# ============================================================
# 2.2 提交本题答案
# ============================================================

class SubmitAnswerView(APIView):
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(SubmitAnswerSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = submit_answer(
                data.get('session_id', ''),
                data.get('question_id'),
                data.get('user_answer', ''),
                user_id, advisor_name,
                answers=data.get('answers'),
            )
        except Exception as e:
            return ApiResponseServerError(msg=f"提交答案失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='提交成功')


# ============================================================
# 4. 多人逐个练习模式
# ============================================================

class StartBatchPracticeView(APIView):
    """4.1 开始多人逐个练习"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(StartBatchSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        count = data.get('count', 10)
        try:
            success, result = start_batch_practice(user_id, advisor_name, count)
        except Exception as e:
            return ApiResponseServerError(msg=f"开始练习失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='开始多人练习成功')


class NextPersonView(APIView):
    """4.2 切换到下一个人"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(NextPersonSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = next_person(data['session_id'], user_id, advisor_name)
        except Exception as e:
            return ApiResponseServerError(msg=f"切换失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='切换成功')


class BatchProgressView(APIView):
    """4.3 查询多人逐个练习进度"""
    permission_classes = [IsCounselor]

    def get(self, request):
        # 校验请求参数（从 query_params 读取）
        data, err = _get_validated(BatchProgressSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID
        user_id = request.user.id
        try:
            success, result = get_batch_progress(data['session_id'], user_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"查询失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


# ============================================================
# 2.3 查看本题答案
# ============================================================

class ViewAnswerView(APIView):
    permission_classes = [IsCounselor]

    def get(self, request):
        # 校验请求参数（从 query_params 读取）
        data, err = _get_validated(ViewAnswerSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = view_answer(
                data['session_id'], data['question_id'], user_id, advisor_name,
            )
        except Exception as e:
            return ApiResponseServerError(msg=f"查看答案失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


# ============================================================
# 2.4 下一组题目
# ============================================================

class NextGroupView(APIView):
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(NextGroupSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = next_group(data['session_id'], user_id, advisor_name)
        except Exception as e:
            return ApiResponseServerError(msg=f"切换失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='切换成功')


# ============================================================
# 2.5 重置练习进度
# ============================================================

class ResetProgressView(APIView):
    permission_classes = [IsCounselor]

    def post(self, request):
        # 仅需辅导员用户ID
        user_id = request.user.id
        try:
            success, result = reset_progress(user_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"重置失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='重置成功')


# ============================================================
# 2.6 练习结果统计
# ============================================================

class PracticeResultView(APIView):
    permission_classes = [IsCounselor]

    def get(self, request):
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = get_practice_result(user_id, advisor_name)
        except Exception as e:
            return ApiResponseServerError(msg=f"查询失败：{str(e)}")
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


# ============================================================
# 3. 收藏夹模块
# ============================================================

class FavoriteListView(APIView):
    """3.1 收藏列表"""
    permission_classes = [IsCounselor]

    def get(self, request):
        # 校验请求参数
        data, err = _get_validated(FavoriteListSerializer, request.query_params)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 获取辅导员用户ID和姓名
        user_id = request.user.id
        advisor_name = request.user.display_name
        try:
            success, result = get_favorites_list(
                user_id, advisor_name,
                page=data.get('page', 1),
                size=data.get('size', 10),
                sort_type=data.get('sort_type', 'time_desc'),
                keyword=data.get('keyword', ''),
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='查询成功')


class AddFavoriteView(APIView):
    """3.2 收藏题目"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(FavoriteAddSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 仅需辅导员用户ID（学生会话中已存储 student_xid）
        user_id = request.user.id
        try:
            success, result = add_favorite(
                data['session_id'], data['question_id'], user_id,
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='收藏成功')


class RemoveFavoriteView(APIView):
    """3.3 取消收藏"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(FavoriteRemoveSerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 仅需辅导员用户ID
        user_id = request.user.id
        try:
            success, result = remove_favorite(data['favorite_id'], user_id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='取消成功')


class ClearFavoritesView(APIView):
    """3.4 清空收藏"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 仅需辅导员用户ID
        user_id = request.user.id
        try:
            success, result = clear_favorites(user_id)
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(msg='清空成功')


class FavoriteReplayView(APIView):
    """3.5 收藏题目回放练习"""
    permission_classes = [IsCounselor]

    def post(self, request):
        # 校验请求参数
        data, err = _get_validated(FavoriteReplaySerializer, request.data)
        if err:
            return ApiResponseError(code=err[0], msg=err[1])
        # 仅需辅导员用户ID
        user_id = request.user.id
        try:
            success, result = replay_favorite(
                data['favorite_id'], data.get('user_answer', ''), user_id,
            )
        except Exception as e:
            return ApiResponseServerError(msg=str(e))
        if not success:
            return ApiResponseError(code=result[0], msg=result[1])
        return ApiResponseSuccess(data=result, msg='提交成功')
