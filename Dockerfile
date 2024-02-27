# 使用Python 3.10的alpine镜像作为基础镜像
FROM python:3.10.11-alpine

# 设置工作目录为/app
WORKDIR /app

# 设置时区为Asia/Shanghai
ENV TZ=Asia/Shanghai

# 将requirements.txt复制到工作目录
COPY requirements.txt requirements.txt

# 安装Python依赖，使用--no-cache-dir选项以避免缓存
RUN pip install --no-cache-dir -r requirements.txt

# 复制bot目录到工作目录下
COPY bot ./bot

# 创建日志目录
RUN mkdir ./log

# 创建数据库备份目录
RUN mkdir ./db_backup

# 将所有.py文件复制到工作目录下
COPY *.py ./

# 定义容器启动时执行的默认命令
ENTRYPOINT [ "python3" ]

# 设置默认的CMD为main.py，这样在容器启动时会自动执行main.py
CMD [ "main.py" ]
