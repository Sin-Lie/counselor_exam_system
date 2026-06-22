# -*- coding: utf-8 -*-
# 练习模块路由配置

from django.urls import path
from . import views

urlpatterns = [
    # 2.1 开始练习
    path('start/', views.StartPracticeView.as_view(), name='practice_start'),
    # 2.2 提交本题答案
    path('submit/', views.SubmitAnswerView.as_view(), name='practice_submit'),
    # 2.3 查看本题答案
    path('answer/', views.ViewAnswerView.as_view(), name='practice_answer'),
    # 2.4 下一组题目
    path('next-group/', views.NextGroupView.as_view(), name='practice_next_group'),
    # 2.5 重置练习进度
    path('reset-progress/', views.ResetProgressView.as_view(), name='practice_reset'),
    # 2.6 练习结果统计
    path('result/', views.PracticeResultView.as_view(), name='practice_result'),
    # 4.1 开始多人逐个练习
    path('start-batch/', views.StartBatchPracticeView.as_view(), name='practice_start_batch'),
    # 4.2 切换到下一个人
    path('next-person/', views.NextPersonView.as_view(), name='practice_next_person'),
    # 4.3 查询多人逐个练习进度
    path('batch-progress/', views.BatchProgressView.as_view(), name='practice_batch_progress'),
]

# 收藏夹路由（独立前缀 /api/collection/）
collection_urlpatterns = [
    # 3.1 收藏列表
    path('list/', views.FavoriteListView.as_view(), name='favorite_list'),
    # 3.2 收藏题目
    path('add/', views.AddFavoriteView.as_view(), name='favorite_add'),
    # 3.3 取消收藏
    path('remove/', views.RemoveFavoriteView.as_view(), name='favorite_remove'),
    # 3.4 清空收藏
    path('clear/', views.ClearFavoritesView.as_view(), name='favorite_clear'),
    # 3.5 收藏题目回放练习
    path('replay/', views.FavoriteReplayView.as_view(), name='favorite_replay'),
]
