import time
from collections import deque
from threading import Lock
from typing import Deque

class RateLimiter:
    """Thread-safe rate limiter using sliding window"""
    
    def __init__(self, max_requests: int, time_window: int):
        """Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self._max_requests = max_requests
        self._time_window = time_window
        self._requests: Deque[float] = deque()
        self._lock = Lock()
        
    def allow_request(self) -> bool:
        """Check if request is allowed under current rate limit
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            while self._requests and self._requests[0] <= now - self._time_window:
                self._requests.popleft()
            
            # Check if we're at the limit
            if len(self._requests) >= self._max_requests:
                return False
            
            # Add new request
            self._requests.append(now)
            return True
            
    def reset(self) -> None:
        """Reset rate limiter state"""
        with self._lock:
            self._requests.clear()
            
    @property
    def current_usage(self) -> int:
        """Get current number of requests in window"""
        with self._lock:
            now = time.time()
            # Remove old requests first
            while self._requests and self._requests[0] <= now - self._time_window:
                self._requests.popleft()
            return len(self._requests)
