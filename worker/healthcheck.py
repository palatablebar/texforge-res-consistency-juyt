"""worker 健康检查：/tmp/worker-heartbeat 在 60 秒内更新过即视为存活。"""
import os
import sys
import time

HEARTBEAT = "/tmp/worker-heartbeat"
MAX_AGE = 60

path = HEARTBEAT
if not os.path.exists(path):
    print(f"heartbeat missing: {path}")
    sys.exit(1)
age = time.time() - os.path.getmtime(path)
if age > MAX_AGE:
    print(f"heartbeat stale: {age:.1f}s > {MAX_AGE}s")
    sys.exit(1)
print(f"heartbeat ok: age={age:.1f}s")
sys.exit(0)
