# -*- coding: utf-8 -*-
# 简答题批改模块 - 序列化器
# 负责请求参数校验和返回数据格式定义

from rest_framework import serializers


class ScoreSubmitSerializer(serializers.Serializer):
    """
    提交/修改批改分数序列化器
    接口：PUT /api/correct/score/{answer_id}/
    校验 score 为必填数值，remark 可选
    """
    score = serializers.IntegerField(
        required=True,
        min_value=0,
        error_messages={
            'required': '请输入分数',
            'min_value': '分数不能为负数',
        }
    )
    remark = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=500,
        error_messages={
            'max_length': '备注不能超过500字',
        }
    )


class CorrectListSerializer(serializers.Serializer):
    """
    待批改列表查询参数序列化器
    接口：GET /api/correct/list/
    参数：exam_id（可选）、page、size
    """
    exam_id = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)


class CorrectProgressSerializer(serializers.Serializer):
    """
    批改进度查询参数序列化器
    接口：GET /api/correct/progress/
    参数：exam_id（可选）
    """
    exam_id = serializers.IntegerField(required=False)


class LogListSerializer(serializers.Serializer):
    """
    批改日志查询参数序列化器
    接口：GET /api/correct/log/list/
    参数：exam_id（可选）、grader_id（可选）、page、size
    """
    exam_id = serializers.IntegerField(required=False)
    grader_id = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)


class AIGradeConfigSerializer(serializers.Serializer):
    """
    AI 批改配置序列化器
    接口：PUT /api/correct/ai-config/
    """
    provider_name = serializers.CharField(required=False, allow_blank=True, default='', max_length=50)
    api_url = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)
    api_key = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)
    model_name = serializers.CharField(required=False, allow_blank=True, default='', max_length=100)
    temperature = serializers.FloatField(required=False, default=0.1, min_value=0.0, max_value=2.0)
    max_tokens = serializers.IntegerField(required=False, default=2000, min_value=100, max_value=10000)
    system_prompt = serializers.CharField(required=False, allow_blank=True, default='')
    is_active = serializers.BooleanField(required=False, default=False)


class AIGradeToggleSerializer(serializers.Serializer):
    """
    考试 AI 批改开关序列化器
    接口：PUT /api/correct/ai-grade/toggle/{exam_id}/
    """
    enabled = serializers.BooleanField(
        required=True,
        error_messages={'required': '请输入enabled参数'},
    )


class AIGradeTestSerializer(serializers.Serializer):
    """
    测试 AI 连接序列化器
    接口：POST /api/correct/ai-config/test/
    使用当前保存的配置发送测试请求，无需额外参数
    """
    pass


class AIGradeLogListSerializer(serializers.Serializer):
    """
    AI 批改日志查询参数序列化器
    接口：GET /api/correct/ai-grade/logs/
    """
    exam_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)  # success / failed
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
