# 设置模块初始化文件
# 用于根据环境导入对应的配置
import os
from .base import *

# 根据环境变量决定使用哪个配置
env = os.environ.get('DJANGO_ENV', 'dev')

if env == 'prod':
    from .prod import *
else:
    from .dev import *
