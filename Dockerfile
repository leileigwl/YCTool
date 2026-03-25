# 义乌耀灿太阳能报价系统
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 - 中文字体和PDF依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 创建上传目录
RUN mkdir -p static/uploads

# 设置环境变量
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5002

# 启动命令 - 生产环境使用 gunicorn
CMD ["python", "app.py"]