# -*- coding: utf-8 -*-
# 认证权限模块 - JWT认证类

import jwt
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .services import extract_bearer_token
from .models import UserStatus
from utils.redis_client import RedisClient

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """
    自定义JWT认证类
    从请求头 Authorization: Bearer {token} 中解析token
    校验token有效性并返回用户
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        token = extract_bearer_token(auth_header)

        if token is None:
            if not auth_header:
                return None  # 无token，不报错，允许匿名访问
            raise AuthenticationFailed('无效的认证格式')

        # 解码验证token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token已过期')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('无效的Token')

        # 检查token是否在黑名单中（已登出）
        try:
            redis_client = RedisClient()
            blacklist_key = f"token_blacklist:{token}"
            if redis_client.exists(blacklist_key):
                raise AuthenticationFailed('Token已失效，请重新登录')
        except AuthenticationFailed:
            raise
        except Exception:
            logger.warning("Redis不可用，token黑名单检查被跳过")

        # 获取用户（id 直接是主键，status 使用 UserStatus.ENABLED 常量）
        try:
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token无效：缺少用户ID')
            user = User.objects.get(id=user_id, status=UserStatus.ENABLED)  # id 为主键，status 用枚举常量
        except User.DoesNotExist:
            raise AuthenticationFailed('用户不存在或已被禁用')

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
