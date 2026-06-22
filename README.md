<p align="center">
  <img src="https://img.shields.io/badge/Django-4.2-092E20?logo=django" alt="Django 4.2">
  <img src="https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js" alt="Vue 3.5">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql" alt="MySQL 8.0">
  <img src="https://img.shields.io/badge/Redis-7-FF4438?logo=redis" alt="Redis 7">
  <img src="https://img.shields.io/badge/DRF-3.15-red" alt="DRF 3.15">
  <img src="https://img.shields.io/badge/Element_Plus-2.x-409EFF?logo=element" alt="Element Plus">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker Compose">
</p>

<h1 align="center">辅导员考试系统（生情熟知）</h1>

<p align="center">
  高校辅导员业务考试一体化平台 · 在线考试 · AI 批改 · 智能防作弊
</p>

---

## 📋 项目介绍

**辅导员考试系统**（代号：生情熟知）是一套专为高校辅导员业务考核设计的全栈在线考试平台。系统覆盖考试全生命周期管理，支持从题库建设、试卷配置、在线答题、AI 智能批改到成绩发布与统计分析的全流程数字化。

系统采用 **三端角色体系**：

- **辅导员** — 在线考试、日常练习、成绩查询
- **批改员** — 主观题批改、成绩录入与发布
- **超级管理员** — 题库管理、试卷配置、考试监控、系统管理

### 核心功能

| 模块            | 功能                                    |
| ------------- | ------------------------------------- |
| 📝 **在线考试**   | 限时答题、自动计时、答案自动保存、客观题自动判分              |
| 🤖 **AI 批改**  | 接入大模型 API，智能批改主观题（简答/案例分析等）           |
| 🛡️ **防作弊引擎** | 强制全屏、切屏检测、DevTools 检测、快捷键拦截、右键/复制粘贴禁用 |
| 📚 **日常练习**   | 题库随机练习、试题收藏、自动批改反馈                    |
| 📊 **成绩管理**   | 成绩录入（Excel 导入/手动）、成绩发布、统计分析           |
| 👥 **学生管理**   | 学生信息批量导入（Excel）、照片管理、学籍状态管理           |
| 📈 **统计看板**   | 考试通过率、分数分布、各维度数据分析                    |
| 🧾 **操作日志**   | 关键操作全记录，审计追溯                          |

---

## 🛠️ 技术栈

### 前端

