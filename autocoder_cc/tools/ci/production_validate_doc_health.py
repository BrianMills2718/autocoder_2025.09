#!/usr/bin/env python3
"""
Production-Grade Documentation Health Score Validator for CI/CD
Comprehensive error handling, logging, monitoring, and notification system
"""

import json
import sys
import argparse
import logging
import time
import uuid
import traceback
import smtplib
import requests
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml


@dataclass
class ValidationMetrics:
    """Metrics collected during validation"""
    execution_time: float
    correlation_id: str
    timestamp: str
    health_score: Optional[float] = None
    high_issues: Optional[int] = None
    validation_passed: bool = False
    error_count: int = 0
    warning_count: int = 0


@dataclass
class NotificationConfig:
    """Configuration for notification systems"""
    email_enabled: bool = False
    webhook_enabled: bool = False
    github_issues_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_recipients: List[str] = None
    webhook_url: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None


class StructuredLogger:
    """Structured logging with correlation IDs and metrics"""
    
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup structured JSON logging"""
        logger = logging.getLogger(f"doc_health_validator_{self.correlation_id}")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # JSON formatter
        formatter = StructuredFormatter(self.correlation_id)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def info(self, message: str, **context):
        """Log info message with context"""
        self.logger.info(message, extra={'context': context})
    
    def warning(self, message: str, **context):
        """Log warning message with context"""
        self.logger.warning(message, extra={'context': context})
    
    def error(self, message: str, error: Exception = None, **context):
        """Log error message with context and exception details"""
        extra_context = {'context': context}
        if error:
            extra_context['context']['error_type'] = type(error).__name__
            extra_context['context']['error_message'] = str(error)
            extra_context['context']['traceback'] = traceback.format_exc()
        self.logger.error(message, extra=extra_context)
    
    def critical(self, message: str, error: Exception = None, **context):
        """Log critical message with context"""
        extra_context = {'context': context}
        if error:
            extra_context['context']['error_type'] = type(error).__name__
            extra_context['context']['error_message'] = str(error)
            extra_context['context']['traceback'] = traceback.format_exc()
        self.logger.critical(message, extra=extra_context)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, correlation_id: str):
        super().__init__()
        self.correlation_id = correlation_id
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'correlation_id': self.correlation_id,
            'level': record.levelname,
            'component': 'doc_health_validator',
            'message': record.getMessage(),
            'logger_name': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if present
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        return json.dumps(log_entry)


class MetricsCollector:
    """Collects and exports metrics for monitoring"""
    
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.metrics = ValidationMetrics(
            execution_time=0.0,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.start_time = time.time()
    
    def record_health_data(self, health_score: float, high_issues: int):
        """Record health data metrics"""
        self.metrics.health_score = health_score
        self.metrics.high_issues = high_issues
    
    def record_validation_result(self, passed: bool):
        """Record validation result"""
        self.metrics.validation_passed = passed
    
    def increment_error_count(self):
        """Increment error counter"""
        self.metrics.error_count += 1
    
    def increment_warning_count(self):
        """Increment warning counter"""
        self.metrics.warning_count += 1
    
    def finalize_metrics(self):
        """Finalize metrics collection"""
        self.metrics.execution_time = time.time() - self.start_time
        return self.metrics
    
    def export_metrics(self, export_path: Optional[str] = None):
        """Export metrics to file or monitoring system"""
        metrics_data = asdict(self.finalize_metrics())
        
        if export_path:
            with open(export_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        
        return metrics_data


class NotificationSystem:
    """Enterprise notification system for critical failures"""
    
    def __init__(self, config: NotificationConfig, logger: StructuredLogger):
        self.config = config
        self.logger = logger
    
    def send_critical_failure_notification(self, 
                                         metrics: ValidationMetrics, 
                                         error_details: str):
        """Send notifications for critical failures"""
        try:
            if self.config.email_enabled:
                self._send_email_notification(metrics, error_details)
            
            if self.config.webhook_enabled:
                self._send_webhook_notification(metrics, error_details)
            
            if self.config.github_issues_enabled:
                self._create_github_issue(metrics, error_details)
                
        except Exception as e:
            self.logger.error("Failed to send notifications", error=e,
                            metrics=asdict(metrics))
    
    def _send_email_notification(self, metrics: ValidationMetrics, error_details: str):
        """Send email notification"""
        if not all([self.config.smtp_server, self.config.email_recipients]):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"[CRITICAL] Documentation Health Validation Failed - {metrics.correlation_id}"
            
            body = f"""
