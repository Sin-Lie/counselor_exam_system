# -*- coding: utf-8 -*-
# 认证权限模块 - 用户模型

from django.db import models


class UserRole(models.IntegerChoices):
    """用户角色枚举"""
    COUNSELOR = 1, '辅导员'
    GRADER = 2, '批改员'
    SUPER_ADMIN = 3, '超级管理员'


class UserStatus(models.IntegerChoices):
    """用户状态枚举"""
    DISABLED = 0, '禁用'
    ENABLED = 1, '启用'


class User(models.Model):
    """
    系统用户模型（对应数据库 users 表）
    角色枚举：
        role=1：辅导员
        role=2：批改员
        role=3：超级管理员
    """

    class Meta:
        app_label = 'accounts'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users'

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'username'

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='用户ID',
    )

    # 登录账号（辅导员为工号，管理员为字母+数字）
    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='登录账号',
    )

    # 密码（明文存储，根据需求文档）
    password = models.CharField(
        max_length=200,
        verbose_name='密码',
    )

    # 角色
    role = models.SmallIntegerField(
        choices=UserRole.choices,
        default=UserRole.COUNSELOR,
        verbose_name='角色',
    )

    # 状态
    status = models.SmallIntegerField(
        choices=UserStatus.choices,
        default=UserStatus.ENABLED,
        verbose_name='状态',
    )

    # 手机号
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='手机号',
    )

    # 真实姓名
    display_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='真实姓名',
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
    )

    # 最后更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='最后更新时间',
    )

    # 最后登录时间
    last_login_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='最后登录时间',
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display() or '未知角色'}"

    def set_password(self, raw_password):
        """明文存储密码（根据系统需求不使用哈希加密）"""
        self.password = raw_password

    def check_password(self, raw_password):
        """明文密码校验"""
        return self.password == raw_password

    @property
    def is_active(self):
        """兼容 Django 的 is_active 属性"""
        return self.status == UserStatus.ENABLED

    @property
    def is_authenticated(self):
        """兼容 Django 的 is_authenticated 属性"""
        return True

    @property
    def is_anonymous(self):
        """兼容 Django 的 is_anonymous 属性"""
        return False
