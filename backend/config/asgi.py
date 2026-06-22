# ASGI配置 - 用于异步部署（如Daphne、Uvicorn）

import os
from django.core.asgi import get_asgi_application

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 获取ASGI应用
application = get_asgi_application()

# 可以在这里添加WebSocket或其他异步协议的支持
