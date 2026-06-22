# -*- coding: utf-8 -*-
# 认证权限模块 - 业务逻辑层

import time
import logging
from typing import List, Optional, Tuple, Union

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from utils.redis_client import RedisClient
from utils.response import ApiResponseError

User = get_user_model()
logger = logging.getLogger(__name__)


def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    从 Authorization 请求头中提取 Bearer token
    返回 token 字符串或 None（格式无效时）
    """
    if not auth_header:
        return None
    try:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        return parts[1]
    except (IndexError, ValueError):
        return None


def generate_jwt_token(user) -> str:
    """
    生成JWT access token（短期有效）
    包含用户ID（user.id 为主键）、角色、过期时间等信息
    """
    payload = {
        'user_id': user.id,  # user.id 直接是主键
        'username': user.username,
        'role': user.role,
        'type': 'access',
        'iat': int(time.time()),
        'exp': int(time.time()) + settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def generate_refresh_token(user) -> str:
    """
    生成JWT refresh token（长期有效，仅用于刷新access token）
    包含 user_id、type='refresh'，过期时间比 access token 长
    """
    payload = {
        'user_id': user.id,
        'type': 'refresh',
        'iat': int(time.time()),
        'exp': int(time.time()) + settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    # 将 refresh token 存入 Redis，用于登出时批量失效
    try:
        redis_client = RedisClient()
        key = f"refresh_token:{user.id}"
        redis_client.sadd(key, token)
        redis_client.expire(key, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
    except Exception:
        logger.warning("Redis不可用，refresh token未持久化存储")
    return token


def verify_refresh_token(token: str) -> Tuple[bool, Union[object, str]]:
    """
    验证 refresh token 的有效性
    返回 (success, user_or_error_msg)
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return False, "Refresh token已过期，请重新登录"
    except jwt.InvalidTokenError:
        return False, "无效的Refresh token"

    # 检查token类型
    if payload.get('type') != 'refresh':
        return False, "非法的token类型，仅接受refresh token"

    user_id = payload.get('user_id')
    if not user_id:
        return False, "Refresh token无效：缺少用户ID"

    # 检查 refresh token 是否仍在 Redis 中（未登出）
    try:
        redis_client = RedisClient()
        key = f"refresh_token:{user_id}"
        if not redis_client.sismember(key, token):
            return False, "Refresh token已失效，请重新登录"
    except Exception:
        logger.warning("Redis不可用，跳过refresh token存在性检查")

    # 获取用户
    try:
        user = User.objects.get(id=user_id, status=1)
    except User.DoesNotExist:
        return False, "用户不存在或已被禁用"

    return True, user


def revoke_all_refresh_tokens(user_id: int) -> None:
    """
    撤销指定用户的所有 refresh token（登出时调用）
    """
    try:
        redis_client = RedisClient()
        key = f"refresh_token:{user_id}"
        redis_client.delete(key)
    except Exception:
        logger.warning("Redis不可用，refresh token撤销失败")


def check_login_rate_limit(username: str) -> bool:
    """
    检查登录频率限制（每分钟最多5次）
    Redis不可用时记录警告并默认放行
    """
    try:
        redis_client = RedisClient()
        rate_key = f"login_rate:{username}"

        count = redis_client.get(rate_key)
        if count is None:
            redis_client.setex(rate_key, 1, 60)
            return True
        elif int(count) >= 5:
            return False
        else:
            redis_client.incr(rate_key)
            redis_client.expire(rate_key, 60)  # 重置TTL，防止key永不过期
            return True
    except Exception:
        logger.warning("Redis不可用，登录频率限制被绕过 for user: %s", username)
        return True


def authenticate_user(
    username: str,
    password: str,
    allowed_roles: Optional[List[int]] = None,
) -> Tuple[bool, Union[object, object]]:
    """
    统一用户登录验证
    返回：(success, user_or_error_response)
    """
    # 频率限制检查
    if not check_login_rate_limit(username):
        return False, ApiResponseError(code=400, msg="登录过于频繁，请稍后再试")

    # 查找用户
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        _log_failed_login(username, '账号不存在')
        return False, ApiResponseError(code=4001, msg="账号或密码错误")

    # 检查用户是否激活（status 字段，UserStatus.ENABLED=1 表示启用）
    if not user.status:
        _log_failed_login(username, '账号已被禁用')
        return False, ApiResponseError(code=4001, msg="账号或密码错误")

    # 密码校验
    if not user.check_password(password):
        _log_failed_login(username, '密码错误')
        return False, ApiResponseError(code=4002, msg="账号或密码错误")

    # 检查角色权限
    if allowed_roles is not None and user.role not in allowed_roles:
        return False, ApiResponseError(code=403, msg="无权限登录，请使用正确的登录入口")

    # 更新最后登录时间（新字段名 last_login_at）
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])

    # 记录登录日志
    _log_login(user)

    return True, user


def _log_login(user):
    """
    记录用户登录日志到 system_log 表
    SystemLog 现在使用 operator 字段（FK 到 User）而非旧的 user_id
    """
    try:
        from apps.system.models import SystemLog
        SystemLog.objects.create(
            operator=user,  # 新字段名：operator（ForeignKey 到 User）
            module='auth',
            action='login',
            target=f"user_id={user.id}",  # user.id 直接是主键
            content=f"用户 {user.username}({user.display_name or ''}) 登录系统，角色={user.role}",
        )
    except Exception:
        logger.exception("记录登录日志失败")


def _log_failed_login(username, reason):
    """
    记录失败的登录尝试
    失败登录无关联用户，不传 operator 字段
    """
    try:
        from apps.system.models import SystemLog
        SystemLog.objects.create(
            module='auth',
            action='login_failed',
            content=f"用户 {username} 登录失败，原因：{reason}",
        )
    except Exception:
        logger.exception("记录失败登录日志异常")


def add_token_to_blacklist(token: str) -> bool:
    """
    将token加入黑名单（登出时调用），同时撤销所有refresh token
    返回 True 表示成功或 token 已过期无需处理
    返回 False 表示 Redis 异常，黑名单写入失败
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        exp = payload.get('exp', 0)
        now = int(time.time())
        ttl = max(exp - now, 0)

        if ttl > 0:
            redis_client = RedisClient()
            blacklist_key = f"token_blacklist:{token}"
            redis_client.setex(blacklist_key, "1", ttl)

        # 同时撤销该用户的所有 refresh token
        user_id = payload.get('user_id')
        if user_id:
            revoke_all_refresh_tokens(user_id)

        return True
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return True
    except Exception:
        logger.error("Redis异常：token黑名单写入失败")
        return False
