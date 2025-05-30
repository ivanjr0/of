#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Django with regular settings (not worker_settings)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

try:
    import django

    django.setup()
    logger.info("Django setup completed successfully")
except Exception as e:
    logger.error(f"Failed to setup Django: {e}")
    sys.exit(1)

# Import after Django setup
try:
    from redis import Redis
    from rq import Worker, Queue

    logger.info("Successfully imported Redis and RQ")
except ImportError as e:
    logger.error(f"Failed to import required packages: {e}")
    sys.exit(1)

# Get Redis connection from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_conn = Redis.from_url(redis_url)
    redis_conn.ping()  # Test the connection
    logger.info(f"Successfully connected to Redis at {redis_url}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Create worker without the deprecated Connection context manager
        worker = Worker(["default", "high", "low"], connection=redis_conn)
        logger.info("Starting RQ worker...")
        logger.info(f"Connected to Redis at: {redis_url}")
        logger.info("Listening on queues: default, high, low")
        worker.work()
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)
