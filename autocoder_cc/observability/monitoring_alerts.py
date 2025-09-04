#!/usr/bin/env python3
"""
Production Monitoring and Alerting System
Real-time monitoring with configurable alerts for LLM provider health and performance
"""

import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"  
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Alert delivery channels"""
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CONSOLE = "console"

@dataclass
class Alert:
    """Alert message with metadata"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "autocoder_cc"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata
        }

@dataclass
class MonitoringMetrics:
    """Metrics for monitoring provider performance"""
    # Provider health metrics
    provider_availability: Dict[str, bool] = field(default_factory=dict)
    provider_response_times: Dict[str, List[float]] = field(default_factory=lambda: {})
    provider_error_rates: Dict[str, float] = field(default_factory=dict)
    
    # Cost metrics
    hourly_cost: float = 0.0
    daily_cost: float = 0.0
    cost_trend: List[float] = field(default_factory=list)
    
    # Performance metrics
    generation_success_rate: float = 1.0
    avg_generation_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    
    # Rate limiting metrics
    rate_limit_hits: Dict[str, int] = field(default_factory=dict)
    
    def update_provider_health(self, provider: str, is_healthy: bool, response_time: float):
        """Update provider health metrics"""
        self.provider_availability[provider] = is_healthy
        
        if provider not in self.provider_response_times:
            self.provider_response_times[provider] = []
        
        self.provider_response_times[provider].append(response_time)
        
        # Keep only last 100 response times
        if len(self.provider_response_times[provider]) > 100:
            self.provider_response_times[provider] = self.provider_response_times[provider][-100:]
    
    def update_generation_metrics(self, success: bool, generation_time: float):
        """Update generation success and timing metrics"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1
        
        # Update success rate
        self.generation_success_rate = (self.total_requests - self.failed_requests) / self.total_requests
        
        # Update average generation time (running average)
        if self.avg_generation_time == 0:
            self.avg_generation_time = generation_time
        else:
            self.avg_generation_time = (self.avg_generation_time * 0.9) + (generation_time * 0.1)
    
    def record_rate_limit(self, provider: str):
        """Record rate limit hit for provider"""
        if provider not in self.rate_limit_hits:
            self.rate_limit_hits[provider] = 0
        self.rate_limit_hits[provider] += 1

class ProductionMonitor:
    """Production monitoring system with alerting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = MonitoringMetrics()
        self.alerts_history: List[Alert] = []
        self.alert_handlers: Dict[AlertChannel, Callable] = {}
        
        # Alert thresholds
        self.thresholds = {
            'max_response_time': config.get('max_response_time', 30.0),  # seconds
            'min_success_rate': config.get('min_success_rate', 0.95),   # 95%
            'max_error_rate': config.get('max_error_rate', 0.05),       # 5%
            'max_hourly_cost': config.get('max_hourly_cost', 10.0),     # $10/hour
            'max_rate_limit_hits': config.get('max_rate_limit_hits', 5)  # per hour
        }
        
        # Alert cooldown to prevent spam
        self.alert_cooldown = timedelta(minutes=config.get('alert_cooldown_minutes', 15))
        self.last_alerts: Dict[str, datetime] = {}
        
        # Initialize default alert handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default alert handlers"""
        self.alert_handlers[AlertChannel.LOG] = self._log_alert
        self.alert_handlers[AlertChannel.CONSOLE] = self._console_alert
    
    def _log_alert(self, alert: Alert):
        """Log alert to application logger"""
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            logger.error(f"ALERT: {alert.title} - {alert.message}")
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(f"ALERT: {alert.title} - {alert.message}")
        else:
            logger.info(f"ALERT: {alert.title} - {alert.message}")
    
    def _console_alert(self, alert: Alert):
        """Print alert to console"""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        emoji = severity_emoji.get(alert.severity, "📋")
        print(f"{emoji} {alert.severity.value.upper()}: {alert.title}")
        print(f"   {alert.message}")
        if alert.metadata:
            print(f"   Details: {alert.metadata}")
    
    def add_alert_handler(self, channel: AlertChannel, handler: Callable[[Alert], None]):
        """Add custom alert handler"""
        self.alert_handlers[channel] = handler
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent based on cooldown"""
        if alert_key not in self.last_alerts:
            return True
        
        time_since_last = datetime.now() - self.last_alerts[alert_key]
        return time_since_last > self.alert_cooldown
    
    def _send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        alert_key = f"{alert.source}:{alert.title}"
        
        if not self._should_send_alert(alert_key):
            return  # Skip due to cooldown
        
        self.alerts_history.append(alert)
        self.last_alerts[alert_key] = alert.timestamp
        
        # Send through all configured channels
        enabled_channels = self.config.get('alert_channels', [AlertChannel.LOG, AlertChannel.CONSOLE])
        
        for channel in enabled_channels:
            if channel in self.alert_handlers:
                try:
                    self.alert_handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel}: {e}")
    
    def check_provider_health(self, provider_stats: Dict[str, Any]):
        """Monitor provider health and generate alerts"""
        for provider_name, stats in provider_stats.items():
            # Check response time
            avg_response_time = stats.get('avg_response_time', 0)
            if avg_response_time > self.thresholds['max_response_time']:
                self._send_alert(Alert(
                    id=f"provider_slow_{provider_name}",
                    title=f"Provider {provider_name} Slow Response",
                    message=f"Average response time {avg_response_time:.2f}s exceeds threshold {self.thresholds['max_response_time']}s",
                    severity=AlertSeverity.WARNING,
                    metadata={'provider': provider_name, 'response_time': avg_response_time}
                ))
            
            # Check error rate
            error_rate = stats.get('error_rate', 0)
            if error_rate > self.thresholds['max_error_rate']:
                self._send_alert(Alert(
                    id=f"provider_errors_{provider_name}",
                    title=f"Provider {provider_name} High Error Rate",
                    message=f"Error rate {error_rate:.2%} exceeds threshold {self.thresholds['max_error_rate']:.2%}",
                    severity=AlertSeverity.ERROR,
                    metadata={'provider': provider_name, 'error_rate': error_rate}
                ))
            
            # Check availability
            is_available = stats.get('is_healthy', True)
            if not is_available:
                self._send_alert(Alert(
                    id=f"provider_down_{provider_name}",
                    title=f"Provider {provider_name} Unavailable",
                    message=f"Provider {provider_name} failed health check",
                    severity=AlertSeverity.CRITICAL,
                    metadata={'provider': provider_name}
                ))
    
    def check_cost_thresholds(self, cost_usage: Dict[str, Any]):
        """Monitor cost usage and generate alerts"""
        hourly_cost = cost_usage.get('hourly', {}).get('cost', 0)
        hourly_limit = cost_usage.get('hourly', {}).get('limit', self.thresholds['max_hourly_cost'])
        hourly_percentage = cost_usage.get('hourly', {}).get('percentage', 0)
        
        # Alert at 80% of hourly limit
        if hourly_percentage > 80:
            severity = AlertSeverity.CRITICAL if hourly_percentage > 95 else AlertSeverity.WARNING
            self._send_alert(Alert(
                id="cost_threshold_hourly",
                title="High Hourly Cost Usage",
                message=f"Hourly cost ${hourly_cost:.4f} is {hourly_percentage:.1f}% of limit ${hourly_limit:.2f}",
                severity=severity,
                metadata={'hourly_cost': hourly_cost, 'percentage': hourly_percentage}
            ))
        
        # Check daily cost
        daily_cost = cost_usage.get('daily', {}).get('cost', 0)
        daily_percentage = cost_usage.get('daily', {}).get('percentage', 0)
        
        if daily_percentage > 80:
            severity = AlertSeverity.CRITICAL if daily_percentage > 95 else AlertSeverity.WARNING
            self._send_alert(Alert(
                id="cost_threshold_daily",
                title="High Daily Cost Usage",
                message=f"Daily cost usage at {daily_percentage:.1f}% of limit",
                severity=severity,
                metadata={'daily_cost': daily_cost, 'percentage': daily_percentage}
            ))
    
    def check_generation_performance(self, success_rate: float, avg_time: float):
        """Monitor generation performance"""
        if success_rate < self.thresholds['min_success_rate']:
            self._send_alert(Alert(
                id="generation_success_rate",
                title="Low Generation Success Rate",
                message=f"Success rate {success_rate:.2%} below threshold {self.thresholds['min_success_rate']:.2%}",
                severity=AlertSeverity.ERROR,
                metadata={'success_rate': success_rate, 'threshold': self.thresholds['min_success_rate']}
            ))
        
        if avg_time > self.thresholds['max_response_time']:
            self._send_alert(Alert(
                id="generation_slow",
                title="Slow Generation Performance", 
                message=f"Average generation time {avg_time:.2f}s exceeds threshold",
                severity=AlertSeverity.WARNING,
                metadata={'avg_time': avg_time, 'threshold': self.thresholds['max_response_time']}
            ))
    
    def check_rate_limiting(self, rate_limit_data: Dict[str, int]):
        """Monitor rate limiting across providers"""
        for provider, hits in rate_limit_data.items():
            if hits > self.thresholds['max_rate_limit_hits']:
                self._send_alert(Alert(
                    id=f"rate_limit_{provider}",
                    title=f"Frequent Rate Limiting on {provider}",
                    message=f"Provider {provider} hit rate limits {hits} times recently",
                    severity=AlertSeverity.WARNING,
                    metadata={'provider': provider, 'rate_limit_hits': hits}
                ))
    
    def monitor_system_health(self, system_stats: Dict[str, Any]):
        """Main monitoring method - check all health indicators"""
        # Check provider health
        if 'providers' in system_stats:
            self.check_provider_health(system_stats['providers'])
        
        # Check cost usage
        if 'cost_controls' in system_stats:
            self.check_cost_thresholds(system_stats['cost_controls'])
        
        # Check generation performance
        if 'generation' in system_stats:
            gen_stats = system_stats['generation']
            self.check_generation_performance(
                gen_stats.get('success_rate', 1.0),
                gen_stats.get('avg_time', 0.0)
            )
        
        # Check rate limiting
        if 'rate_limits' in system_stats:
            self.check_rate_limiting(system_stats['rate_limits'])
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get current monitoring status summary"""
        recent_alerts = [
            alert.to_dict() for alert in self.alerts_history[-10:]  # Last 10 alerts
        ]
        
        alert_counts = {
            'critical': len([a for a in self.alerts_history if a.severity == AlertSeverity.CRITICAL]),
            'error': len([a for a in self.alerts_history if a.severity == AlertSeverity.ERROR]),
            'warning': len([a for a in self.alerts_history if a.severity == AlertSeverity.WARNING]),
            'info': len([a for a in self.alerts_history if a.severity == AlertSeverity.INFO])
        }
        
        return {
            'monitoring_status': 'active',
            'alert_counts': alert_counts,
            'recent_alerts': recent_alerts,
            'thresholds': self.thresholds,
            'uptime': time.time(),  # Can be enhanced with actual uptime tracking
            'last_check': datetime.now().isoformat()
        }

def create_production_monitor(config: Optional[Dict[str, Any]] = None) -> ProductionMonitor:
    """Factory function to create production monitor with defaults"""
    if config is None:
        config = {
            'max_response_time': 30.0,
            'min_success_rate': 0.95,
            'max_error_rate': 0.05,
            'max_hourly_cost': 10.0,
            'alert_cooldown_minutes': 15,
            'alert_channels': [AlertChannel.LOG, AlertChannel.CONSOLE]
        }
    
    return ProductionMonitor(config)