# 考试核心模块应用配置

from django.apps import AppConfig


class ExamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.exam'
    verbose_name = '考试核心模块'
