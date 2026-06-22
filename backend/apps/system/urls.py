# -*- coding: utf-8 -*-
# 系统模块路由配置

from django.urls import path
from . import views

urlpatterns = [
    # 7.1 导入辅导员
    path('import/users/', views.ImportUsersView.as_view(), name='import_users'),
    # 7.2 导入学生信息
    path('import/students/', views.ImportStudentsView.as_view(), name='import_students'),
    # 7.3.1 用户列表
    path('user/list/', views.UserListView.as_view(), name='user_list'),
    # 7.3.2 启用/禁用用户
    path('user/set-status/', views.SetUserStatusView.as_view(), name='user_set_status'),
    # 7.3.3 重置用户密码
    path('user/reset-password/', views.ResetPasswordView.as_view(), name='user_reset_password'),
    # 7.3.4 编辑用户信息
    path('user/edit/<int:user_id>/', views.EditUserView.as_view(), name='user_edit'),
    # 7.4 管理员账号创建
    path('admin/create/', views.CreateAdminView.as_view(), name='admin_create'),
    # 7.5.1 题库列表
    path('question/list/', views.QuestionListView.as_view(), name='question_list'),
    # 7.5.2 新增题目
    path('question/add/', views.AddQuestionView.as_view(), name='question_add'),
    # 7.5.3 编辑题目
    path('question/edit/<int:template_id>/', views.EditQuestionView.as_view(), name='question_edit'),
    # 7.5.4 删除题目
    path('question/del/<int:template_id>/', views.DeleteQuestionView.as_view(), name='question_del'),
    # 7.5.5 启用/禁用题目
    path('question/set-status/<int:template_id>/', views.SetQuestionStatusView.as_view(), name='question_set_status'),
    # 7.6.0 考试列表（管理员/超管）
    path('exam/list/', views.AdminExamListView.as_view(), name='exam_list'),
    # 7.6.1 创建考试
    path('exam/create/', views.CreateExamView.as_view(), name='exam_create'),
    # 7.6.1a 编辑考试
    path('exam/edit/<int:exam_id>/', views.EditExamView.as_view(), name='exam_edit'),
    # 7.6.1b 删除考试
    path('exam/del/<int:exam_id>/', views.DeleteExamView.as_view(), name='exam_delete'),
    # 7.6.2 考试发布/关闭
    path('exam/set-status/', views.SetExamStatusView.as_view(), name='exam_set_status'),
    # 7.6.3 考卷预览
    path('exam/preview/<int:exam_id>/', views.ExamPreviewView.as_view(), name='exam_preview'),
    # 7.6.4 考试异常记录
    path('exam/abnormal-list/', views.ExamAbnormalListView.as_view(), name='exam_abnormal_list'),
    # 7.7 系统日志查询
    path('log/list/', views.LogListView.as_view(), name='log_list'),
]
