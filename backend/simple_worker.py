#!/usr/bin/env python
import os
import sys
import time
from redis import Redis
from rq import Worker, Queue

# Get Redis URL from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

print(f"Starting Simple RQ Worker...")
print(f"Redis URL: {redis_url}")

# Connect to Redis
try:
    redis_conn = Redis.from_url(redis_url)
    redis_conn.ping()
    print("✓ Connected to Redis successfully")
except Exception as e:
    print(f"✗ Failed to connect to Redis: {e}")
    sys.exit(1)

# Start worker
worker = Worker(["default", "high", "low"], connection=redis_conn)
print("✓ Worker started, listening on queues: default, high, low")
print("Press Ctrl+C to stop")

try:
    worker.work()
except KeyboardInterrupt:
    print("\nShutting down worker...")
    sys.exit(0)
