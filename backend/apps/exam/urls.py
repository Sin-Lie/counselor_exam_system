# -*- coding: utf-8 -*-
# 考试模块 - 路由配置
# 前缀已在 config/urls.py 中配置为 /api/exam/

from django.urls import path
from . import views
from apps.system.views import ExamUserStatusView

urlpatterns = [
    # 4.1 获取考试列表
    path('list/', views.ExamListView.as_view(), name='exam_list'),

    # 4.2 获取考试详情
    path('info/<int:exam_id>/', views.ExamInfoView.as_view(), name='exam_info'),

    # 4.3 进入考试（支持断线恢复）
    path('enter/<int:exam_id>/', views.EnterExamView.as_view(), name='exam_enter'),

    # 4.4 获取已保存答案（断线快速恢复）
    path('saved-answers/<int:paper_id>/', views.SavedAnswersView.as_view(), name='saved_answers'),

    # 4.5 实时保存答案
    path('save/', views.SaveAnswerView.as_view(), name='exam_save'),

    # 4.6 交卷
    path('submit/<int:paper_id>/', views.SubmitExamView.as_view(), name='exam_submit'),

    # 4.7 考试异常日志上报（含强制交卷判断）
    path('report-abnormal/', views.ReportAbnormalView.as_view(), name='report_abnormal'),

    # 7.6.5 考生状态列表（超管查看，视图实现位于 system 模块）
    path('user-status/<int:exam_id>/', ExamUserStatusView.as_view(), name='exam_user_status'),

    # 🆕 超管试卷检查（试卷生成后、开考前，人工校验所有考生试卷是否正确）
    path('paper-review/<int:paper_id>/', views.PaperReviewView.as_view(), name='paper_review'),

    # 🆕 预加载试卷图片（考前10分钟入场时调用，base64编码返回所有选项图片供前端缓存）
    path('preload-images/<int:paper_id>/', views.PreloadImagesView.as_view(), name='preload_images'),

    # 🆕 导出考试学生信息
    path('export-students/<int:exam_id>/', views.ExportStudentsView.as_view(), name='export_students'),
]
