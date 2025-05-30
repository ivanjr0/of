"""
Queue Manager - Singleton pattern for Redis Queue management
"""
import os
from typing import Optional
from redis import Redis
from rq import Queue


class QueueManager:
    """Singleton class to manage Redis queue connections"""
    
    _instance: Optional['QueueManager'] = None
    _queue: Optional[Queue] = None
    _redis_conn: Optional[Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._queue is None:
            self._initialize_queue()
    
    def _initialize_queue(self):
        """Initialize Redis connection and queue"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis_conn = Redis.from_url(redis_url)
            self._queue = Queue(connection=self._redis_conn)
            print(f"Queue Manager initialized with Redis URL: {redis_url}")
        except Exception as e:
            print(f"Warning: Failed to initialize queue: {e}")
            print("Background job processing will be disabled")
            self._queue = None
            self._redis_conn = None
    
    @property
    def queue(self) -> Optional[Queue]:
        """Get the default queue"""
        return self._queue
    
    @property
    def redis_connection(self) -> Optional[Redis]:
        """Get the Redis connection"""
        return self._redis_conn
    
    def is_available(self) -> bool:
        """Check if queue is available for use"""
        return self._queue is not None
    
    def enqueue(self, func, *args, **kwargs):
        """Enqueue a job, with fallback if queue is not available"""
        if self.is_available():
            return self._queue.enqueue(func, *args, **kwargs)
        else:
            print(f"Warning: Queue not available, executing {func.__name__} synchronously")
            # Fallback: execute synchronously if queue is not available
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Error executing {func.__name__} synchronously: {e}")
                return None
    
    def get_queue_stats(self) -> dict:
        """Get queue statistics"""
        if not self.is_available():
            return {"status": "unavailable", "message": "Redis queue not initialized"}
        
        try:
            return {
                "status": "available",
                "pending_jobs": len(self._queue),
                "failed_jobs": len(self._queue.failed_job_registry),
                "redis_info": {
                    "connected": self._redis_conn.ping() if self._redis_conn else False
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global instance
queue_manager = QueueManager() 