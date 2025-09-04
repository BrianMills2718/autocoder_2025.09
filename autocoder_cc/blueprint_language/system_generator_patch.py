#!/usr/bin/env python3
"""
Patch for system_generator.py to use live benchmark data
This module provides an enhanced TransparentMessagingAnalyzer
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import live benchmark collector
from .live_benchmark_collector import LiveIndustryBenchmarkCollector, LiveBenchmarkData
from .system_generator import (
    SystemRequirements, DecisionAudit, TransparentAnalysis,
    TransparentMessagingAnalyzer as OriginalAnalyzer
)


class EnhancedTransparentMessagingAnalyzer(OriginalAnalyzer):
    """Enhanced messaging analyzer that uses live benchmark data instead of hardcoded values"""
    
    def __init__(self):
        # Don't call parent __init__ to avoid hardcoded benchmarks
        self.benchmark_collector = LiveIndustryBenchmarkCollector()
        self._live_benchmarks: Optional[LiveBenchmarkData] = None
        self._last_collection_time: Optional[datetime] = None
    
    @property
    def VERIFIED_INDUSTRY_BENCHMARKS(self):
        """Override parent property to return live benchmark data"""
        # Ensure we have fresh benchmark data
        if self._live_benchmarks is None or self._should_refresh_benchmarks():
            self._refresh_benchmarks()
        
        # Convert live benchmarks to expected format
        result = {}
        for protocol, benchmark in self._live_benchmarks.benchmarks.items():
            perf_data = benchmark.performance_data
            result[protocol] = {
                "source": benchmark.source_name,
                "url": benchmark.source_url,
                "citation": f"{benchmark.source_name} (collected {benchmark.collected_at.strftime('%Y-%m-%d %H:%M UTC')})",
                "conditions": perf_data.get("conditions", "Standard test conditions"),
                "performance_envelope": perf_data.get("performance_envelope", {}),
                "optimal_use_cases": perf_data.get("optimal_use_cases", [])
            }
        
        return result
    
    def _should_refresh_benchmarks(self) -> bool:
        """Check if benchmarks should be refreshed"""
        if self._last_collection_time is None:
            return True
        
        # Refresh every hour
        age = datetime.utcnow() - self._last_collection_time
        return age.total_seconds() > 3600
    
    def _refresh_benchmarks(self):
        """Refresh benchmark data from live sources"""
        self._live_benchmarks = self.benchmark_collector.collect_live_benchmarks()
        self._last_collection_time = datetime.utcnow()
    
    def analyze_system_requirements_transparent(self, system_blueprint) -> TransparentAnalysis:
        """Override to ensure live data is used"""
        # Refresh benchmarks before analysis
        if self._should_refresh_benchmarks():
            self._refresh_benchmarks()
        
        # Call parent method which will now use our live benchmark property
        analysis = super().analyze_system_requirements_transparent(system_blueprint)
        
        # Add live data metadata to justification
        if self._live_benchmarks:
            analysis.justification["live_data_metadata"] = {
                "collection_timestamp": self._live_benchmarks.collection_timestamp.isoformat(),
                "all_sources_valid": all(v.is_valid for v in self._live_benchmarks.validation_results.values()),
                "data_freshness": "live" if not any(b.is_cached for b in self._live_benchmarks.benchmarks.values()) else "mixed"
            }
        
        return analysis
    
    def _get_all_citations(self) -> List[str]:
        """Override to provide live data citations"""
        if self._live_benchmarks:
            return [
                self._live_benchmarks.get_citation(protocol)
                for protocol in ["rabbitmq", "kafka", "http"]
            ]
        return super()._get_all_citations()


def patch_system_generator():
    """Monkey-patch the system generator to use live benchmark data"""
    import sys
    import importlib
    
    # Import the system_generator module
    if 'blueprint_language.system_generator' in sys.modules:
        sg_module = sys.modules['blueprint_language.system_generator']
    else:
        import blueprint_language.system_generator as sg_module
    
    # Replace the TransparentMessagingAnalyzer class
    sg_module.TransparentMessagingAnalyzer = EnhancedTransparentMessagingAnalyzer
    
    # Also patch the legacy wrapper
    sg_module.MessagingRequirementsAnalyzer = EnhancedTransparentMessagingAnalyzer
    
    print("✅ System generator patched to use live benchmark data")


def validate_live_benchmarks():
    """Validate that live benchmarks are working correctly"""
    print("Validating live benchmark system...")
    
    analyzer = EnhancedTransparentMessagingAnalyzer()
    
    # Force benchmark collection
    analyzer._refresh_benchmarks()
    
    print(f"\n📊 Benchmark Collection Results:")
    print(f"Collection Time: {analyzer._live_benchmarks.collection_timestamp}")
    
    print("\n✓ Validation Status:")
    for protocol, validation in analyzer._live_benchmarks.validation_results.items():
        status = "✅" if validation.is_valid else "❌"
        print(f"  {status} {protocol}: {validation.error or 'Valid'}")
    
    print("\n📈 Benchmark Data:")
    benchmarks = analyzer.VERIFIED_INDUSTRY_BENCHMARKS
    for protocol, data in benchmarks.items():
        print(f"\n{protocol.upper()}:")
        print(f"  Source: {data['source']}")
        print(f"  Citation: {data['citation']}")
        if 'performance_envelope' in data:
            print(f"  Performance: {data['performance_envelope']}")


if __name__ == "__main__":
    # Validate the live benchmark system
    validate_live_benchmarks()
    
    # Apply the patch
    patch_system_generator()
    
    print("\n✅ System generator enhancement complete!")
    print("The TransparentMessagingAnalyzer now uses live benchmark data instead of hardcoded values.")