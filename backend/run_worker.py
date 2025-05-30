import os
import sys
import multiprocessing
from rq import Worker
from redis import Redis

# Load environment variables from .env file if it exists
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Set environment variable to prevent the fork() issue on macOS
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Set multiprocessing start method to 'spawn' for macOS compatibility
if sys.platform == "darwin":
    multiprocessing.set_start_method("spawn")

# Get the list of queues to listen to
listen = ["default"]

# Create a Redis connection using environment variable
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
print(f"Environment REDIS_URL: {os.getenv('REDIS_URL')}")
print(f"Using Redis URL: {redis_url}")

redis_conn = Redis.from_url(redis_url)


def run_worker():
    try:
        print(f"Starting worker with Redis URL: {redis_url}")
        # Test Redis connection first
        redis_conn.ping()
        print("Redis connection successful!")

        worker = Worker(listen, connection=redis_conn)
        worker.work()
    except Exception as e:
        print(f"Worker error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
