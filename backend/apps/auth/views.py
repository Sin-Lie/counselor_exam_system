# -*- coding: utf-8 -*-
# 认证权限模块 - 视图层

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import UserRole
from .serializers import LoginSerializer, UserInfoSerializer, RefreshTokenSerializer
from .services import (
    generate_jwt_token,
    generate_refresh_token,
    authenticate_user,
    add_token_to_blacklist,
    extract_bearer_token,
    verify_refresh_token,
)
from utils.response import ApiResponseSuccess, ApiResponseError, ApiResponseUnauthorized


def _get_serializer_error_msg(serializer):
    """将序列化器所有校验错误拼接为单个字符串"""
    errors = []
    for field, msgs in serializer.errors.items():
        errors.extend(msgs)
    return errors[0] if len(errors) == 1 else '; '.join(errors)


class BaseLoginView(APIView):
    """登录基类，子类通过 allowed_roles 控制可登录的角色"""
    permission_classes = [AllowAny]
    allowed_roles = None

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=_get_serializer_error_msg(serializer))

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        success, result = authenticate_user(username, password, allowed_roles=self.allowed_roles)
        if not success:
            return result

        user = result
        token = generate_jwt_token(user)
        refresh_token = generate_refresh_token(user)

        return ApiResponseSuccess(
            data={
                'token': token,
                'refresh_token': refresh_token,
                'name': user.display_name or user.username,  # 新字段名：display_name 替代原 name
                'role': user.role,
            },
            msg='登录成功',
        )


class CounselorLoginView(BaseLoginView):
    """
    辅导员登录接口
    POST /api/auth/login/
    """
    allowed_roles = [UserRole.COUNSELOR]


class AdminLoginView(BaseLoginView):
    """
    管理员/超管登录接口
    POST /api/admin/login/
    """
    allowed_roles = [UserRole.GRADER, UserRole.SUPER_ADMIN]


class UserInfoView(APIView):
    """
    获取当前用户信息接口
    GET /api/auth/info/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserInfoSerializer(user)
        return ApiResponseSuccess(data=serializer.data, msg='查询成功')


class TokenRefreshView(APIView):
    """
    Token刷新接口
    POST /api/auth/refresh/
    使用 refresh_token 换取新的 access token（refresh token 本身不会被刷新）
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponseError(code=400, msg=_get_serializer_error_msg(serializer))

        refresh_token = serializer.validated_data['refresh_token']
        success, result = verify_refresh_token(refresh_token)
        if not success:
            return ApiResponseUnauthorized(msg=result)

        user = result
        new_token = generate_jwt_token(user)
        return ApiResponseSuccess(
            data={'token': new_token},
            msg='Token刷新成功',
        )


class LogoutView(APIView):
    """
    用户登出接口
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        token = extract_bearer_token(auth_header)
        if token is None:
            return ApiResponseError(code=400, msg='无效的认证格式')

        if not add_token_to_blacklist(token):
            return ApiResponseError(code=500, msg='登出失败，请稍后重试')

        return ApiResponseSuccess(msg='登出成功')
