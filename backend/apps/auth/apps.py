# 认证权限模块应用配置

from django.apps import AppConfig

# 认证权限模块应用配置
class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField' # 默认主键字段类型为BigAutoField
    name = 'apps.auth'  # 应用名称
    label = 'accounts'  # 应用标签
    verbose_name = '认证权限模块'  # 应用显示名称

    # 模块启动时执行的操作
    def ready(self):
        pass
