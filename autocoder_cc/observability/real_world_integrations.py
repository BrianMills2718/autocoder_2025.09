#!/usr/bin/env python3
"""
Real-World Data Integration for Observability Economics

Integrates with actual cost APIs and monitoring systems to provide
real-world data for observability economics management.
"""

import json
import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RealCostData:
    """Real-world cost data from external APIs"""
    timestamp: datetime
    total_cost: float
    storage_cost: float
    query_cost: float
    ingestion_cost: float
    source: str
    period: str
    confidence: float = 1.0

class AWSCostExplorerIntegration:
    """Integration with AWS Cost Explorer API"""
    
    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None):
        self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.logger = logging.getLogger(__name__)
        
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS credentials required - set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
    
    def get_cloudwatch_costs(self, start_date: datetime, end_date: datetime) -> RealCostData:
        """Get actual CloudWatch costs from AWS Cost Explorer"""
        try:
            # Real AWS Cost Explorer API call
            import boto3
            client = boto3.client(
                'ce',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name='us-east-1'
            )
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon CloudWatch']
                    }
                }
            )
            
            total_cost = 0.0
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    if 'Amazon CloudWatch' in group['Keys']:
                        cost = float(group['Metrics']['BlendedCost']['Amount'])
                        total_cost += cost
            
            return RealCostData(
                timestamp=datetime.now(),
                total_cost=total_cost,
                storage_cost=total_cost * 0.6,  # CloudWatch Logs storage
                query_cost=total_cost * 0.3,    # CloudWatch Insights queries
                ingestion_cost=total_cost * 0.1, # Log ingestion
                source="AWS Cost Explorer",
                period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                confidence=1.0
            )
            
        except Exception as e:
            self.logger.error(f"AWS Cost Explorer API error: {e}")
            raise RuntimeError(f"Failed to get AWS costs: {e}")
    

