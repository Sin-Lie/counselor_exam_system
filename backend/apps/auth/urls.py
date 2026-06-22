# -*- coding: utf-8 -*-
# 认证权限模块 - 路由配置

from django.urls import path
from . import views

# 认证模块路由
# 前缀已在 config/urls.py 中配置为 /api/auth/
urlpatterns = [
    # 辅导员登录
    path('login/', views.CounselorLoginView.as_view(), name='counselor_login'),
    # Token刷新
    path('refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    # 获取当前用户信息
    path('info/', views.UserInfoView.as_view(), name='user_info'),
    # 用户登出
    path('logout/', views.LogoutView.as_view(), name='user_logout'),
]

# 管理员登录路由（独立出口，需在config/urls.py中单独配置）
# 前缀在 config/urls.py 中配置为 /api/admin/
admin_urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin_login'),
]
