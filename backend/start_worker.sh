#!/bin/bash
set -e

echo "Setting up Django for worker..."
export DJANGO_SETTINGS_MODULE=settings
export PYTHONPATH=/app

echo "Installing dependencies..."
uv pip install -e .

echo "Checking Redis connection..."
python -c "
import redis
import sys
try:
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
"

echo "Starting RQ worker..."
exec uv run python worker.py 