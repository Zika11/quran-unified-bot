FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    PYTHONPATH=/app

WORKDIR /app

# مكتبات النظام المطلوبة (ffmpeg اختياري للفيديو)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir "python-telegram-bot[job-queue]==22.8" requests Pillow

COPY app ./app
COPY deploy ./deploy
COPY tools ./tools
COPY tests ./tests
COPY .env.example .

# تخزين دائم (اربطه بقرص/volume إن أمكن)
ENV DATA_DIR=/data \
    LOG_DIR=/data/logs \
    DB_PATH=/data/quran_unified.db
RUN mkdir -p /data/logs

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fsS http://127.0.0.1:8080/ || exit 1

CMD ["python", "-u", "deploy/start.py"]
