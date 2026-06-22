# -*- coding: utf-8 -*-
# 成绩与统计模块 - URL路由配置

from django.urls import path
from . import views

urlpatterns = [
    # 6.1 我的成绩
    path('my/<int:exam_id>/', views.MyScoreView.as_view(), name='my_score'),

    # 6.2 我的考试试卷详情
    path('my-paper/<int:paper_id>/', views.MyPaperDetailView.as_view(), name='my_paper_detail'),

    # 6.3 查看任意考生试卷详情（支持 paper_id 路径 或 exam_id+user_id 查询参数）
    path('paper-detail/<int:paper_id>/', views.PaperDetailView.as_view(), name='paper_detail'),
    path('paper-detail/', views.PaperDetailView.as_view(), name='paper_detail_query'),

    # 6.4 考试整体统计
    path('statistics/<int:exam_id>/', views.ExamStatisticsView.as_view(), name='exam_statistics'),

    # 6.5 未参考人员清单
    path('unattended/<int:exam_id>/', views.UnattendedListView.as_view(), name='unattended_list'),

    # 6.6 导出成绩Excel
    path('export/<int:exam_id>/', views.ExportScoresView.as_view(), name='export_scores'),
]
