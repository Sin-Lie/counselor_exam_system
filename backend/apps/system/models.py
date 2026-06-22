# -*- coding: utf-8 -*-
# 系统管理模块 - 数据库模型
# 对应数据库表：question_templates, students, system_logs, import_records

from django.conf import settings
from django.db import models


class QuestionType(models.TextChoices):
    """题目类型枚举"""
    SINGLE = 'single', '单选题'
    MULTI = 'multi', '多选题'
    JUDGE = 'judge', '判断题'
    ESSAY = 'essay', '简答题'


class QuestionTemplate(models.Model):
    """
    题目模板表（对应数据库 question_templates 表）
    存储题库中的题目模板，支持动态替换学生信息生成题目
    """

    class Meta:
        app_label = 'system'
        verbose_name = '题目模板'
        verbose_name_plural = '题目模板'
        db_table = 'question_templates'

    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='模板ID',
    )

    # 题型
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        verbose_name='题型',
    )

    # 题干模板（含占位符如 {name}）
    stem = models.CharField(
        max_length=500,
        verbose_name='题干模板',
    )

    # 参数字段（指向 student 表的字段名或特殊关键字）
    param_field = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='参数字段',
    )

    # 题目解析
    explanation = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='题目解析',
    )

    # 是否启用
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用',
    )

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.stem[:50]}"


class Student(models.Model):
    """
    学生信息表（对应数据库 students 表）
    """

    class Meta:
        app_label = 'system'
        verbose_name = '学生信息'
        verbose_name_plural = '学生信息'
        db_table = 'students'
        indexes = [
            models.Index(fields=['advisor_name']),
            models.Index(fields=['class_name']),
            models.Index(fields=['college']),
        ]

    # 学号（主键）
    id = models.BigIntegerField(
        primary_key=True,
        verbose_name='学号',
    )

    # 姓名
    name = models.CharField(
        max_length=100,
        verbose_name='姓名',
    )

    # 性别
    gender = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='性别',
    )

    # 学院
    college = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='学院',
    )

    # 年级
    grade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='年级',
    )

    # 班级（Python 保留字，用 db_column 映射）
    class_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_column='class',
        verbose_name='班级',
    )

    # 专业
    major = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='专业',
    )

    # 辅导员（外键关联用户表，可获取姓名、电话等信息）
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='辅导员',
    )

    # 辅导员姓名（冗余存储，方便导入和展示）
    advisor_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='辅导员姓名',
    )

    # 辅导员电话（从关联的 users.phone 同步）
    advisor_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='辅导员电话',
    )

    # 辅导员工号（冗余存储，导入时若提供工号则直接填入）
    advisor_username = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='辅导员工号',
    )

    # 民族
    ethnicity = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='民族',
    )

    # 籍贯
    native_place = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='籍贯',
    )

    # 生源地
    origin_place = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='生源地',
    )

    # 家庭所在地
    family_address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='家庭所在地',
    )

    # 户籍所在地
    household_address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='户籍所在地',
    )

    # 是否学业困难
    is_academic_difficulty = models.BooleanField(
        default=False,
        verbose_name='是否学业困难',
    )

    # 宗教信仰
    religion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='宗教信仰',
    )

    # 住宿地址
    dorm_address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='住宿地址',
    )

    # 校外住宿地址
    off_campus_address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='校外住宿地址',
    )

    # 是否经济困难
    is_financial_difficulty = models.BooleanField(
        default=False,
        verbose_name='是否经济困难',
    )

    # 学籍状态
    enrollment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='学籍状态',
    )

    # 照片地址
    photo_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='照片地址',
    )

    def __str__(self):
        return f"{self.id} - {self.name}"


class SystemLog(models.Model):
    """
    系统操作日志表（对应数据库 system_logs 表）
    """

    class Meta:
        app_label = 'system'
        verbose_name = '系统日志'
        verbose_name_plural = '系统日志'
        db_table = 'system_logs'

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='日志ID',
    )

    # 操作人
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='操作人',
    )

    # 操作模块
    module = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='操作模块',
    )

    # 动作
    action = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='动作',
    )

    # 操作对象
    target = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='操作对象',
    )

    # 日志详情
    content = models.TextField(
        blank=True,
        null=True,
        verbose_name='日志详情',
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
    )

    def __str__(self):
        return f"[{self.module}|{self.action}] {self.target}"


class ImportRecord(models.Model):
    """
    数据导入记录表（对应数据库 import_records 表）
    """

    class Meta:
        app_label = 'system'
        verbose_name = '导入记录'
        verbose_name_plural = '导入记录'
        db_table = 'import_records'

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='记录ID',
    )

    # 导入文件名
    file_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='导入文件名',
    )

    # 导入类型
    import_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='导入类型',
    )

    # 总行数
    total_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='总行数',
    )

    # 成功数
    success_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='成功数',
    )

    # 失败数
    fail_rows = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='失败数',
    )

    # 错误详情
    error_detail = models.TextField(
        blank=True,
        null=True,
        verbose_name='错误详情',
    )

    # 导入时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='导入时间',
    )

    def __str__(self):
        return f"{self.file_name} ({self.import_type})"
