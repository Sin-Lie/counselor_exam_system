# WSGI配置 - 用于传统部署（如Gunicorn）

import os
from django.core.wsgi import get_wsgi_application

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 获取WSGI应用
application = get_wsgi_application()
