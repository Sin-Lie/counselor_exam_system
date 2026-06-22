# -*- coding: utf-8 -*-
# 考试模块 - 数据库模型
# 对应数据库表：exams, exam_questions, exam_papers, exam_answers, cheat_logs

from django.conf import settings
from django.db import models


class ExamStatus(models.IntegerChoices):
    """考试状态枚举"""
    NOT_PUBLISHED = 0, '未发布'
    IN_PROGRESS = 1, '进行中'
    ENDED = 2, '已结束'
    CLOSED = 3, '已关闭'


class QuestionType(models.TextChoices):
    """题目类型枚举"""
    SINGLE = 'single', '单选题'
    MULTI = 'multi', '多选题'
    JUDGE = 'judge', '判断题'
    ESSAY = 'essay', '简答题'


class Exam(models.Model):
    """
    考试定义表（对应数据库 exams 表）
    状态流转：0(未发布) → 1(进行中) → 2(已结束)，3(已关闭) 需管理员手动操作
    """

    class Meta:
        app_label = 'exam'
        verbose_name = '考试'
        verbose_name_plural = '考试'
        db_table = 'exams'

    # 主键
    id = models.AutoField(
        primary_key=True,
        verbose_name='考试ID',
    )

    # 考试名称
    name = models.CharField(
        max_length=100,
        verbose_name='考试名称',
    )

    # 发布日期
    release_date = models.DateField(
        verbose_name='发布日期',
    )

    # 考试开始时间（UTC存储）
    start_time = models.DateTimeField(
        verbose_name='考试开始时间',
    )

    # 考试时长（分钟）
    duration_minutes = models.IntegerField(
        verbose_name='考试时长（分钟）',
    )

    # 考试状态
    status = models.SmallIntegerField(
        choices=ExamStatus.choices,
        default=ExamStatus.NOT_PUBLISHED,
        verbose_name='考试状态',
    )

    # 考试题型配置快照（JSON格式）
    question_config = models.JSONField(
        blank=True,
        null=True,
        verbose_name='考试题型配置快照',
    )

    # AI 自动批改开关（考试级别控制）
    ai_grade_enabled = models.BooleanField(
        default=False,
        verbose_name='AI 自动批改',
    )

    # 创建人
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='创建人',
    )

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ExamQuestion(models.Model):
    """
    考试题目明细表（对应数据库 exam_questions 表）
    考试创建时预生成，每条记录对应一个考生的一道题目
    """

    class Meta:
        app_label = 'exam'
        verbose_name = '考试题目'
        verbose_name_plural = '考试题目'
        db_table = 'exam_questions'
        indexes = [
            models.Index(fields=['exam', 'user']),
        ]

    # 主键（API 中对应 question_id）
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='题目ID',
    )

    # 所属考试
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        verbose_name='考试',
    )

    # 考生
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='考生',
    )

    # 题目模板
    template = models.ForeignKey(
        'system.QuestionTemplate',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='题目模板',
    )

    # 引用的学生
    student = models.ForeignKey(
        'system.Student',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='学生',
    )

    # 渲染后的题干
    question_text = models.CharField(
        max_length=2000,
        verbose_name='题干',
    )

    # 题型
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        verbose_name='题型',
    )

    # 选项内容（JSON格式）
    options = models.JSONField(
        blank=True,
        null=True,
        verbose_name='选项内容',
    )

    # 标准答案
    correct_answer = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='标准答案',
    )

    # 本小题分值
    score = models.IntegerField(
        default=0,
        verbose_name='分值',
    )

    # 题号顺序
    sort_order = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='题号顺序',
    )

    # 学生组内排序号（by_student 模式：学生1的题1-5, 学生2的题1-3...）
    student_sort_order = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='学生组内题号',
    )

    def __str__(self):
        return f"题目{self.id} - 序号{self.sort_order}"


