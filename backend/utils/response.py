# -*- coding: utf-8 -*-
# 统一返回格式工具类
# 提供标准化的API响应格式

from typing import Any, Dict, Optional, Union

from rest_framework.response import Response


def ApiResponse(
    code: int = 200,
    msg: str = "操作成功",
    data: Optional[Dict[str, Any]] = None,
    status: Optional[int] = None,
) -> Response:
    """
    统一API响应格式
    根据接口文档规范：{code: 200, msg: "操作成功", data: {}}
    """
    if data is None:
        data = {}
    return Response({"code": code, "msg": msg, "data": data}, status=status or 200)


def ApiResponseSuccess(
    data: Optional[Dict[str, Any]] = None,
    msg: str = "操作成功",
) -> Response:
    """操作成功响应"""
    return ApiResponse(code=200, msg=msg, data=data)


def _business_code_to_http_status(code: int) -> int:
    """
    将业务错误码映射为 HTTP 状态码
    若业务码在标准 HTTP 范围内(100-599)，直接用作 HTTP 状态码
    否则返回 200，保留业务码在响应体中区分
    """
    if isinstance(code, int) and 100 <= code <= 599:
        return code
    return 200


def ApiResponseError(
    code: int = 400,
    msg: str = "参数错误",
    data: Optional[Dict[str, Any]] = None,
) -> Response:
    """操作失败响应，HTTP状态码依据业务码自动映射"""
    return ApiResponse(code=code, msg=msg, data=data, status=_business_code_to_http_status(code))


def ApiResponseUnauthorized(msg: str = "未登录") -> Response:
    """未授权响应（401），HTTP状态码正确返回401"""
    return ApiResponse(code=401, msg=msg, data={}, status=401)


def ApiResponseForbidden(msg: str = "无权限") -> Response:
    """无权限响应（403），HTTP状态码正确返回403"""
    return ApiResponse(code=403, msg=msg, data={}, status=403)


def ApiResponseNotFound(msg: str = "资源不存在") -> Response:
    """资源不存在响应（404），HTTP状态码正确返回404"""
    return ApiResponse(code=404, msg=msg, data={}, status=404)


def ApiResponseServerError(msg: str = "服务器异常") -> Response:
    """服务器异常响应（500），HTTP状态码正确返回500"""
    return ApiResponse(code=500, msg=msg, data={}, status=500)
