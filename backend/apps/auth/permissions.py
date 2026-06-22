# -*- coding: utf-8 -*-
# 认证权限模块 - 权限类（已统一迁移至 utils/permissions.py）
# 此处保留兼容导入，新代码请直接使用 utils.permissions

from utils.permissions import IsCounselor, IsGrader, IsSuperAdmin, IsAdminOrSuperAdmin

IsAdmin = IsGrader  # 兼容旧名称
