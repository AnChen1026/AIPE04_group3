# 1. 抓取官方 Python 3.12.10 環境（slim 版極度適合科學計算與微服務）
FROM python:3.12.10-slim

# 2. 安裝 Linux 底層必要的編譯工具（有些舊版 scipy/numpy 在安裝時會需要 gcc 編譯）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. 在容器內部開闢一間叫 /app 的虛擬辦公室，並把位置停在這裡
WORKDIR /app

# 4. 設定環境變數：讓 Python Log 能即時輸出，並防止產生 .pyc 垃圾快取
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 5. 先複製套件清單，並在容器內自動安裝（優化快取機制）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


