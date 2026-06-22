# 生产环境配置
# 完全支持 Docker 环境变量覆盖

from .base import *

# 调试模式关闭
DEBUG = False

# 生产环境允许的域名（从环境变量读取，多个域名用逗号分隔）
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# 生产环境数据库配置（全部从环境变量读取）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'counselor_exam_system'),
        'USER': os.environ.get('DB_USER', os.environ.get('MYSQL_USER', 'root')),
        'PASSWORD': os.environ.get('DB_PASSWORD', os.environ.get('mysql_pwd', '')),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Redis配置（使用 base.py 中的环境变量读取机制，覆盖默认值即可）
# 这些值已在 base.py 中从环境变量读取，无需重复

# 生产环境必须从环境变量读取安全密钥
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("DJANGO_SECRET_KEY 环境变量必须设置")
JWT_SECRET_KEY = SECRET_KEY

# SSL/HTTPS 设置（通过环境变量控制，默认关闭方便首次部署）
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'False') == 'True'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_HSTS_INCLUDE_SUBDOMAINS', 'False') == 'True'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_HSTS_PRELOAD', 'False') == 'True'

# 生产环境日志级别
LOGGING['loggers']['django']['level'] = 'INFO'


# 学生照片存储路径（数据库中 photo_url 只存文件名，显示时拼接此路径）
STUDENT_PHOTO_DIR = '/opt/photo'