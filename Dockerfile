# 使用 Python 3.12.6 基礎映像
FROM python:3.12.6

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt 到容器中
COPY requirements.txt .

# 安裝必要的 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 複製應用程式的其他檔案
COPY . .

# 設置容器啟動時執行的命令
CMD ["python", "server.py"]