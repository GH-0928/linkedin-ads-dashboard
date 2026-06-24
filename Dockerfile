# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Cloud Run 會帶 PORT 環境變數(預設 8080),Streamlit 要綁定它
ENV PORT=8080
EXPOSE 8080

# Streamlit Cloud Run 啟動參數:
# - server.port 用 $PORT
# - server.address 0.0.0.0 才能接外部連線
# - server.headless 不開瀏覽器
# - server.enableCORS false / enableXsrfProtection false 讓 Cloudflare 反代不擋
CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
