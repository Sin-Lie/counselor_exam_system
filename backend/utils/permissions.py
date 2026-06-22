# -*- coding: utf-8 -*-
# 全局权限类（统一入口）
# 所有业务模块均从此处导入权限类，避免重复定义
# 角色枚举：1=辅导员, 2=批改员, 3=超级管理员

from rest_framework.permissions import BasePermission


class IsCounselor(BasePermission):
    """仅辅导员（role=1）可访问"""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and request.user.role == 1
        )


class IsGrader(BasePermission):
    """仅批改员（role=2）可访问"""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and request.user.role == 2
        )


class IsSuperAdmin(BasePermission):
    """仅超级管理员（role=3）可访问"""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and request.user.role == 3
        )


class IsAdminOrSuperAdmin(BasePermission):
    """管理员或超管（role=2 或 3）可访问"""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and request.user.role in (2, 3)
        )
