# -*- coding: utf-8 -*-
# 练习模块 - 序列化器

from rest_framework import serializers


class AnswerItemSerializer(serializers.Serializer):
    """单题答案条目"""
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(allow_blank=True, required=False, default='')


class SubmitAnswerSerializer(serializers.Serializer):
    """2.2 提交本题答案（兼容单题和批量两种模式）"""
    # 批量模式（优先）
    answers = AnswerItemSerializer(many=True, required=False)
    # 单题模式（兼容旧版，answers 为空时使用）
    session_id = serializers.CharField(max_length=100, required=False)
    question_id = serializers.IntegerField(required=False)
    user_answer = serializers.CharField(allow_blank=True, required=False, default='')

    def validate(self, attrs):
        """校验：answers 和 question_id 至少存在一个"""
        if not attrs.get('answers') and not attrs.get('question_id'):
            raise serializers.ValidationError('请提供 answers 数组（批量模式）或 question_id（单题模式）')
        if attrs.get('answers') and not attrs.get('session_id'):
            raise serializers.ValidationError('批量模式需要 session_id')
        return attrs


class ViewAnswerSerializer(serializers.Serializer):
    """2.3 查看本题答案"""
    session_id = serializers.CharField(max_length=100)
    question_id = serializers.IntegerField()


class NextGroupSerializer(serializers.Serializer):
    """2.4 下一组题目"""
    session_id = serializers.CharField(max_length=100)


class FavoriteAddSerializer(serializers.Serializer):
    """3.2 收藏题目"""
    session_id = serializers.CharField(max_length=100)
    question_id = serializers.IntegerField()


class FavoriteRemoveSerializer(serializers.Serializer):
    """3.3 取消收藏"""
    favorite_id = serializers.IntegerField()


class FavoriteListSerializer(serializers.Serializer):
    """3.1 收藏列表查询参数"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    sort_type = serializers.ChoiceField(required=False, default='time_desc',
                                         choices=['time_desc', 'name_asc'])
    keyword = serializers.CharField(required=False, allow_blank=True, default='')


class FavoriteReplaySerializer(serializers.Serializer):
    """3.5 收藏题目回放练习"""
    favorite_id = serializers.IntegerField()
    user_answer = serializers.CharField(allow_blank=True, required=False, default='')


class StartBatchSerializer(serializers.Serializer):
    """4.1 开始多人逐个练习"""
    count = serializers.IntegerField(
        required=False, default=10, min_value=1, max_value=50,
        help_text='练习人数，默认10人',
    )


class NextPersonSerializer(serializers.Serializer):
    """4.2 切换到下一个人"""
    session_id = serializers.CharField(max_length=100)


class BatchProgressSerializer(serializers.Serializer):
    """4.3 查询多人逐个练习进度"""
    session_id = serializers.CharField(max_length=100)