Documentation health validation has failed critically.

Correlation ID: {metrics.correlation_id}
Timestamp: {metrics.timestamp}
Execution Time: {metrics.execution_time:.2f}s
Health Score: {metrics.health_score}
High Priority Issues: {metrics.high_issues}
Error Count: {metrics.error_count}

Error Details:
{error_details}

Please investigate immediately.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.config.smtp_username, self.config.email_recipients, text)
            server.quit()
            
            self.logger.info("Email notification sent successfully",
                           recipients=self.config.email_recipients)
            
        except Exception as e:
            self.logger.error("Failed to send email notification", error=e)
    
    def _send_webhook_notification(self, metrics: ValidationMetrics, error_details: str):
        """Send webhook notification"""
        if not self.config.webhook_url:
            return
        
        try:
            payload = {
                'event': 'documentation_health_failure',
                'severity': 'critical',
                'correlation_id': metrics.correlation_id,
                'timestamp': metrics.timestamp,
                'metrics': asdict(metrics),
                'error_details': error_details
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            self.logger.info("Webhook notification sent successfully",
                           webhook_url=self.config.webhook_url,
                           response_status=response.status_code)
            
        except Exception as e:
            self.logger.error("Failed to send webhook notification", error=e,
                            webhook_url=self.config.webhook_url)
    
    def _create_github_issue(self, metrics: ValidationMetrics, error_details: str):
        """Create GitHub issue for critical failure"""
        if not all([self.config.github_token, self.config.github_repo]):
            return
        
        try:
            issue_title = f"[CRITICAL] Documentation Health Validation Failed - {metrics.correlation_id}"
            issue_body = f"""
## Critical Documentation Health Validation Failure

**Correlation ID:** `{metrics.correlation_id}`
**Timestamp:** {metrics.timestamp}
**Execution Time:** {metrics.execution_time:.2f}s

### Metrics
- **Health Score:** {metrics.health_score}
- **High Priority Issues:** {metrics.high_issues}
- **Error Count:** {metrics.error_count}
- **Warning Count:** {metrics.warning_count}

### Error Details
```
{error_details}
```

### Action Required
This is a critical failure that requires immediate investigation and resolution.

**Auto-generated by Documentation Health Validator**
"""
            
            api_url = f"https://api.github.com/repos/{self.config.github_repo}/issues"
            headers = {
                'Authorization': f'token {self.config.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            payload = {
                'title': issue_title,
                'body': issue_body,
                'labels': ['bug', 'critical', 'documentation', 'automated']
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            issue_data = response.json()
            
            self.logger.info("GitHub issue created successfully",
                           issue_number=issue_data.get('number'),
                           issue_url=issue_data.get('html_url'))
            
        except Exception as e:
            self.logger.error("Failed to create GitHub issue", error=e,
                            repo=self.config.github_repo)


class RetryHandler:
    """Handles retry logic for transient failures"""
    
    def __init__(self, max_retries: int = 3, backoff_multiplier: float = 2.0):
        self.max_retries = max_retries
        self.backoff_multiplier = backoff_multiplier
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = (self.backoff_multiplier ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    break
        
        raise last_exception


class ProductionDocumentationHealthValidator:
    """Production-grade documentation health validator with enterprise features"""
    
    DEFAULT_HEALTH_THRESHOLD = 90
    DEFAULT_HIGH_ISSUES_THRESHOLD = 0
    
    def __init__(self, 
                 health_threshold: int = None, 
                 high_issues_threshold: int = None,
                 config_file: str = None):
        self.health_threshold = health_threshold or self.DEFAULT_HEALTH_THRESHOLD
        self.high_issues_threshold = high_issues_threshold or self.DEFAULT_HIGH_ISSUES_THRESHOLD
        
        # Generate correlation ID for this execution
        self.correlation_id = str(uuid.uuid4())
        
        # Initialize components
        self.logger = StructuredLogger(self.correlation_id)
        self.metrics = MetricsCollector(self.correlation_id)
        self.retry_handler = RetryHandler()
        
        # Load configuration
        self.notification_config = self._load_notification_config(config_file)
        self.notification_system = NotificationSystem(self.notification_config, self.logger)
        
        self.logger.info("Production validator initialized",
                        health_threshold=self.health_threshold,
                        high_issues_threshold=self.high_issues_threshold,
                        correlation_id=self.correlation_id)
    
    def _load_notification_config(self, config_file: str = None) -> NotificationConfig:
        """Load notification configuration from file or environment"""
        config = NotificationConfig()
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                notifications = config_data.get('notifications', {})
                
                # Email configuration
                email_config = notifications.get('email', {})
                config.email_enabled = email_config.get('enabled', False)
                config.smtp_server = email_config.get('smtp_server')
                config.smtp_port = email_config.get('smtp_port', 587)
                config.smtp_username = email_config.get('username')
                config.smtp_password = email_config.get('password')
                config.email_recipients = email_config.get('recipients', [])
                
                # Webhook configuration
                webhook_config = notifications.get('webhook', {})
                config.webhook_enabled = webhook_config.get('enabled', False)
                config.webhook_url = webhook_config.get('url')
                
                # GitHub configuration
                github_config = notifications.get('github', {})
                config.github_issues_enabled = github_config.get('enabled', False)
                config.github_token = github_config.get('token')
                config.github_repo = github_config.get('repo')
                
            except Exception as e:
                self.logger.warning("Failed to load notification config", error=e,
                                  config_file=config_file)
        
        return config
    
    def validate_health_report(self, report_file: str, timeout: int = 30) -> bool:
        """
        Validates documentation health report with comprehensive error handling
        
        Args:
            report_file: Path to JSON health report
            timeout: Maximum execution time in seconds
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            self.logger.info("Starting health report validation",
                           report_file=report_file,
                           timeout=timeout)
            
            # Validate input parameters
            self._validate_input_parameters(report_file, timeout)
            
            # Load and validate report file with retry logic
            report_data = self.retry_handler.retry_with_backoff(
                self._load_report_file, report_file
            )
            
            # Validate report data structure
            self._validate_report_structure(report_data)
            
            # Perform health validation
            validation_result = self._perform_health_validation(report_data)
            
            # Record metrics
            self.metrics.record_validation_result(validation_result)
            
            self.logger.info("Health report validation completed",
                           validation_passed=validation_result,
                           health_score=report_data.get('health_score'),
                           high_issues=report_data.get('statistics', {}).get('high_issues'))
            
            return validation_result
            
        except ValidationError as e:
            self.metrics.increment_error_count()
            self.logger.error("Validation error", error=e, report_file=report_file)
            
            # Send GitHub Actions error annotation
            print(f"::error file={report_file}::Validation error: {e}")
            
            return False
            
        except CriticalValidationError as e:
            self.metrics.increment_error_count()
            self.logger.critical("Critical validation error", error=e, 
                               report_file=report_file)
            
            # Send critical failure notifications
            self.notification_system.send_critical_failure_notification(
                self.metrics.finalize_metrics(), str(e)
            )
            
            # Send GitHub Actions error annotation
            print(f"::error file={report_file}::Critical validation error: {e}")
            
            return False
            
        except Exception as e:
            self.metrics.increment_error_count()
            self.logger.critical("Unexpected error during validation", error=e,
                               report_file=report_file)
            
            # Send critical failure notifications for unexpected errors
            self.notification_system.send_critical_failure_notification(
                self.metrics.finalize_metrics(), 
                f"Unexpected error: {e}\n\nTraceback:\n{traceback.format_exc()}"
            )
            
            # Send GitHub Actions error annotation
            print(f"::error file={report_file}::Unexpected error: {e}")
            
            return False
        
        finally:
            # Always finalize metrics
            final_metrics = self.metrics.finalize_metrics()
            self.logger.info("Validation execution completed",
                           execution_time=final_metrics.execution_time,
                           error_count=final_metrics.error_count,
                           warning_count=final_metrics.warning_count)
    
    def _validate_input_parameters(self, report_file: str, timeout: int):
        """Validate input parameters"""
        if not report_file:
            raise ValidationError("Report file path cannot be empty")
        
        if timeout <= 0:
            raise ValidationError("Timeout must be positive")
        
        if timeout > 300:  # 5 minutes max
            raise ValidationError("Timeout cannot exceed 300 seconds")
    
    def _load_report_file(self, report_file: str) -> Dict[str, Any]:
        """Load and parse report file with comprehensive error handling"""
        report_path = Path(report_file)
        
        # Check file existence
        if not report_path.exists():
            raise ValidationError(f"Health report file not found: {report_file}")
        
        # Check file permissions
        if not os.access(report_path, os.R_OK):
            raise ValidationError(f"No read permission for file: {report_file}")
        
        # Check file size (prevent loading huge files)
        file_size = report_path.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            raise ValidationError(f"Report file too large: {file_size} bytes")
        
        if file_size == 0:
            raise ValidationError(f"Report file is empty: {report_file}")
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("Report file loaded successfully",
                           file_size=file_size,
                           report_file=report_file)
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in health report: {e}")
        except UnicodeDecodeError as e:
            raise ValidationError(f"Invalid file encoding: {e}")
        except MemoryError:
            raise CriticalValidationError("Insufficient memory to load report file")
    
    def _validate_report_structure(self, data: Dict[str, Any]):
        """Validate report data structure"""
        required_fields = ['health_score', 'statistics']
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field in report: {field}")
        
        # Validate health_score
        health_score = data.get('health_score')
        if not isinstance(health_score, (int, float)):
            raise ValidationError("health_score must be a number")
        
        if not 0 <= health_score <= 100:
            raise ValidationError(f"health_score must be between 0 and 100, got {health_score}")
        
        # Validate statistics
        statistics = data.get('statistics', {})
        if not isinstance(statistics, dict):
            raise ValidationError("statistics must be a dictionary")
        
        # Validate high_issues
        high_issues = statistics.get('high_issues', 0)
        if not isinstance(high_issues, int):
            raise ValidationError("high_issues must be an integer")
        
        if high_issues < 0:
            raise ValidationError("high_issues cannot be negative")
    
    def _perform_health_validation(self, data: Dict[str, Any]) -> bool:
        """Perform health validation against thresholds"""
        health_score = data.get('health_score', 0)
        high_issues = data.get('statistics', {}).get('high_issues', 0)
        
        # Record health data in metrics
        self.metrics.record_health_data(health_score, high_issues)
        
        # Display validation information
        print(f"📊 Health score: {health_score}")
        print(f"⚠️  High priority issues: {high_issues}")
        print(f"🎯 Required health score: ≥{self.health_threshold}")
        print(f"🎯 Max high priority issues: ≤{self.high_issues_threshold}")
        
        validation_passed = True
        
        # Check health score threshold
        if health_score < self.health_threshold:
            error_msg = f"Documentation health score {health_score} below threshold ({self.health_threshold})"
            print(f"::error::{error_msg}")
            self.logger.warning("Health score below threshold",
                              actual_score=health_score,
                              required_score=self.health_threshold)
            self.metrics.increment_error_count()
            validation_passed = False
        
        # Check high priority issues threshold
        if high_issues > self.high_issues_threshold:
            error_msg = f"{high_issues} high priority documentation issues detected (max: {self.high_issues_threshold})"
            print(f"::error::{error_msg}")
            self.logger.warning("Too many high priority issues",
                              actual_issues=high_issues,
                              max_issues=self.high_issues_threshold)
            self.metrics.increment_error_count()
            validation_passed = False
        
        # Display result
        if validation_passed:
            print("✅ Documentation health check passed")
            self.logger.info("Documentation health check passed")
        else:
            print("❌ Documentation health check failed")
            self.logger.warning("Documentation health check failed")
        
        return validation_passed
    
    def get_health_summary(self, report_file: str) -> Dict[str, Any]:
        """Get comprehensive health summary with error handling"""
        try:
            self.logger.info("Generating health summary", report_file=report_file)
            
            report_data = self.retry_handler.retry_with_backoff(
                self._load_report_file, report_file
            )
            
            validation_passed = self._perform_health_validation(report_data)
            
            summary = {
                'correlation_id': self.correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'health_score': report_data.get('health_score', 0),
                'high_issues': report_data.get('statistics', {}).get('high_issues', 0),
                'total_issues': report_data.get('statistics', {}).get('total_issues', 0),
                'coverage': report_data.get('coverage', {}),
                'validation_passed': validation_passed,
                'thresholds': {
                    'health_score_minimum': self.health_threshold,
                    'high_issues_maximum': self.high_issues_threshold
                },
                'metrics': asdict(self.metrics.finalize_metrics())
            }
            
            self.logger.info("Health summary generated successfully")
            return summary
            
        except Exception as e:
            self.logger.error("Failed to generate health summary", error=e,
                            report_file=report_file)
            return {
                'correlation_id': self.correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def export_metrics(self, export_path: str):
        """Export metrics for monitoring systems"""
        try:
            metrics_data = self.metrics.export_metrics(export_path)
            self.logger.info("Metrics exported successfully", export_path=export_path)
            return metrics_data
        except Exception as e:
            self.logger.error("Failed to export metrics", error=e, export_path=export_path)
            raise


class ValidationError(Exception):
    """Standard validation error"""
    pass


class CriticalValidationError(Exception):
    """Critical validation error requiring immediate attention"""
    pass


def main():
    """Main CLI entry point with comprehensive error handling"""
    parser = argparse.ArgumentParser(
        description='Production-grade documentation health score validator'
    )
    parser.add_argument('report_file', 
                       help='Path to JSON health report file')
    parser.add_argument('--health-threshold', type=int, default=90,
                       help='Minimum health score threshold (default: 90)')
    parser.add_argument('--max-high-issues', type=int, default=0,
                       help='Maximum high priority issues allowed (default: 0)')
    parser.add_argument('--summary', action='store_true',
                       help='Print summary and exit with success')
    parser.add_argument('--config', 
                       help='Path to notification configuration file')
    parser.add_argument('--export-metrics',
                       help='Export metrics to specified file')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Maximum execution time in seconds (default: 30)')
    
    args = parser.parse_args()
    
    try:
        validator = ProductionDocumentationHealthValidator(
            health_threshold=args.health_threshold,
            high_issues_threshold=args.max_high_issues,
            config_file=args.config
        )
        
        if args.summary:
            summary = validator.get_health_summary(args.report_file)
            print(json.dumps(summary, indent=2))
            
            if args.export_metrics:
                validator.export_metrics(args.export_metrics)
            
            sys.exit(0)
        
        success = validator.validate_health_report(args.report_file, args.timeout)
        
        if args.export_metrics:
            validator.export_metrics(args.export_metrics)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n::error::Validation interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"::error::Fatal error during validation: {e}")
        sys.exit(2)  # Fatal error exit code


if __name__ == "__main__":
    main()