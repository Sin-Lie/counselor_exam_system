# -*- coding: utf-8 -*-
# 练习模块 - 数据库模型
# 对应数据库表：practice_progresses, practice_favorites

from django.conf import settings
from django.db import models


class PracticeProgress(models.Model):
    """
    练习进度表（对应数据库 practice_progresses 表）
    记录每个辅导员对每个"学生-题目模板"是否已答对，实现"做对即剔除"
    """

    class Meta:
        app_label = 'practice'
        verbose_name = '练习进度'
        verbose_name_plural = '练习进度'
        db_table = 'practice_progresses'
        unique_together = [['user', 'student', 'template']]

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='进度ID',
    )

    # 辅导员
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='辅导员',
    )

    # 学生
    student = models.ForeignKey(
        'system.Student',
        on_delete=models.CASCADE,
        verbose_name='学生',
    )

    # 题目模板
    template = models.ForeignKey(
        'system.QuestionTemplate',
        on_delete=models.CASCADE,
        verbose_name='题目模板',
    )

    # 是否已答对
    is_passed = models.BooleanField(
        default=False,
        verbose_name='是否已答对',
    )

    # 最后更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='最后更新时间',
    )

    def __str__(self):
        return f"用户{self.user_id} - 学生{self.student_id} - 模板{self.template_id}"


class PracticeFavorite(models.Model):
    """
    收藏夹表（对应数据库 practice_favorites 表）
    收藏时快照保存原题数据（题干、选项、正确答案），实现收藏后反复练习
    """

    class Meta:
        app_label = 'practice'
        verbose_name = '收藏夹'
        verbose_name_plural = '收藏夹'
        db_table = 'practice_favorites'
        unique_together = [['user', 'student', 'template']]
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='收藏ID',
    )

    # 辅导员
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='辅导员',
    )

    # 学生
    student = models.ForeignKey(
        'system.Student',
        on_delete=models.CASCADE,
        verbose_name='学生',
    )

    # 题目模板（关联原模板，仅用于追溯和 unique_together 约束）
    template = models.ForeignKey(
        'system.QuestionTemplate',
        on_delete=models.CASCADE,
        verbose_name='题目模板',
    )

    # 收藏时快照 —— 题干（已替换学生姓名后的完整文案）
    question_title = models.CharField(
        max_length=500,
        default='',
        blank=True,
        verbose_name='题目题干',
    )

    # 收藏时快照 —— 题型
    question_type = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name='题型',
    )

    # 收藏时快照 —— 选项（JSON 格式存储，如 {"A":"...","B":"..."}）
    options = models.JSONField(
        null=True,
        blank=True,
        verbose_name='选项',
    )

    # 收藏时快照 —— 正确答案（客观题有值，essay 为空）
    correct_answer = models.CharField(
        max_length=500,
        default='',
        blank=True,
        verbose_name='正确答案',
    )

    # 收藏时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='收藏时间',
    )

    def __str__(self):
        return f"用户{self.user_id} - 收藏{self.id}"
