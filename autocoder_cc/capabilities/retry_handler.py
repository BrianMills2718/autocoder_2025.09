#!/usr/bin/env python3
"""Retry Handler Capability - FAIL-FAST implementation with real functionality"""

import asyncio
import logging
from typing import Callable, Any, Optional
from autocoder_cc.observability.structured_logging import get_logger

class RetryHandler:
    """Handles retry logic for component operations with exponential backoff"""
    
    def __init__(self, max_retries=3, backoff_factor=2.0, base_delay=1.0, max_delay=60.0, **kwargs):
        # FAIL-FAST: Validate all parameters
        if max_retries <= 0:
            raise ValueError("max_retries must be positive (fail-fast principle)")
        if backoff_factor <= 0:
            raise ValueError("backoff_factor must be positive (fail-fast principle)")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive (fail-fast principle)")
        if max_delay <= 0:
            raise ValueError("max_delay must be positive (fail-fast principle)")
            
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = get_logger(f"RetryHandler")
        
        # Metrics
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
    
    async def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic - FAIL-FAST on exhausted retries"""
        if not callable(operation):
            raise ValueError("operation must be callable (fail-fast principle)")
            
        last_exception = None
        delay = self.base_delay
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            self.total_attempts += 1
            
            try:
                self.logger.debug(f"Executing operation (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                self.total_successes += 1
                if attempt > 0:
                    self.logger.info(f"Operation succeeded after {attempt + 1} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Operation failed on attempt {attempt + 1}: {e}")
                
                # Don't delay after the last attempt
                if attempt < self.max_retries:
                    self.logger.debug(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
        
        # FAIL-FAST: All retries exhausted
        self.total_failures += 1
        self.logger.error(f"Operation failed after {self.max_retries + 1} attempts")
        raise RuntimeError(f"Operation failed after {self.max_retries + 1} attempts. Last error: {last_exception}")
    
    def get_stats(self) -> dict:
        """Get retry statistics"""
        return {
            "total_attempts": self.total_attempts,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": self.total_successes / max(self.total_attempts, 1)
        }
