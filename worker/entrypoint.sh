#!/usr/bin/env bash
# Celery worker + 心跳文件写盘（供 compose healthcheck 检测存活）
set -u
mkdir -p /data/artifacts /data/previews
echo "worker starting (broker=${REDIS_URL:-unset})"

celery -A app.config.celery_app worker --loglevel=info --concurrency=1 &
CELERY_PID=$!
echo "celery pid=$CELERY_PID"

while true; do
  date +%s > /tmp/worker-heartbeat
  if ! kill -0 "$CELERY_PID" 2>/dev/null; then
    echo "celery exited, restarting in 3s"
    sleep 3
    celery -A app.config.celery_app worker --loglevel=info --concurrency=1 &
    CELERY_PID=$!
  fi
  sleep 10
done