| 技术                                              | 版本  | 用途                                       |
| ----------------------------------------------- | --- | ---------------------------------------- |
| [Vue](https://vuejs.org/)                       | 3.5 | 前端框架（Composition API + `<script setup>`） |
| [Vite](https://vitejs.dev/)                     | 6.x | 构建工具（HMR 极速热更新）                          |
| [Element Plus](https://element-plus.org/)       | 2.x | UI 组件库                                   |
| [Pinia](https://pinia.vuejs.org/)               | 3.x | 状态管理                                     |
| [Vue Router](https://router.vuejs.org/)         | 4.x | 路由管理（懒加载 + 导航守卫）                         |
| [Axios](https://axios-http.com/)                | 1.x | HTTP 请求（拦截器封装、Token 注入）                  |
| [NProgress](https://ricostacruz.com/nprogress/) | 0.2 | 路由进度条                                    |

### 后端

| 技术                                                              | 版本   | 用途                               |
| --------------------------------------------------------------- | ---- | -------------------------------- |
| [Django](https://www.djangoproject.com/)                        | 4.2  | Web 框架                           |
| [Django REST Framework](https://www.django-rest-framework.org/) | 3.15 | RESTful API                      |
| [MySQL](https://www.mysql.com/)                                 | 8.0  | 关系数据库（utf8mb4 编码）                |
| [Redis](https://redis.io/)                                      | 7    | 缓存、考试计时、防作弊状态                    |
| [PyJWT](https://github.com/jpadilla/pyjwt/)                     | 2.x  | JWT 身份认证（Access + Refresh Token） |
| [Gunicorn](https://gunicorn.org/)                               | 21.x | 生产级 WSGI 服务器                     |
| [httpx](https://www.python-httpx.org/)                          | 0.28 | AI 批改调用大模型 API                   |
| [openpyxl](https://openpyxl.readthedocs.io/)                    | 3.x  | Excel 导入导出                       |
| [Pillow](https://python-pillow.org/)                            | 10.x | 图片处理（学生照片）                       |

### DevOps

| 技术                                                                              | 用途                                 |
| ------------------------------------------------------------------------------- | ---------------------------------- |
| [Docker](https://www.docker.com/) + [Compose](https://docs.docker.com/compose/) | 容器化部署（前后端 + MySQL + Redis + Nginx） |
| [Nginx](https://nginx.org/)                                                     | 反向代理 + 静态文件服务（前端构建产物）              |
| Supervisor（通过 Docker）                                                           | 进程守护（Gunicorn）                     |

---

## 🚀 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 20.19
- MySQL 8.0
- Redis 7.x
- Docker & Docker Compose（可选，用于生产部署）

### 本地开发

#### 1️⃣ 后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（参考 .env.prod.example）
# 确保 MySQL 和 Redis 已启动

# 数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

#### 2️⃣ 前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器（HMR 热更新）
npm run dev
```

前端默认运行在 `http://localhost:5173`，通过 Vite 代理 API 请求至后端 `http://localhost:8000`。

---

## 🐳 Docker 生产部署

### 1. 配置环境变量

复制示例环境变量文件并修改密码和密钥：

```bash
cp .env.prod.example .env.prod
```

关键配置项：

- `MYSQL_ROOT_PASSWORD` / `MYSQL_PASSWORD` — 数据库密码
- `REDIS_PASSWORD` — Redis 密码
- `DJANGO_SECRET_KEY` — Django 密钥（建议更换）

### 2. 一键部署

```bash
# 启动所有服务（后台运行）
docker-compose --env-file .env.prod up -d

# 初始化数据库（首次部署）
docker exec -it counselor_backend python manage.py migrate

# 收集静态文件
docker exec -it counselor_backend python manage.py collectstatic --noinput
```

### 3. 访问服务

部署完成后访问 `http://服务器IP` 即可进入系统。

### 服务架构

```
┌─────────┐     ┌──────────┐     ┌──────────┐
│ Browser │────▶│  Nginx   │────▶│ Backend  │
│  :80    │     │  :80     │     │  :8000   │
└─────────┘     │          │     └────┬─────┘
                │  (前端    │          │
                │   静态    │     ┌────▼─────┐
                │   文件)   │     │  MySQL    │
                └──────────┘     │  :3306    │
                                 └────┬─────┘
                                      │
                                 ┌────▼─────┐
                                 │  Redis   │
                                 │  :6379   │
                                 └──────────┘
```

---

## ✨ 技术亮点

### 1. 🛡️ 全链路防作弊引擎

系统内置了强大的前端防作弊模块 `AntiCheatEngine`，覆盖考试全过程：

- **强制全屏** — 进入考试自动切换全屏，拦截 ESC / F11 退出，退出即全屏重入
- **切屏检测** — 通过 `visibilitychange` + `blur` 双重检测，超过阈值自动强制交卷
- **DevTools 检测** — 使用 `debugger` 耗时差异法检测开发者工具开启
- **快捷键拦截** — 在捕获阶段拦截：ESC（退出全屏）、F1-F12、Win/Meta 键、Alt 组合键、Ctrl 组合键（含 Ctrl+Shift+I/J/C 等开发者工具快捷键）
- **内容安全** — 禁用右键菜单、复制、粘贴、剪切、拖拽，阻止页面关闭/刷新
- **反作弊上报** — 异常行为实时上报后端，存入考试异常记录表

```javascript
// 防作弊引擎核心 — 极简调用
const engine = new AntiCheatEngine({
  maxLeaveCount: 3,
  examStore: useExamStore(),
  onForceSubmit: () => handleSubmit(),
})
engine.start()
```

### 2. 🤖 AI 智能批改

主观题（简答题、案例分析题等）接入大模型 API 实现智能批改：

- **标准化 Prompt** — 构造结构化 prompt，包含题目要求、标准答案、学生作答
- **自适应评分** — AI 根据关键信息点完整性、表述准确性、逻辑清晰度综合评分
- **学生信息注入** — prompt 中嵌入学生背景信息（如籍贯、家庭所在地、学籍状态），辅助人工复核
- **兼容 OpenAI 协议** — 支持市面上所有兼容 OpenAI chat/completions 接口的大模型服务
- **人工复核兜底** — AI 批改完成后，批改员可逐题复审并修正分数

### 3. 🔐 JWT 双 Token 认证体系

自研 JWT 认证方案，支持 Access Token + Refresh Token：

- **Access Token** — 24 小时有效期，携带用户身份和角色信息
- **Refresh Token** — 2 天有效期，无感续期
- **角色路由守卫** — 前端路由级权限控制，后端接口级权限校验
- **明文密码兼容** — 根据需求文档支持明文密码校验（非哈希存储）

### 4. ⏱️ Redis 驱动的实时考试引擎

利用 Redis 特性保障考试可靠运行：

- **考试计时** — 基于 Redis 的集中式考试倒计时（不受前端时间篡改影响）
- **答案暂存** — 答题过程中答案实时写入 Redis，交卷时持久化
- **切屏计数** — 考试异常行为计数与阈值判定（前端计数 + 后端校验双保险）
- **状态管理** — 考试开始、提交、异常中断等状态转换管理

### 5. 📋 模块化 Django 应用架构

后端采用 DDD 领域驱动思想的模块化拆分：

```
backend/
├── apps/
│   ├── auth/       # 认证授权（用户、角色、JWT）
│   ├── exam/       # 考试核心（试卷、答题、计时）
│   ├── practice/   # 日常练习（随机出题、收藏）
│   ├── correct/    # AI批改 + 人工批改
│   ├── score/      # 成绩管理（录入、发布、统计）
│   └── system/     # 系统管理（学生、班级、学院）
├── config/         # Django 配置（base/dev/prod 分层）
└── utils/          # 通用工具（Excel、异常、响应封装）
```

**分层配置体系**：`base.py`（公共配置）→ `dev.py`（开发环境）→ `prod.py`（生产环境），环境变量驱动。

### 6. 🎨 Vue 3 Composition API + Element Plus

前端采用现代化 Vue 3 架构：

- **`<script setup>`** — 组合式 API 语法糖，代码更简洁
- **Pinia 状态管理** — `userStore`（用户/权限）、`examStore`（考试状态/答案/计时）
- **路由懒加载** — 页面组件异步加载，首屏优化
- **NProgress 进度条** — 路由切换可视化反馈
- **Element Plus 全套 UI** — 表格、表单、弹窗、消息提示等组件统一

---

## 📁 项目结构

```
├── backend/                    # Django 后端
│   ├── apps/
│   │   ├── auth/               # 认证模块
│   │   ├── exam/               # 考试模块
│   │   ├── practice/           # 练习模块
│   │   ├── correct/            # 批改模块（AI + 人工）
│   │   ├── score/              # 成绩模块
│   │   └── system/             # 系统管理模块
│   ├── config/                 # 配置文件
│   │   └── settings/           # 分层配置（base/dev/prod）
│   ├── utils/                  # 公共工具
│   ├── manage.py               # Django 管理脚本
│   └── requirements.txt        # Python 依赖
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # API 接口封装（axios）
│   │   ├── components/         # 公共组件
│   │   ├── layout/             # 布局组件
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── utils/              # 工具函数（防作弊引擎等）
│   │   └── views/              # 页面组件
│   │       ├── counselor/      # 辅导员端
│   │       ├── admin/          # 管理员端
│   │       └── super-admin/    # 超级管理员端
│   ├── vite.config.js          # Vite 构建配置
│   └── index.html              # 入口 HTML
│
├── docker-compose.yml          # Docker Compose 编排
├── .env.prod.example           # 生产环境变量模板
├── 构建镜像.bat                 # 镜像构建脚本（Windows）
└── 启动服务.bat                 # 服务启动脚本（Windows）
```

---

## 🔧 配置说明

### 环境变量（.env.prod）

| 变量                                     | 说明             |
| -------------------------------------- | -------------- |
| `DJANGO_SECRET_KEY`                    | Django 密钥      |
| `MYSQL_ROOT_PASSWORD`                  | MySQL root 密码  |
| `MYSQL_DATABASE`                       | 数据库名           |
| `DB_NAME/DB_USER/DB_PASSWORD`          | Django 连接数据库凭据 |
| `REDIS_HOST/REDIS_PORT/REDIS_PASSWORD` | Redis 连接配置     |

### 开发与生产配置分离

- `config/settings/base.py` — 公共配置（数据库、JWT、日志、中间件等）
- `config/settings/dev.py` — 开发配置（调试模式、SQLite 可选、CORS 宽松）
- `config/settings/prod.py` — 生产配置（调试关闭、安全头、日志级别调整）

---

## 📜 开源协议

本项目为内部系统，仅供学习参考。
