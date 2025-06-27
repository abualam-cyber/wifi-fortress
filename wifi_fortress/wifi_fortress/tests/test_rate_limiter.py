import pytest
import time
from wifi_fortress.core.rate_limiter import RateLimiter

@pytest.fixture
def rate_limiter():
    return RateLimiter(max_requests=5, time_window=1)  # 5 requests per second for testing

def test_rate_limiter_init(rate_limiter):
    """Test rate limiter initialization"""
    assert rate_limiter._max_requests == 5
    assert rate_limiter._time_window == 1
    assert len(rate_limiter._requests) == 0

def test_rate_limiter_allow_request(rate_limiter):
    """Test request allowance"""
    # Should allow initial requests
    for _ in range(5):
        assert rate_limiter.allow_request()
    
    # Should block additional requests
    assert not rate_limiter.allow_request()

def test_rate_limiter_window_sliding(rate_limiter):
    """Test sliding window functionality"""
    # Fill up the limit
    for _ in range(5):
        assert rate_limiter.allow_request()
    
    # Wait for window to slide
    time.sleep(1.1)  # Slightly longer than window
    
    # Should allow new requests
    assert rate_limiter.allow_request()

def test_rate_limiter_reset(rate_limiter):
    """Test reset functionality"""
    # Fill up the limit
    for _ in range(5):
        rate_limiter.allow_request()
    
    # Reset
    rate_limiter.reset()
    assert len(rate_limiter._requests) == 0
    
    # Should allow new requests
    assert rate_limiter.allow_request()

def test_rate_limiter_current_usage(rate_limiter):
    """Test current usage tracking"""
    assert rate_limiter.current_usage == 0
    
    # Add some requests
    for i in range(3):
        rate_limiter.allow_request()
        assert rate_limiter.current_usage == i + 1
    
    # Wait for window to slide
    time.sleep(1.1)
    assert rate_limiter.current_usage == 0
