# -*- coding: utf-8 -*-
# 全局异常处理工具类
# 统一处理Django和DRF的异常

from rest_framework.views import exception_handler
from .response import ApiResponse, ApiResponseServerError


def custom_exception_handler(exc, context):
    """
    自定义DRF异常处理器
    将DRF异常转换为统一响应格式
    对应settings/base.py中 EXCEPTION_HANDLER 配置
    """
    # 先调用DRF默认的异常处理
    response = exception_handler(exc, context)

    if response is not None:
        # 获取原始错误信息
        detail = response.data
        if isinstance(detail, dict):
            # 提取第一个错误信息
            first_error = list(detail.values())[0]
            if isinstance(first_error, list):
                msg = str(first_error[0])
            else:
                msg = str(first_error)
        elif isinstance(detail, list):
            msg = str(detail[0])
        else:
            msg = str(detail)

        # 映射状态码到业务错误码
        code_map = {
            400: 400,
            401: 401,
            403: 403,
            404: 404,
            405: 400,
            429: 400,
            500: 500,
        }

        code = code_map.get(response.status_code, 500)

        return ApiResponse(code=code, msg=msg, data={})

    # 非DRF异常，返回服务器错误
    return ApiResponseServerError(msg=str(exc) if str(exc) else "服务器异常")
