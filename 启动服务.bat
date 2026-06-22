@echo off
chcp 65001 > nul

:: 把当前工作目录切到【脚本自己所在目录】
cd /d "%~dp0"

echo 【启动Django后端】
start "Backend" cmd /k "cd backend && python manage.py runserver"

echo 【启动Vue/React前端】
start "fr" cmd /k "cd frontend && npm run dev"


