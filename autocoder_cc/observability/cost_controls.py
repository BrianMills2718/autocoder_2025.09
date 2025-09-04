#!/usr/bin/env python3
"""
Cost Control System - Circuit Breakers and Budget Management
Prevents runaway LLM costs through configurable limits and monitoring
"""

import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CostLimits:
    """Configurable cost limits for circuit breaker behavior"""
    max_cost_per_request: float = 0.20      # $0.20 per generation
    max_hourly_cost: float = 1.00           # $1.00 per hour  
    max_daily_cost: float = 10.00           # $10.00 per day
    max_monthly_cost: float = 100.00        # $100.00 per month
    
    # Provider-specific limits (optional overrides)
    provider_limits: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Warning thresholds (percentage of limit)
    warning_threshold: float = 0.8          # Warn at 80% of limit
    
    def get_provider_limit(self, provider: str, limit_type: str) -> float:
        """Get limit for specific provider, fall back to global limit"""
        if provider in self.provider_limits:
            return self.provider_limits[provider].get(limit_type, getattr(self, limit_type))
        return getattr(self, limit_type)

@dataclass 
class CostUsage:
    """Track cost usage over time periods"""
    total_cost: float = 0.0
    request_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    def add_cost(self, cost: float):
        """Add cost to usage tracking"""
        self.total_cost += cost
        self.request_count += 1
    
    def reset_if_expired(self, window_hours: int) -> bool:
        """Reset usage if time window expired"""
        if datetime.now() - self.last_reset > timedelta(hours=window_hours):
            self.total_cost = 0.0
            self.request_count = 0
            self.last_reset = datetime.now()
            return True
        return False

