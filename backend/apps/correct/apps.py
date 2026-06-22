# 简答题批改模块应用配置

from django.apps import AppConfig


class CorrectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.correct'
    verbose_name = '简答题批改模块'
