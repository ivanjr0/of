#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django

django.setup()

from rq import Queue
from redis import Redis

# Get Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)

# Get the queue
q = Queue(connection=redis_conn)

# Check failed jobs
failed_registry = q.failed_job_registry
print(f"Failed jobs: {failed_registry.count}")

# List failed jobs
for job_id in failed_registry.get_job_ids():
    job = q.fetch_job(job_id)
    if job:
        print(f"\nJob ID: {job_id}")
        print(f"Function: {job.func_name}")
        print(f"Args: {job.args}")
        print(f"Error: {job.exc_info}")
        print("-" * 50)
