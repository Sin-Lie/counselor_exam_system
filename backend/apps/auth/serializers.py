# -*- coding: utf-8 -*-
# 认证权限模块 - 序列化器

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器
    校验username和password参数
    """

    username = serializers.CharField(
        required=True,
        error_messages={'required': '请输入用户名', 'blank': '用户名不能为空'}
    )
    password = serializers.CharField(
        required=True,
        error_messages={'required': '请输入密码', 'blank': '密码不能为空'},
        write_only=True
    )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Token刷新序列化器
    校验 refresh_token 参数
    """
    refresh_token = serializers.CharField(
        required=True,
        error_messages={'required': '请提供refresh_token', 'blank': 'refresh_token不能为空'}
    )


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器
    返回用户基本信息（display_name 为真实姓名）
    """
    class Meta:
        model = User
        fields = ['username', 'display_name', 'role']  # 新字段名：display_name 替代原 name