class CostCircuitBreaker:
    """Circuit breaker for cost control with configurable limits"""
    
    def __init__(self, limits: CostLimits, usage_file: Optional[str] = None):
        self.limits = limits
        self.usage_file = Path(usage_file) if usage_file else Path("cost_usage.json")
        
        # Time-based usage tracking
        self.hourly_usage = CostUsage()
        self.daily_usage = CostUsage()
        self.monthly_usage = CostUsage()
        
        # Circuit breaker state
        self.is_open = False
        self.last_failure = None
        self.consecutive_failures = 0
        
        # Load persistent usage data
        self._load_usage()
    
    def _load_usage(self):
        """Load usage data from persistent storage"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    
                # Restore usage data with proper datetime conversion
                for period_name, default_data in [('hourly', {}), ('daily', {}), ('monthly', {})]:
                    period_data = data.get(period_name, default_data).copy()
                    
                    # Convert ISO string back to datetime object
                    if 'last_reset' in period_data and isinstance(period_data['last_reset'], str):
                        try:
                            period_data['last_reset'] = datetime.fromisoformat(period_data['last_reset'])
                        except (ValueError, TypeError) as e:
                            # If conversion fails, use current time as fallback
                            period_data['last_reset'] = datetime.now()
                    
                    # Create usage object with converted datetime
                    setattr(self, f'{period_name}_usage', CostUsage(**period_data))
                
                # Reset expired windows (now safe with datetime objects)
                self.hourly_usage.reset_if_expired(1)
                self.daily_usage.reset_if_expired(24)
                self.monthly_usage.reset_if_expired(24 * 30)
                
        except Exception as e:
            logger.warning(f"Could not load cost usage data: {e}")
            # Start fresh if loading fails
    
    def _save_usage(self):
        """Save usage data to persistent storage"""
        try:
            data = {
                'hourly': {
                    'total_cost': self.hourly_usage.total_cost,
                    'request_count': self.hourly_usage.request_count,
                    'last_reset': self.hourly_usage.last_reset.isoformat()
                },
                'daily': {
                    'total_cost': self.daily_usage.total_cost,
                    'request_count': self.daily_usage.request_count,
                    'last_reset': self.daily_usage.last_reset.isoformat()
                },
                'monthly': {
                    'total_cost': self.monthly_usage.total_cost,
                    'request_count': self.monthly_usage.request_count,
                    'last_reset': self.monthly_usage.last_reset.isoformat()
                }
            }
            
            # Ensure directory exists
            self.usage_file.parent.mkdir(exist_ok=True)
            
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save cost usage data: {e}")
    
    def check_request_allowed(self, estimated_cost: float, provider: str = "default") -> Tuple[bool, str]:
        """
        Check if request is allowed based on cost limits
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Reset expired time windows
        self.hourly_usage.reset_if_expired(1)
        self.daily_usage.reset_if_expired(24) 
        self.monthly_usage.reset_if_expired(24 * 30)
        
        # Check per-request limit
        max_request_cost = self.limits.get_provider_limit(provider, 'max_cost_per_request')
        if estimated_cost > max_request_cost:
            return False, f"Request cost ${estimated_cost:.6f} exceeds limit ${max_request_cost:.6f}"
        
        # Check hourly limit
        max_hourly = self.limits.get_provider_limit(provider, 'max_hourly_cost')
        if self.hourly_usage.total_cost + estimated_cost > max_hourly:
            return False, f"Would exceed hourly limit: ${self.hourly_usage.total_cost + estimated_cost:.4f} > ${max_hourly:.4f}"
        
        # Check daily limit
        max_daily = self.limits.get_provider_limit(provider, 'max_daily_cost')
        if self.daily_usage.total_cost + estimated_cost > max_daily:
            return False, f"Would exceed daily limit: ${self.daily_usage.total_cost + estimated_cost:.4f} > ${max_daily:.4f}"
        
        # Check monthly limit
        max_monthly = self.limits.get_provider_limit(provider, 'max_monthly_cost')
        if self.monthly_usage.total_cost + estimated_cost > max_monthly:
            return False, f"Would exceed monthly limit: ${self.monthly_usage.total_cost + estimated_cost:.4f} > ${max_monthly:.4f}"
        
        # Check warning thresholds
        warning_threshold = self.limits.warning_threshold
        
        if self.daily_usage.total_cost + estimated_cost > max_daily * warning_threshold:
            logger.warning(f"Approaching daily cost limit: ${self.daily_usage.total_cost + estimated_cost:.4f} / ${max_daily:.4f}")
        
        if self.monthly_usage.total_cost + estimated_cost > max_monthly * warning_threshold:
            logger.warning(f"Approaching monthly cost limit: ${self.monthly_usage.total_cost + estimated_cost:.4f} / ${max_monthly:.4f}")
        
        return True, "Request allowed"
    
    def record_request(self, actual_cost: float, provider: str = "default"):
        """Record actual cost after successful request"""
        self.hourly_usage.add_cost(actual_cost)
        self.daily_usage.add_cost(actual_cost)
        self.monthly_usage.add_cost(actual_cost)
        
        # Reset circuit breaker on successful request
        self.consecutive_failures = 0
        self.is_open = False
        
        # Save updated usage
        self._save_usage()
        
        logger.info(f"Cost recorded: ${actual_cost:.6f} (Daily: ${self.daily_usage.total_cost:.4f}, Monthly: ${self.monthly_usage.total_cost:.4f})")
    
    def record_failure(self, reason: str):
        """Record failed request for circuit breaker logic"""
        self.consecutive_failures += 1
        self.last_failure = datetime.now()
        
        # Open circuit breaker after consecutive failures
        if self.consecutive_failures >= 3:
            self.is_open = True
            logger.error(f"Cost circuit breaker opened after {self.consecutive_failures} failures: {reason}")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        return {
            'hourly': {
                'cost': self.hourly_usage.total_cost,
                'requests': self.hourly_usage.request_count,
                'limit': self.limits.max_hourly_cost,
                'percentage': (self.hourly_usage.total_cost / self.limits.max_hourly_cost) * 100
            },
            'daily': {
                'cost': self.daily_usage.total_cost,
                'requests': self.daily_usage.request_count,
                'limit': self.limits.max_daily_cost,
                'percentage': (self.daily_usage.total_cost / self.limits.max_daily_cost) * 100
            },
            'monthly': {
                'cost': self.monthly_usage.total_cost,
                'requests': self.monthly_usage.request_count,
                'limit': self.limits.max_monthly_cost,
                'percentage': (self.monthly_usage.total_cost / self.limits.max_monthly_cost) * 100
            },
            'circuit_breaker': {
                'is_open': self.is_open,
                'consecutive_failures': self.consecutive_failures,
                'last_failure': self.last_failure.isoformat() if self.last_failure else None
            }
        }

# Default cost limits for different environments
DEFAULT_COST_LIMITS = {
    'development': CostLimits(
        max_cost_per_request=0.20,
        max_hourly_cost=5.00,
        max_daily_cost=20.00,
        max_monthly_cost=100.00
    ),
    'staging': CostLimits(
        max_cost_per_request=0.05,
        max_hourly_cost=5.00,
        max_daily_cost=25.00,
        max_monthly_cost=200.00
    ),
    'production': CostLimits(
        max_cost_per_request=0.10,
        max_hourly_cost=20.00,
        max_daily_cost=100.00,
        max_monthly_cost=1000.00
    )
}

def create_cost_circuit_breaker(environment: str = 'development', 
                               custom_limits: Optional[CostLimits] = None) -> CostCircuitBreaker:
    """Factory function to create cost circuit breaker with environment defaults"""
    if custom_limits:
        limits = custom_limits
    else:
        limits = DEFAULT_COST_LIMITS.get(environment, DEFAULT_COST_LIMITS['development'])
    
    usage_file = f"cost_usage_{environment}.json"
    return CostCircuitBreaker(limits, usage_file)