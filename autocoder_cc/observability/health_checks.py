#!/usr/bin/env python3
"""
OpenTelemetry Backend Health Checks
==================================

Provides health check functionality for OpenTelemetry backend connectivity
as required by Cycle 21 validation requirements.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from autocoder_cc.core.config import settings
from autocoder_cc.observability.structured_logging import get_logger


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    service_name: str
    is_healthy: bool
    response_time_ms: float
    endpoint: str
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class HealthCheckRegistry:
    """Registry for health check functions with async execution"""
    
    def __init__(self):
        self.checks = {}
        self.logger = get_logger(__name__)
    
    def register_check(self, name: str, check_function):
        """Register a health check function"""
        self.checks[name] = check_function
        self.logger.debug(f"Registered health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks and return results"""
        results = {}
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    results[name] = await check_func()
                else:
                    results[name] = check_func()
            except Exception as e:
                self.logger.error(f"Health check '{name}' failed: {e}")
                results[name] = {"healthy": False, "error": str(e)}
        return results
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {"healthy": False, "error": f"Check '{name}' not found"}
        
        try:
            check_func = self.checks[name]
            if asyncio.iscoroutinefunction(check_func):
                return await check_func()
            else:
                return check_func()
        except Exception as e:
            self.logger.error(f"Health check '{name}' failed: {e}")
            return {"healthy": False, "error": str(e)}


