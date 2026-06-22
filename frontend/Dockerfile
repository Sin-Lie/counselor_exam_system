# 辅导员考试系统 - 前端 Dockerfile
# 多阶段构建：Stage 1 构建 Vue 项目，Stage 2 用 Nginx 运行

# ========== Stage 1: 构建 ==========
FROM node:20-alpine AS build

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码并构建
COPY . .

# 构建生产版本
RUN npm run build

# ========== Stage 2: 运行 ==========
FROM nginx:alpine

# 复制构建产物到 Nginx 静态文件目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
