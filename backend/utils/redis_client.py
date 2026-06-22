# -*- coding: utf-8 -*-
# Redis客户端工具类
# 用于Redis连接管理和常见操作封装

import time
import socket
from typing import Any, List, Optional, Union

import redis
from django.conf import settings

# Redis是否可用的全局缓存标志
_redis_available = None
# 上次检测时间戳（Unix秒），用于定期刷新缓存
_last_redis_check_time = 0
# 缓存有效期（秒）：60秒后重新检测Redis可用性，避免永久缓存失败状态
_REDIS_CHECK_INTERVAL = 60


def _check_redis_available() -> bool:
    """
    检测Redis服务是否可达
    使用原始TCP连接探测，设置短超时避免阻塞
    缓存有效期为60秒，过期后自动重新检测，避免Redis恢复后系统仍不可用
    """
    global _redis_available, _last_redis_check_time
    now = time.time()
    # 缓存未过期时直接返回（None表示首次检测，也需进入检测逻辑）
    if _redis_available is not None and (now - _last_redis_check_time) < _REDIS_CHECK_INTERVAL:
        return _redis_available
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((settings.REDIS_HOST, settings.REDIS_PORT))
        sock.close()
        _redis_available = (result == 0)
    except Exception:
        _redis_available = False
    _last_redis_check_time = now
    return _redis_available


def get_redis_connection() -> redis.Redis:
    """
    获取Redis连接实例
    使用settings中的REDIS配置
    """
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=False,
    )


class RedisClient:
    """Redis操作封装类"""

    def __init__(self):
        if not _check_redis_available():
            raise ConnectionError("Redis服务不可用")
        self.client = get_redis_connection()

    def setex(self, key, value, timeout):
        """设置带过期时间的键值对"""
        return self.client.setex(key, timeout, value)

    def get(self, key):
        """获取键值"""
        return self.client.get(key)

    def delete(self, key):
        """删除键"""
        return self.client.delete(key)

    def exists(self, key):
        """检查键是否存在"""
        return self.client.exists(key)

    def incr(self, key):
        """自增"""
        return self.client.incr(key)

    def expire(self, key, timeout):
        """设置过期时间"""
        return self.client.expire(key, timeout)

    def ttl(self, key):
        """获取剩余生存时间"""
        return self.client.ttl(key)

    def smembers(self, key):
        """获取集合所有成员"""
        return self.client.smembers(key)

    def sadd(self, key, value):
        """向集合添加成员"""
        return self.client.sadd(key, value)

    def sismember(self, key, value):
        """检查成员是否在集合中"""
        return self.client.sismember(key, value)

    def srem(self, key, value):
        """从集合移除成员"""
        return self.client.srem(key, value)