class OpenTelemetryHealthChecker:
    """
    Health checker for OpenTelemetry backend services.
    
    Supports:
    - Jaeger tracing backend health checks
    - Prometheus metrics backend health checks
    - OTLP collector endpoint verification
    - Connection timeout and retry logic
    - Detailed error reporting
    """
    
    def __init__(self, timeout: float = 5.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = get_logger(__name__)
        
        # Default endpoints (can be overridden by settings)
        self.default_endpoints = {
            'jaeger_ui': 'http://localhost:16686',
            'jaeger_api': 'http://localhost:16686/api/services',
            'jaeger_health': 'http://localhost:14269/health',
            'prometheus_ui': 'http://localhost:9090',
            'prometheus_health': 'http://localhost:9090/-/healthy',
            'prometheus_api': 'http://localhost:9090/api/v1/status/config',
            'otlp_grpc': 'http://localhost:4317',
            'otlp_http': 'http://localhost:4318/v1/traces'
        }
    
    def _get_endpoint(self, service_type: str, endpoint_key: str) -> str:
        """Get endpoint URL from settings or defaults"""
        # Try to get from settings first
        if hasattr(settings, 'JAEGER_UI_ENDPOINT') and endpoint_key.startswith('jaeger'):
            base_url = settings.JAEGER_UI_ENDPOINT
            if endpoint_key == 'jaeger_api':
                return f"{base_url}/api/services"
            elif endpoint_key == 'jaeger_health':
                return f"{base_url.replace(':16686', ':14269')}/health"
            return base_url
        
        if hasattr(settings, 'PROMETHEUS_ENDPOINT') and endpoint_key.startswith('prometheus'):
            base_url = settings.PROMETHEUS_ENDPOINT
            if endpoint_key == 'prometheus_health':
                return f"{base_url}/-/healthy"
            elif endpoint_key == 'prometheus_api':
                return f"{base_url}/api/v1/status/config"
            return base_url
        
        if hasattr(settings, 'OTLP_ENDPOINT') and endpoint_key.startswith('otlp'):
            base_url = settings.OTLP_ENDPOINT
            if endpoint_key == 'otlp_http':
                return f"{base_url}/v1/traces"
            return base_url
        
        # Fall back to defaults
        return self.default_endpoints.get(endpoint_key, '')
    
    async def _http_health_check(self, endpoint: str, expected_status: List[int] = None) -> Tuple[bool, float, Optional[int], Optional[str], Optional[Dict]]:
        """Perform HTTP health check with retry logic"""
        if expected_status is None:
            expected_status = [200, 204]
        
        last_error = None
        for attempt in range(self.max_retries):
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(endpoint) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        is_healthy = response.status in expected_status
                        
                        # Try to get response details
                        details = None
                        try:
                            if response.content_type and 'json' in response.content_type:
                                details = await response.json()
                            else:
                                text = await response.text()
                                if text and len(text) < 1000:  # Limit text size
                                    details = {'response_text': text[:500]}
                        except:
                            pass  # Ignore response parsing errors
                        
                        if is_healthy:
                            return True, response_time, response.status, None, details
                        else:
                            last_error = f"HTTP {response.status}"
                            
            except asyncio.TimeoutError:
                response_time = (time.time() - start_time) * 1000
                last_error = f"Timeout after {self.timeout}s"
            except aiohttp.ClientError as e:
                response_time = (time.time() - start_time) * 1000
                last_error = f"Connection error: {str(e)}"
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                last_error = f"Unexpected error: {str(e)}"
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        return False, response_time, None, last_error, None
    
    async def check_jaeger_health(self) -> HealthCheckResult:
        """Check Jaeger tracing backend health"""
        self.logger.debug("Checking Jaeger health...")
        
        # Try multiple endpoints for comprehensive check
        endpoints_to_check = [
            ('health', self._get_endpoint('jaeger', 'jaeger_health')),
            ('api', self._get_endpoint('jaeger', 'jaeger_api')),
            ('ui', self._get_endpoint('jaeger', 'jaeger_ui'))
        ]
        
        best_result = None
        total_response_time = 0
        errors = []
        
        for endpoint_name, endpoint_url in endpoints_to_check:
            if not endpoint_url:
                continue
                
            is_healthy, response_time, status_code, error, details = await self._http_health_check(endpoint_url)
            total_response_time += response_time
            
            if is_healthy:
                # Found a healthy endpoint
                return HealthCheckResult(
                    service_name="Jaeger",
                    is_healthy=True,
                    response_time_ms=response_time,
                    endpoint=endpoint_url,
                    status_code=status_code,
                    details={'endpoint_type': endpoint_name, 'response_details': details}
                )
            else:
                errors.append(f"{endpoint_name} ({endpoint_url}): {error}")
                if best_result is None:
                    best_result = (endpoint_url, response_time, status_code, error)
        
        # No healthy endpoints found
        endpoint_url, response_time, status_code, error = best_result or (endpoints_to_check[0][1], 0, None, "No endpoints configured")
        
        return HealthCheckResult(
            service_name="Jaeger",
            is_healthy=False,
            response_time_ms=response_time,
            endpoint=endpoint_url,
            status_code=status_code,
            error_message=error,
            details={'all_errors': errors}
        )
    
    async def check_prometheus_health(self) -> HealthCheckResult:
        """Check Prometheus metrics backend health"""
        self.logger.debug("Checking Prometheus health...")
        
        # Try health endpoint first, then API endpoint
        endpoints_to_check = [
            ('health', self._get_endpoint('prometheus', 'prometheus_health')),
            ('api', self._get_endpoint('prometheus', 'prometheus_api')),
            ('ui', self._get_endpoint('prometheus', 'prometheus_ui'))
        ]
        
        best_result = None
        errors = []
        
        for endpoint_name, endpoint_url in endpoints_to_check:
            if not endpoint_url:
                continue
                
            is_healthy, response_time, status_code, error, details = await self._http_health_check(endpoint_url)
            
            if is_healthy:
                # Extract Prometheus version if available
                version_info = None
                if details and isinstance(details, dict):
                    if 'data' in details and 'yaml' in details['data']:
                        version_info = "Config API accessible"
                    elif 'response_text' in details:
                        if 'Prometheus' in details['response_text']:
                            version_info = "UI accessible"
                
                return HealthCheckResult(
                    service_name="Prometheus",
                    is_healthy=True,
                    response_time_ms=response_time,
                    endpoint=endpoint_url,
                    status_code=status_code,
                    details={
                        'endpoint_type': endpoint_name,
                        'version_info': version_info,
                        'response_details': details
                    }
                )
            else:
                errors.append(f"{endpoint_name} ({endpoint_url}): {error}")
                if best_result is None:
                    best_result = (endpoint_url, response_time, status_code, error)
        
        # No healthy endpoints found
        endpoint_url, response_time, status_code, error = best_result or (endpoints_to_check[0][1], 0, None, "No endpoints configured")
        
        return HealthCheckResult(
            service_name="Prometheus",
            is_healthy=False,
            response_time_ms=response_time,
            endpoint=endpoint_url,
            status_code=status_code,
            error_message=error,
            details={'all_errors': errors}
        )
    
    async def check_otlp_collector_health(self) -> HealthCheckResult:
        """Check OTLP collector health"""
        self.logger.debug("Checking OTLP collector health...")
        
        # OTLP HTTP endpoint check (POST with small trace payload)
        otlp_http_endpoint = self._get_endpoint('otlp', 'otlp_http')
        
        if not otlp_http_endpoint:
            return HealthCheckResult(
                service_name="OTLP Collector",
                is_healthy=False,
                response_time_ms=0,
                endpoint="",
                error_message="No OTLP endpoint configured"
            )
        
        # Simple connectivity test (OPTIONS or GET)
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Try OPTIONS first (more permissive)
                async with session.options(otlp_http_endpoint) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # OTLP typically returns 405 for OPTIONS, which is fine
                    if response.status in [200, 204, 405]:
                        return HealthCheckResult(
                            service_name="OTLP Collector",
                            is_healthy=True,
                            response_time_ms=response_time,
                            endpoint=otlp_http_endpoint,
                            status_code=response.status,
                            details={'method': 'OPTIONS', 'endpoint_accessible': True}
                        )
                    else:
                        return HealthCheckResult(
                            service_name="OTLP Collector",
                            is_healthy=False,
                            response_time_ms=response_time,
                            endpoint=otlp_http_endpoint,
                            status_code=response.status,
                            error_message=f"Unexpected status code: {response.status}"
                        )
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="OTLP Collector",
                is_healthy=False,
                response_time_ms=response_time,
                endpoint=otlp_http_endpoint,
                error_message=f"Timeout after {self.timeout}s"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="OTLP Collector",
                is_healthy=False,
                response_time_ms=response_time,
                endpoint=otlp_http_endpoint,
                error_message=str(e)
            )
    
    async def check_all_backends(self) -> List[HealthCheckResult]:
        """Check all OpenTelemetry backend services"""
        self.logger.info("Performing comprehensive OpenTelemetry backend health checks...")
        
        # Run all health checks concurrently
        health_check_tasks = [
            self.check_jaeger_health(),
            self.check_prometheus_health(),
            self.check_otlp_collector_health()
        ]
        
        results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        # Handle any exceptions
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_names = ["Jaeger", "Prometheus", "OTLP Collector"]
                health_results.append(HealthCheckResult(
                    service_name=service_names[i],
                    is_healthy=False,
                    response_time_ms=0,
                    endpoint="",
                    error_message=f"Health check failed: {str(result)}"
                ))
            else:
                health_results.append(result)
        
        return health_results
    
    async def wait_for_backends_healthy(self, timeout: float = 60, check_interval: float = 5) -> bool:
        """Wait for all backends to become healthy within timeout"""
        self.logger.info(f"Waiting for backends to become healthy (timeout: {timeout}s)...")
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            health_results = await self.check_all_backends()
            
            healthy_services = [result for result in health_results if result.is_healthy]
            unhealthy_services = [result for result in health_results if not result.is_healthy]
            
            if len(unhealthy_services) == 0:
                self.logger.info(f"All {len(healthy_services)} backend services are healthy")
                return True
            
            self.logger.info(f"Healthy: {len(healthy_services)}, Unhealthy: {len(unhealthy_services)}")
            for unhealthy in unhealthy_services:
                self.logger.debug(f"  {unhealthy.service_name}: {unhealthy.error_message}")
            
            await asyncio.sleep(check_interval)
        
        self.logger.warning(f"Backend health check timeout after {timeout}s")
        return False
    
    def generate_health_report(self, health_results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        healthy_count = sum(1 for result in health_results if result.is_healthy)
        total_count = len(health_results)
        
        avg_response_time = sum(result.response_time_ms for result in health_results) / total_count if total_count > 0 else 0
        
        return {
            'overall_health': healthy_count == total_count,
            'healthy_services': healthy_count,
            'total_services': total_count,
            'average_response_time_ms': round(avg_response_time, 2),
            'timestamp': datetime.now().isoformat(),
            'service_details': [
                {
                    'service_name': result.service_name,
                    'is_healthy': result.is_healthy,
                    'response_time_ms': result.response_time_ms,
                    'endpoint': result.endpoint,
                    'status_code': result.status_code,
                    'error_message': result.error_message,
                    'details': result.details,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in health_results
            ]
        }


# Convenience functions for integration
async def check_opentelemetry_health(timeout: float = 5.0) -> List[HealthCheckResult]:
    """Quick health check for all OpenTelemetry backends"""
    checker = OpenTelemetryHealthChecker(timeout=timeout)
    return await checker.check_all_backends()


async def verify_backend_connectivity() -> bool:
    """Verify that at least one backend is healthy"""
    health_results = await check_opentelemetry_health()
    return any(result.is_healthy for result in health_results)


async def wait_for_backend_readiness(timeout: float = 60) -> bool:
    """Wait for backends to be ready for data export"""
    checker = OpenTelemetryHealthChecker()
    return await checker.wait_for_backends_healthy(timeout=timeout)


# CLI for standalone health checking
async def main():
    """CLI main function"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='OpenTelemetry Backend Health Checker')
    parser.add_argument('--timeout', type=float, default=5.0, help='Request timeout in seconds')
    parser.add_argument('--wait', type=float, help='Wait for backends to be healthy (timeout in seconds)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    checker = OpenTelemetryHealthChecker(timeout=args.timeout)
    
    if args.wait:
        success = await checker.wait_for_backends_healthy(timeout=args.wait)
        if success:
            print("✅ All backends are healthy")
            return 0
        else:
            print("❌ Backends failed to become healthy within timeout")
            return 1
    
    # Perform health checks
    health_results = await checker.check_all_backends()
    health_report = checker.generate_health_report(health_results)
    
    if args.json:
        print(json.dumps(health_report, indent=2))
    else:
        print("OpenTelemetry Backend Health Check Results")
        print("=" * 45)
        
        overall_status = "✅ Healthy" if health_report['overall_health'] else "❌ Unhealthy"
        print(f"Overall Status: {overall_status}")
        print(f"Healthy Services: {health_report['healthy_services']}/{health_report['total_services']}")
        print(f"Average Response Time: {health_report['average_response_time_ms']:.2f}ms")
        print()
        
        for service in health_report['service_details']:
            status_emoji = "✅" if service['is_healthy'] else "❌"
            print(f"{status_emoji} {service['service_name']}")
            print(f"   Endpoint: {service['endpoint']}")
            print(f"   Response Time: {service['response_time_ms']:.2f}ms")
            if service['status_code']:
                print(f"   Status Code: {service['status_code']}")
            if service['error_message']:
                print(f"   Error: {service['error_message']}")
            print()
    
    # Return appropriate exit code
    return 0 if health_report['overall_health'] else 1


if __name__ == '__main__':
    import sys
    sys.exit(asyncio.run(main()))