# -*- coding: utf-8 -*-
# 成绩与统计模块 - 序列化器
# 负责请求参数校验和返回数据格式定义

from rest_framework import serializers


class ExportScopeSerializer(serializers.Serializer):
    """
    导出成绩Excel查询参数序列化器
    接口：GET /api/score/export/{exam_id}/
    参数：export_scope（可选，all=全部，graded_only=仅已出成绩，默认all）
    """
    export_scope = serializers.ChoiceField(
        required=False,
        default='all',
        choices=['all', 'graded_only'],
    )
