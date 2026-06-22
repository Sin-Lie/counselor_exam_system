# -*- coding: utf-8 -*-
# 成绩模块 - 权限类（已统一迁移至 utils/permissions.py）
# 此处保留兼容导入，新代码请直接使用 utils.permissions

from utils.permissions import IsCounselor, IsSuperAdmin, IsAdminOrSuperAdmin

IsCounselorPermission = IsCounselor              # 兼容旧名称
IsSuperAdminPermission = IsSuperAdmin            # 兼容旧名称
IsGraderOrSuperAdminPermission = IsAdminOrSuperAdmin  # 兼容旧名称
