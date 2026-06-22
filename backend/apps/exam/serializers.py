# -*- coding: utf-8 -*-
# 考试模块 - 序列化器
# 负责参数校验和返回格式控制

from rest_framework import serializers


class ExamItemSerializer(serializers.Serializer):
    """
    考试列表单项序列化器（输出用）
    返回字段：exam_id、exam_name、exam_status
    """
    exam_id = serializers.IntegerField()
    exam_name = serializers.CharField()
    exam_status = serializers.CharField()
    paper_id = serializers.IntegerField(allow_null=True, required=False)


class ExamInfoSerializer(serializers.Serializer):
    """
    考试详情序列化器（输出用）
    返回字段：exam_name、duration、start_time、end_time、exam_status、remaining_time、paper_id
    """
    exam_name = serializers.CharField()
    duration = serializers.IntegerField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    exam_status = serializers.CharField()
    remaining_time = serializers.IntegerField()
    paper_id = serializers.IntegerField(allow_null=True, required=False)


class QuestionSerializer(serializers.Serializer):
    """
    试卷题目序列化器（输出用）
    question_id 对应 ExamPaper.paper_id
    options 为字典格式（如 {"A":"选项A","B":"选项B"}）
    user_answer 为考生已保存的答案，null 表示未作答
    score 为本小题分值
    """
    question_id = serializers.IntegerField()
    title = serializers.CharField()
    question_type = serializers.CharField()
    score = serializers.IntegerField()
    options = serializers.DictField(required=False)
    user_answer = serializers.CharField(allow_null=True, required=False)


class SavedAnswersSerializer(serializers.Serializer):
    """
    已保存答案序列化器（输出用）
    answers 为 key-value 映射：{question_id: user_answer}
    """
    answers = serializers.DictField(child=serializers.CharField())


class ExamAnswerItemSerializer(serializers.Serializer):
    """考试单题答案条目"""
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(allow_blank=True, required=False, default='')


class SaveAnswerSerializer(serializers.Serializer):
    """
    保存答案请求序列化器（兼容单题/批量两种模式）
    POST /api/exam/save/
    单题模式: paper_id + question_id + user_answer + save_time（兼容旧版）
    批量模式: paper_id + answers[question_id, user_answer] + save_time
    paper_id：考试记录ID（UserExam.record_id）
    save_time：毫秒时间戳
    reconnect：是否断线重连标记（可选）
    """
    paper_id = serializers.IntegerField()
    save_time = serializers.IntegerField()
    reconnect = serializers.BooleanField(required=False, default=False)
    # 批量模式（优先）
    answers = ExamAnswerItemSerializer(many=True, required=False)
    # 单题模式（兼容旧版，answers 为空时使用）
    question_id = serializers.IntegerField(required=False)
    user_answer = serializers.CharField(allow_blank=True, required=False, default='')

    def validate(self, attrs):
        """校验：answers 和 question_id 至少存在一个"""
        if not attrs.get('answers') and attrs.get('question_id') is None:
            raise serializers.ValidationError('请提供 answers 数组（批量模式）或 question_id（单题模式）')
        return attrs


class ReportAbnormalSerializer(serializers.Serializer):
    """
    异常上报请求序列化器（输入校验）
    POST /api/exam/report-abnormal/
    paper_id：考试记录ID（UserExam.record_id）
    type：异常类型枚举（screen_out / timeout / abnormal_operation）
    duration：切出或异常持续时长（秒）
    screen_out_count：前端累计切屏次数（仅作参考）
    """
    paper_id = serializers.IntegerField()
    exam_id = serializers.IntegerField()
    type = serializers.ChoiceField(
        choices=['screen_out', 'timeout', 'abnormal_operation']
    )
    duration = serializers.IntegerField(min_value=0)
    screen_out_count = serializers.IntegerField(min_value=0)
