chcp 65001 > nul


docker build -t counselor-backend:latest .\backend
docker build -t counselor-frontend:latest .\frontend
docker save counselor-backend:latest counselor-frontend:latest -o D:\离线部署\project-images.tar

