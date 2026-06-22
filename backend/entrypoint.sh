#!/bin/bash
# 辅导员考试系统 - 后端容器启动脚本
# 功能：等待数据库就绪 -> 执行迁移 -> 收集静态文件 -> 启动 Gunicorn

set -e

echo "===== 后端容器启动 ====="

# 等待 MySQL 就绪
echo "等待 MySQL 就绪..."
python << 'EOF'
import time, sys, os

try:
    import MySQLdb
except ImportError:
    print("MySQLdb 未安装，跳过数据库等待。")
    sys.exit(0)

host = os.environ.get('DB_HOST', 'localhost')
port = int(os.environ.get('DB_PORT', '3306'))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')

for i in range(30):
    try:
        conn = MySQLdb.connect(host=host, port=port, user=user, password=password)
        conn.close()
        print("MySQL 数据库就绪！")
        sys.exit(0)
    except Exception as e:
        print(f"等待 MySQL... ({i+1}/30) - {e}")
        time.sleep(2)

print("MySQL 连接超时，请检查数据库配置。")
sys.exit(1)
EOF

# 执行数据库迁移
echo "执行数据库迁移..."
python manage.py migrate --noinput

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 启动 Gunicorn
echo "启动 Gunicorn 服务器..."
exec "$@"
