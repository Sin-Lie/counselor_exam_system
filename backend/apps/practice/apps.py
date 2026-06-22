# 练习刷题模块应用配置

from django.apps import AppConfig


class PracticeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.practice'
    verbose_name = '练习刷题模块'
