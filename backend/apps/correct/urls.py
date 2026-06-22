# -*- coding: utf-8 -*-
# 简答题批改模块 - URL路由配置

from django.urls import path
from . import views

urlpatterns = [
    # 5.1 待批改列表（支持分页）
    path('list/', views.CorrectListView.as_view(), name='correct_list'),

    # 5.2 提交/修改批改分数
    path('score/<int:answer_id>/', views.CorrectScoreView.as_view(), name='correct_score'),

    # 5.3 批改进度统计
    path('progress/', views.CorrectProgressView.as_view(), name='correct_progress'),

    # 5.4 批改日志查询
    path('log/list/', views.CorrectLogListView.as_view(), name='correct_log_list'),

    # 5.5 发布批改成绩
    path('publish/<int:exam_id>/', views.PublishScoresView.as_view(), name='correct_publish'),

    # 5.6 AI 批改配置
    path('ai-config/', views.AIGradeConfigView.as_view(), name='ai_grade_config'),

    # 5.7 AI 批改连接测试
    path('ai-config/test/', views.AIGradeTestView.as_view(), name='ai_grade_test'),

    # 5.8 AI 批改考试开关
    path('ai-grade/toggle/<int:exam_id>/', views.AIGradeToggleView.as_view(), name='ai_grade_toggle'),

    # 5.9 AI 批改日志
    path('ai-grade/logs/', views.AIGradeLogListView.as_view(), name='ai_grade_logs'),
]
