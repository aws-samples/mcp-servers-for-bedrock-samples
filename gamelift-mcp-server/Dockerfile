# 基于官方Python 3.12镜像
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装uv（推荐的Python包管理工具）
RUN pip install --upgrade pip \
    && pip install uv

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装依赖
RUN uv pip install --system --no-cache-dir .

# 设置环境变量（可根据需要覆盖）
ENV AWS_ACCESS_KEY_ID=xxxxx \
    AWS_SECRET_ACCESS_KEY=xxxxxx \
    AWS_REGION=us-east-1

# 默认启动命令
CMD ["uv", "run", "src/gamelift_mcp_server.py"] 