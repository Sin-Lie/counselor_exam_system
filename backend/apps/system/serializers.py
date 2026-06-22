# -*- coding: utf-8 -*-
# 系统管理模块 - 序列化器
# 负责参数校验和返回格式控制

from rest_framework import serializers


class UserListSerializer(serializers.Serializer):
    """请求：用户列表查询参数"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    role = serializers.IntegerField(required=False)
    keyword = serializers.CharField(required=False, allow_blank=True, default='')


class SetStatusSerializer(serializers.Serializer):
    """请求：启用/禁用用户"""
    user_id = serializers.IntegerField()
    status = serializers.IntegerField(min_value=0, max_value=1)


class ResetPasswordSerializer(serializers.Serializer):
    """请求：重置密码"""
    user_id = serializers.IntegerField()
    new_password = serializers.CharField(min_length=6, max_length=200)


class EditUserSerializer(serializers.Serializer):
    """请求：编辑用户信息"""
    name = serializers.CharField(required=False, allow_blank=True, max_length=50)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)


class CreateAdminSerializer(serializers.Serializer):
    """请求：创建管理员"""
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(min_length=6, max_length=200)
    name = serializers.CharField(max_length=50)
    role = serializers.IntegerField()


class QuestionAddSerializer(serializers.Serializer):
    """请求：新增题目"""
    title = serializers.CharField(max_length=500)
    type = serializers.ChoiceField(choices=['single', 'multi', 'judge', 'essay'])
    param_field = serializers.CharField(required=False, allow_blank=True, max_length=100)
    analysis = serializers.CharField(required=False, allow_blank=True, max_length=500)


class QuestionEditSerializer(serializers.Serializer):
    """请求：编辑题目（全部可选，允许部分更新）"""
    title = serializers.CharField(required=False, max_length=500)
    type = serializers.ChoiceField(required=False, choices=['single', 'multi', 'judge', 'essay'])
    param_field = serializers.CharField(required=False, allow_blank=True, max_length=100)
    analysis = serializers.CharField(required=False, allow_blank=True, max_length=500)


class QuestionItemSerializer(serializers.Serializer):
    """单个题型配置校验"""
    type = serializers.ChoiceField(choices=['single', 'multi', 'judge', 'essay'])
    count = serializers.IntegerField(min_value=1)
    score = serializers.IntegerField(min_value=1)


class CreateExamSerializer(serializers.Serializer):
    """请求：创建考试"""
    exam_name = serializers.CharField(max_length=100)
    release_time = serializers.DateField()
    exam_start = serializers.DateTimeField()
    exam_duration = serializers.IntegerField(min_value=1)
    questions = serializers.ListField(child=QuestionItemSerializer())
    # AI批改开关（7.6.6）
    ai_grade_enabled = serializers.BooleanField(required=False, default=False)
    # 出题模式（4.0）
    generate_mode = serializers.ChoiceField(
        required=False, default='by_type',
        choices=['by_type', 'by_student'],
    )
    # 按学生出题时的人数（4.0）
    student_count = serializers.IntegerField(
        required=False, default=0, min_value=0, max_value=50,
    )


class SetExamStatusSerializer(serializers.Serializer):
    """请求：考试发布/关闭"""
    exam_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['publish', 'close'])


class EditExamSerializer(serializers.Serializer):
    """请求：编辑考试（全部可选，允许部分更新）"""
    exam_name = serializers.CharField(required=False, max_length=100)
    release_time = serializers.DateField(required=False)
    exam_start = serializers.DateTimeField(required=False)
    exam_duration = serializers.IntegerField(required=False, min_value=1)
    questions = serializers.ListField(required=False, child=QuestionItemSerializer())
    # AI批改开关，编辑时可选（7.6.6）
    ai_grade_enabled = serializers.BooleanField(required=False)
    # 出题模式（4.0）
    generate_mode = serializers.ChoiceField(
        required=False, choices=['by_type', 'by_student'],
    )
    # 按学生出题时的人数（4.0）
    student_count = serializers.IntegerField(
        required=False, min_value=0, max_value=50,
    )


class ExamAbnormalListSerializer(serializers.Serializer):
    """请求：异常记录查询"""
    exam_id = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)


class ExamUserStatusSerializer(serializers.Serializer):
    """请求：考生状态列表查询（7.6.5）"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    status = serializers.IntegerField(required=False)
    keyword = serializers.CharField(required=False, allow_blank=True, default='')


class LogListSerializer(serializers.Serializer):
    """请求：日志查询"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    module = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.DateTimeField(required=False, input_formats=['%Y-%m-%d %H:%M:%S'])
    end_time = serializers.DateTimeField(required=False, input_formats=['%Y-%m-%d %H:%M:%S'])


class QuestionListSerializer(serializers.Serializer):
    """请求：题库列表查询"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    type = serializers.CharField(required=False, allow_blank=True)
    keyword = serializers.CharField(required=False, allow_blank=True, default='')


class ExamListSerializer(serializers.Serializer):
    """请求：管理员/超管考试列表查询"""
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