class ExamPaper(models.Model):
    """
    考生试卷表（对应数据库 exam_papers 表）
    每位考生在一场考试中对应一条记录，API 中的 paper_id 即此表 id
    """

    class Meta:
        app_label = 'exam'
        verbose_name = '考生试卷'
        verbose_name_plural = '考生试卷'
        db_table = 'exam_papers'
        unique_together = [['exam', 'user']]

    class Status(models.IntegerChoices):
        NOT_STARTED = 0, '未开始'
        IN_PROGRESS = 1, '进行中'
        SUBMITTED = 2, '已交卷'
        ABNORMAL = 3, '异常交卷'

    # 主键（API 中对应 paper_id）
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='记录ID',
    )

    # 考试
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        verbose_name='考试',
    )

    # 考生
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='考生',
    )

    # 实际开始时间
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='开始时间',
    )

    # 交卷时间
    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='交卷时间',
    )

    # 考试状态
    status = models.SmallIntegerField(
        choices=Status.choices,
        default=Status.NOT_STARTED,
        verbose_name='考试状态',
    )

    # 客观题总分
    objective_score = models.IntegerField(
        default=0,
        verbose_name='客观题总分',
    )

    # 主观题总分
    subjective_score = models.IntegerField(
        default=0,
        verbose_name='主观题总分',
    )

    # 总成绩
    total_score = models.IntegerField(
        default=0,
        verbose_name='总成绩',
    )

    # 主观题是否全部批改完成
    is_graded = models.BooleanField(
        default=False,
        verbose_name='批改完成标记',
    )

    # 是否触发防作弊
    cheat_flag = models.BooleanField(
        default=False,
        verbose_name='防作弊标记',
    )

    # 分配的批改员（主观题批改分配，考试创建时随机均匀分配）
    assigned_grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_papers',
        verbose_name='批改员',
    )

    def __str__(self):
        return f"试卷{self.id} - 考生{self.user_id}"


class ExamAnswer(models.Model):
    """
    作答记录表（对应数据库 exam_answers 表）
    统一存储客观题和主观题答案
    """

    class Meta:
        app_label = 'exam'
        verbose_name = '作答记录'
        verbose_name_plural = '作答记录'
        db_table = 'exam_answers'
        indexes = [
            models.Index(fields=['question']),
        ]

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='答案ID',
    )

    # 关联题目
    question = models.ForeignKey(
        'ExamQuestion',
        on_delete=models.CASCADE,
        verbose_name='试卷题目',
    )

    # 考生提交答案
    content = models.CharField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name='考生答案',
    )

    # 是否正确（NULL=未判定）
    is_correct = models.BooleanField(
        blank=True,
        null=True,
        verbose_name='是否正确',
    )

    # 实得分数
    score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='实得分数',
    )

    # 批改人
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='批改人',
    )

    # 批改时间
    graded_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='批改时间',
    )

    # 批改备注
    remark = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='批改备注',
    )

    def __str__(self):
        return f"答案{self.id} - 题目{self.question_id}"


class CheatLog(models.Model):
    """
    防作弊日志表（对应数据库 cheat_logs 表）
    """

    class Meta:
        app_label = 'exam'
        verbose_name = '防作弊日志'
        verbose_name_plural = '防作弊日志'
        db_table = 'cheat_logs'

    # 主键
    id = models.BigAutoField(
        primary_key=True,
        verbose_name='日志ID',
    )

    # 考试
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='考试',
    )

    # 考生
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='考生',
    )

    # 异常类型
    action_type = models.CharField(
        max_length=50,
        verbose_name='异常类型',
    )

    # 发生时间
    occurred_at = models.DateTimeField(
        verbose_name='发生时间',
    )

    # 补充说明
    detail = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='补充说明',
    )

    def __str__(self):
        return f"作弊日志{self.id} - {self.user_id}"


class GradePublish(models.Model):
    """
    批改发布记录表（对应数据库 grade_publishes 表）
    记录各批改员在各场考试中的发布状态，用于控制成绩对考生可见性
    只有某场考试的所有批改员都发布后，辅导员才能查看成绩
    """
    class Meta:
        app_label = 'exam'
        verbose_name = '批改发布记录'
        verbose_name_plural = '批改发布记录'
        db_table = 'grade_publishes'
        unique_together = [['exam', 'grader']]

    # 主键（记录ID）
    id = models.BigAutoField(primary_key=True, verbose_name='记录ID')
    # 考试
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        verbose_name='考试',
    )
    # 批改员
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='批改员',
    )
    # 发布时间
    published_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='发布时间',
    )

    def __str__(self):
        return f"批改发布 - 考试{self.exam_id} 批改员{self.grader_id}"
