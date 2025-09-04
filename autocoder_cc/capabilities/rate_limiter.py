#!/usr/bin/env python3
"""Rate Limiter Capability - FAIL-FAST implementation with real functionality"""

import time
import asyncio
from collections import deque
from typing import Optional
from autocoder_cc.observability.structured_logging import get_logger

class RateLimiter:
    """Token bucket rate limiter for throughput control"""
    
    def __init__(self, max_requests=100, time_window=60, burst_size=None, **kwargs):
        # FAIL-FAST: Validate configuration
        if max_requests <= 0:
            raise ValueError("max_requests must be positive (fail-fast principle)")
        if time_window <= 0:
            raise ValueError("time_window must be positive (fail-fast principle)")
            
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self.logger = get_logger("RateLimiter")
        
        # Token bucket implementation
        self.tokens = self.burst_size
        self.last_refill = time.time()
        self.refill_rate = max_requests / time_window  # tokens per second
        
        # Request tracking
        self.request_times = deque()
        self.total_requests = 0
        self.total_throttled = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens_needed: int = 1) -> None:
        """Acquire tokens - FAIL-FAST if rate limit exceeded"""
        if tokens_needed <= 0:
            raise ValueError("tokens_needed must be positive (fail-fast principle)")
            
        async with self._lock:
            self.total_requests += 1
            current_time = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = current_time - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_refill = current_time
            
            # Clean old request times
            cutoff_time = current_time - self.time_window
            while self.request_times and self.request_times[0] < cutoff_time:
                self.request_times.popleft()
            
            # Check if we have enough tokens
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                self.request_times.append(current_time)
                self.logger.debug(f"Acquired {tokens_needed} tokens, {self.tokens:.1f} remaining")
            else:
                # FAIL-FAST: Rate limit exceeded
                self.total_throttled += 1
                current_rate = len(self.request_times) / self.time_window
                self.logger.warning(f"Rate limit exceeded: {current_rate:.1f} req/s > {self.refill_rate:.1f} req/s")
                raise RuntimeError(f"Rate limit exceeded: {current_rate:.1f} requests/second exceeds limit of {self.refill_rate:.1f} requests/second")
    
    def release(self) -> None:
        """Release method for compatibility - tokens auto-refill"""
        pass  # Token bucket automatically refills
    
    def get_status(self) -> dict:
        """Get rate limiter status"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        # Count recent requests
        recent_requests = sum(1 for req_time in self.request_times if req_time >= cutoff_time)
        current_rate = recent_requests / self.time_window
        
        return {
            "current_rate": current_rate,
            "max_rate": self.refill_rate,
            "available_tokens": self.tokens,
            "burst_capacity": self.burst_size,
            "total_requests": self.total_requests,
            "total_throttled": self.total_throttled,
            "throttle_rate": self.total_throttled / max(self.total_requests, 1)
        }
