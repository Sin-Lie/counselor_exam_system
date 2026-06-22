# -*- coding: utf-8 -*-
# 简答题批改模块 - 数据库模型
# 本模块的数据表由 exam 和 system 模块提供，此处新增 AI 批改相关表
# 主要依赖的表：
#   - exam_answer (ExamAnswer)：作答详情表（来自 exam 模块）
#   - exam_question (ExamQuestion)：考试题目表（来自 exam 模块）
#   - exam_paper (ExamPaper)：学生考试记录表（来自 exam 模块）
#   - system_log (SystemLog)：系统操作日志表（来自 system 模块）
#   - question_template (QuestionTemplate)：题目模板表（来自 system 模块）
#   - users (User)：用户表（Django 内置 User 模型）
# 新增表：
#   - ai_grade_config (AIGradeConfig)：AI 批改全局配置表
#   - ai_grade_log (AIGradeLog)：AI 批改日志表

from django.db import models


class AIGradeConfig(models.Model):
    """
    AI 批改全局配置表（对应数据库 ai_grade_config 表）
    系统只维护一条记录，通过 GET/PUT 接口管理
    """

    class Meta:
        app_label = 'correct'
        verbose_name = 'AI 批改配置'
        verbose_name_plural = 'AI 批改配置'
        db_table = 'ai_grade_config'

    # 供应商名称（如 OpenAI、DeepSeek、千问）
    provider_name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='供应商名称',
    )

    # API 端点地址
    api_url = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='API 地址',
    )

    # API 密钥
    api_key = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='API 密钥',
    )

    # 模型名称（如 gpt-4o、deepseek-chat）
    model_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='模型名称',
    )

    # 温度参数，默认 0.1 保证评分一致性
    temperature = models.FloatField(
        default=0.1,
        verbose_name='温度参数',
    )

    # 最大输出 token
    max_tokens = models.IntegerField(
        default=2000,
        verbose_name='最大输出 Token',
    )

    # 自定义系统提示词
    system_prompt = models.TextField(
        blank=True,
        default='',
        verbose_name='系统提示词',
    )

    # 全局启用开关（关闭后所有考试都不生效）
    is_active = models.BooleanField(
        default=False,
        verbose_name='全局启用',
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
    )

    # 最后更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
    )

    def __str__(self):
        return f"AI批改配置 - {self.provider_name or '未配置'}"


class AIGradeLog(models.Model):
    """
    AI 批改日志表（对应数据库 ai_grade_log 表）
    记录每次 AI 批改的请求/响应详情，用于追踪和排错
    """

    class Meta:
        app_label = 'correct'
        verbose_name = 'AI 批改日志'
        verbose_name_plural = 'AI 批改日志'
        db_table = 'ai_grade_log'

    # 关联答案ID
    answer = models.ForeignKey(
        'exam.ExamAnswer',
        on_delete=models.CASCADE,
        verbose_name='答案',
    )

    # 使用的模型名称
    model_name = models.CharField(
        max_length=100,
        verbose_name='模型名称',
    )

    # 发送给大模型的完整 prompt
    prompt_sent = models.TextField(
        verbose_name='发送的 Prompt',
    )

    # 大模型原始返回
    response_raw = models.TextField(
        blank=True,
        default='',
        verbose_name='原始返回',
    )

    # AI 返回的分数
    score_returned = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='AI 返回分数',
    )

    # AI 返回的评语
    remark_returned = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='AI 返回评语',
    )

    # 耗时（毫秒）
    latency_ms = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='耗时(ms)',
    )

    # 状态：success=成功, failed=失败
    status = models.CharField(
        max_length=20,
        choices=[('success', '成功'), ('failed', '失败')],
        verbose_name='状态',
    )

    # 失败原因
    error_msg = models.TextField(
        blank=True,
        default='',
        verbose_name='错误信息',
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
    )

    def __str__(self):
        return f"AI批改日志-{self.id} - {'成功' if self.status == 'success' else '失败'}"