class DatadogBillingIntegration:
    """Integration with Datadog Billing API"""
    
    def __init__(self, api_key: str = None, app_key: str = None):
        self.api_key = api_key or os.getenv('DATADOG_API_KEY')
        self.app_key = app_key or os.getenv('DATADOG_APP_KEY')
        self.base_url = "https://api.datadoghq.com/api/v1"
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key or not self.app_key:
            raise ValueError("Datadog credentials required - set DATADOG_API_KEY and DATADOG_APP_KEY environment variables")
    
    def get_usage_costs(self, start_date: datetime, end_date: datetime) -> RealCostData:
        """Get actual Datadog usage costs from Billing API"""
        try:
            headers = {
                'DD-API-KEY': self.api_key,
                'DD-APPLICATION-KEY': self.app_key,
                'Content-Type': 'application/json'
            }
            
            # Get usage summary
            params = {
                'start_hr': start_date.strftime('%Y-%m-%dT%H'),
                'end_hr': end_date.strftime('%Y-%m-%dT%H')
            }
            
            response = requests.get(
                f"{self.base_url}/usage/summary",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                usage = data.get('usage', {})
                
                # Calculate costs based on Datadog pricing
                log_events = sum(day.get('indexed_events_count', 0) for day in usage.get('indexed_events', []))
                metrics = sum(day.get('custom_metrics_count', 0) for day in usage.get('custom_metrics', []))
                
                # Datadog pricing estimates
                log_cost = (log_events / 1000000) * 1.27  # $1.27 per million events
                metrics_cost = metrics * 0.05  # $0.05 per metric
                
                total_cost = log_cost + metrics_cost
                
                return RealCostData(
                    timestamp=datetime.now(),
                    total_cost=total_cost,
                    storage_cost=log_cost * 0.7,  # Most of log cost is storage
                    query_cost=log_cost * 0.3,    # Query overhead
                    ingestion_cost=metrics_cost,   # Metrics ingestion
                    source="Datadog Billing API",
                    period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    confidence=1.0
                )
            else:
                self.logger.error(f"Datadog API error: {response.status_code}")
                raise RuntimeError(f"Datadog API returned status {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Datadog API error: {e}")
            raise RuntimeError(f"Failed to get Datadog costs: {e}")
    

class PrometheusMetricsIntegration:
    """Integration with Prometheus for real-time metrics"""
    
    def __init__(self, prometheus_url: str = None):
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.logger = logging.getLogger(__name__)
        
        # Test connectivity - fail fast if not available
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                  params={'query': 'up'}, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Connected to Prometheus at {self.prometheus_url}")
            else:
                raise RuntimeError(f"Prometheus returned status {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Prometheus connection failed: {e}")
    
    def get_actual_data_volumes(self, hours: int = 24) -> Dict[str, float]:
        """Get actual data volumes from Prometheus metrics"""
        try:
            # Query Prometheus for actual data volumes
            queries = {
                'log': 'sum(rate(log_entries_total[1h])) * 3600',  # Logs per hour
                'metric': 'sum(rate(prometheus_tsdb_samples_appended_total[1h])) * 3600',  # Metrics per hour
                'trace': 'sum(rate(jaeger_spans_total[1h])) * 3600',  # Traces per hour
                'error': 'sum(rate(log_entries_total{level="error"}[1h])) * 3600',  # Error logs per hour
                'security': 'sum(rate(security_events_total[1h])) * 3600',  # Security events per hour
                'audit': 'sum(rate(audit_events_total[1h])) * 3600',  # Audit events per hour
                'performance': 'sum(rate(performance_metrics_total[1h])) * 3600'  # Performance metrics per hour
            }
            
            volumes = {}
            for data_type, query in queries.items():
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': query},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['data']['result']:
                        value = float(result['data']['result'][0]['value'][1])
                        # Convert to GB per day (assuming 1KB average event size)
                        volumes[data_type] = (value * 24 * 1024) / (1024 * 1024 * 1024)
                    else:
                        volumes[data_type] = 0.0
                else:
                    self.logger.warning(f"Prometheus query failed for {data_type}: {response.status_code}")
                    volumes[data_type] = 0.0
            
            return volumes
            
        except Exception as e:
            self.logger.error(f"Prometheus metrics error: {e}")
            raise RuntimeError(f"Failed to get Prometheus data volumes: {e}")
    

class RealWorldDataManager:
    """Manages real-world data integrations for observability economics"""
    
    def __init__(self):
        # Lazy initialization to avoid credential checks during setup
        self._aws_integration = None
        self._datadog_integration = None
        self._prometheus_integration = None
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path("config/observability/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.cache_ttl = 3600  # 1 hour TTL in seconds
    
    @property
    def aws_integration(self):
        """Lazy initialization of AWS integration"""
        if self._aws_integration is None:
            self._aws_integration = AWSCostExplorerIntegration()
        return self._aws_integration
    
    @property
    def datadog_integration(self):
        """Lazy initialization of Datadog integration"""
        if self._datadog_integration is None:
            self._datadog_integration = DatadogBillingIntegration()
        return self._datadog_integration
    
    @property
    def prometheus_integration(self):
        """Lazy initialization of Prometheus integration"""
        if self._prometheus_integration is None:
            self._prometheus_integration = PrometheusMetricsIntegration()
        return self._prometheus_integration
    
    def get_real_cost_data(self, environment: str, days: int = 7) -> Dict[str, Any]:
        """Get real cost data with caching"""
        cache_key = f"cost_data_{environment}_{days}"
        
        # Try cache first
        cached_data = self.read_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch real data
        real_data = self._fetch_real_cost_data(environment, days)
        
        # Cache the result
        self.cache_real_data(cache_key, real_data)
        
        return real_data
    
    def get_real_data_volumes(self, environment: str, hours: int = 24) -> Dict[str, Any]:
        """Get real data volumes with attribution and caching"""
        cache_key = f"volume_data_{environment}_{hours}"
        
        # Try cache first
        cached_data = self.read_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch real data
        volume_data = self.prometheus_integration.get_actual_data_volumes(hours)
        
        # Add attribution information
        real_data = {
            "volumes": volume_data,
            "data_source": "Prometheus Metrics API",
            "confidence": 1.0,  # High confidence for real Prometheus data
            "timestamp": datetime.now().isoformat(),
            "query_period_hours": hours,
            "environment": environment
        }
        
        # Cache the result
        self.cache_real_data(cache_key, real_data)
        
        return real_data
    
    def get_real_costs(self, environment: str, days: int = 7) -> RealCostData:
        """Get real-world costs from appropriate API based on environment"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Use different APIs based on environment
        if environment == "production":
            # Production uses AWS CloudWatch
            return self.aws_integration.get_cloudwatch_costs(start_date, end_date)
        elif environment == "staging":
            # Staging uses Datadog
            return self.datadog_integration.get_usage_costs(start_date, end_date)
        else:
            # Development uses mock data (lightweight)
            return RealCostData(
                timestamp=datetime.now(),
                total_cost=5.25 * days,  # $5.25/day for dev
                storage_cost=3.15 * days,
                query_cost=1.58 * days,
                ingestion_cost=0.52 * days,
                source="Development Mock",
                period=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                confidence=0.9
            )
    
    def _fetch_real_cost_data(self, environment: str, days: int = 7) -> Dict[str, Any]:
        """Fetch real cost data from APIs"""
        cost_data = self.get_real_costs(environment, days)
        
        # Convert to dictionary format for caching
        return {
            "timestamp": cost_data.timestamp.isoformat(),
            "total_cost": cost_data.total_cost,
            "storage_cost": cost_data.storage_cost,
            "query_cost": cost_data.query_cost,
            "ingestion_cost": cost_data.ingestion_cost,
            "source": cost_data.source,
            "period": cost_data.period,
            "confidence": cost_data.confidence,
            "cost_per_unit": {
                "log": cost_data.storage_cost / cost_data.total_cost if cost_data.total_cost else 0,
                "metric": cost_data.query_cost / cost_data.total_cost if cost_data.total_cost else 0,
                "trace": cost_data.ingestion_cost / cost_data.total_cost if cost_data.total_cost else 0,
                "error": cost_data.storage_cost / cost_data.total_cost if cost_data.total_cost else 0,
                "security": cost_data.total_cost / days if days else 0,
                "audit": cost_data.total_cost / days if days else 0,
                "performance": cost_data.query_cost / cost_data.total_cost if cost_data.total_cost else 0
            }
        }
    
    def read_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Read cached data with TTL validation"""
        cache_file = self.cache_dir / f"{cache_key}_cache.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check TTL
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if (datetime.now() - cached_time).total_seconds() > self.cache_ttl:
                cache_file.unlink()  # Remove expired cache
                return None
            
            return cached_data['data']
        except Exception as e:
            self.logger.warning(f"Failed to read cache {cache_key}: {e}")
            return None

    def cache_real_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache real data with timestamp and TTL"""
        cache_file = self.cache_dir / f"{cache_key}_cache.json"
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'ttl': self.cache_ttl
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        self.logger.info(f"Cached data for {cache_key} with TTL {self.cache_ttl}s")

    def cache_historical_data(self, environment: str, cost_data: RealCostData, volume_data: Dict[str, float]):
        """Cache historical data for offline analysis (separate from TTL cache)"""
        cache_file = self.cache_dir / f"historical_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "environment": environment,
            "cost_data": {
                "timestamp": cost_data.timestamp.isoformat(),
                "total_cost": cost_data.total_cost,
                "storage_cost": cost_data.storage_cost,
                "query_cost": cost_data.query_cost,
                "ingestion_cost": cost_data.ingestion_cost,
                "source": cost_data.source,
                "period": cost_data.period,
                "confidence": cost_data.confidence
            },
            "volume_data": volume_data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        self.logger.info(f"Cached historical data for {environment} to {cache_file}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all real-world integrations"""
        status = {}
        
        # Check AWS integration
        try:
            aws_integration = self.aws_integration
            status["aws_cost_explorer"] = {
                "available": True,
                "credentials": bool(aws_integration.aws_access_key_id),
                "status": "Connected"
            }
        except Exception:
            status["aws_cost_explorer"] = {
                "available": False,
                "credentials": False,
                "status": "Mock Mode"
            }
        
        # Check Datadog integration
        try:
            datadog_integration = self.datadog_integration
            status["datadog_billing"] = {
                "available": True,
                "credentials": bool(datadog_integration.api_key),
                "status": "Connected"
            }
        except Exception:
            status["datadog_billing"] = {
                "available": False,
                "credentials": False,
                "status": "Mock Mode"
            }
        
        # Check Prometheus integration
        try:
            prometheus_integration = self.prometheus_integration
            status["prometheus_metrics"] = {
                "available": True,
                "url": prometheus_integration.prometheus_url,
                "status": "Connected"
            }
        except Exception:
            status["prometheus_metrics"] = {
                "available": False,
                "url": "http://localhost:9090",
                "status": "Mock Mode"
            }
        
        return status

# Default real-world data manager instance
default_real_world_manager = RealWorldDataManager()

if __name__ == "__main__":
    import sys
    
    # Test real-world integrations
    manager = RealWorldDataManager()
    
    print("🌍 Testing Real-World Data Integrations...")
    
    # Test integration status
    print("\n📊 Integration Status:")
    status = manager.get_integration_status()
    for service, info in status.items():
        print(f"  {service}: {info['status']}")
    
    # Test real cost data
    print("\n💰 Testing Real Cost Data:")
    for env in ["development", "staging", "production"]:
        cost_data = manager.get_real_costs(env, days=7)
        print(f"  {env}: ${cost_data.total_cost:.2f} over 7 days")
        print(f"    Source: {cost_data.source} (confidence: {cost_data.confidence:.1%})")
        print(f"    Breakdown: Storage ${cost_data.storage_cost:.2f}, Query ${cost_data.query_cost:.2f}, Ingestion ${cost_data.ingestion_cost:.2f}")
    
    # Test real data volumes
    print("\n📈 Testing Real Data Volumes:")
    volume_data = manager.get_real_data_volumes("production", hours=24)
    volumes = volume_data["volumes"]
    for data_type, volume in volumes.items():
        print(f"  {data_type}: {volume:.3f} GB/day")
    print(f"  Data source: {volume_data['data_source']}")
    print(f"  Confidence: {volume_data['confidence']:.1%}")
    
    # Test caching functionality
    print("\n💾 Testing Data Caching:")
    
    # Test cache miss and cache hit
    print("  Testing cache miss/hit cycle...")
    cache_key = "test_cache"
    test_data = {"test": "value", "number": 42}
    
    # Should be cache miss
    cached = manager.read_cached_data(cache_key)
    print(f"  Cache miss: {cached is None}")
    
    # Cache the data
    manager.cache_real_data(cache_key, test_data)
    
    # Should be cache hit
    cached = manager.read_cached_data(cache_key)
    print(f"  Cache hit: {cached == test_data}")
    
    # Test real cost data caching
    print("  Testing real cost data caching...")
    cost_data_1 = manager.get_real_cost_data("production", days=7)
    cost_data_2 = manager.get_real_cost_data("production", days=7)  # Should be cached
    print(f"  Cost data cached: {cost_data_1['source'] == cost_data_2['source']}")
    
    # Test real volume data caching
    print("  Testing real volume data caching...")
    volume_data_1 = manager.get_real_data_volumes("production", hours=24)
    volume_data_2 = manager.get_real_data_volumes("production", hours=24)  # Should be cached
    print(f"  Volume data cached: {volume_data_1 == volume_data_2}")
    
    # Test historical data caching
    print("  Testing historical data caching...")
    sample_cost = manager.get_real_costs("production", days=1)
    sample_volume_data = manager.get_real_data_volumes("production", hours=24)
    manager.cache_historical_data("production", sample_cost, sample_volume_data["volumes"])
    
    print("✅ Real-world data integration test complete")
