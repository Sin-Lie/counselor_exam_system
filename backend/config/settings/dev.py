# 开发环境配置
# 开发环境使用的配置

from .base import *

# 调试模式开启
DEBUG = True

# 开发环境安全密钥（仅用于本地开发，不可用于生产）
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-only-change-in-production')
JWT_SECRET_KEY = SECRET_KEY

# 开发环境允许所有hosts
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# 开发环境数据库配置（使用MySQL）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'counselor_exam_system',
        # 'NAME': 'test_sqsz',
        'USER': os.environ.get("mysql_user", "root"),
        'PASSWORD': os.environ.get("mysql_pwd","111305"), 
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Redis配置（开发环境）
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# 开发环境日志级别
LOGGING['loggers']['django']['level'] = 'DEBUG'

# CORS 配置（跨域资源共享）
# 允许所有域名访问（开发环境）
CORS_ALLOW_ALL_ORIGINS = True

# 允许的 HTTP 方法
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# 允许的 HTTP 头
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

STUDENT_PHOTO_DIR = r'C:\Users\Sin\Desktop\photo'