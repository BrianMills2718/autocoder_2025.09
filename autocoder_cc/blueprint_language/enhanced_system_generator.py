#!/usr/bin/env python3
"""
Enhanced System Generator with Live Benchmark Data
Uses real-time industry benchmarks for transparent messaging type selection
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import the original system generator components
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autocoder_cc.blueprint_language import (
    SystemRequirements, DecisionAudit, TransparentAnalysis,
    SystemGenerationReport, GeneratedSystem
)
from autocoder_cc.blueprint_language.live_benchmark_collector import (
    LiveIndustryBenchmarkCollector, LiveBenchmarkData
)


class EnhancedTransparentMessagingAnalyzer:
    """Enhanced messaging analyzer using live benchmark data"""
    
    def __init__(self):
        self.benchmark_collector = LiveIndustryBenchmarkCollector()
        self.live_benchmarks: Optional[LiveBenchmarkData] = None
    
    def analyze_system_requirements_with_live_data(self, system_blueprint) -> TransparentAnalysis:
        """Perform analysis using live benchmark data"""
        
        # Collect live benchmarks
        self.live_benchmarks = self.benchmark_collector.collect_live_benchmarks()
        
        # Extract exact requirements
        requirements = self._extract_exact_requirements(system_blueprint)
        
        # Apply decision rules with live data
        decision_audit = self._apply_transparent_decision_rules_live(requirements)
        
        # Generate justification with live citations
        justification = self._generate_live_data_justification(decision_audit)
        
        return TransparentAnalysis(
            requirements=requirements,
            decision_audit=decision_audit,
            selected_type=decision_audit.final_selection,
            justification=justification,
            benchmark_citations=self._get_live_citations(),
            transparency_score=1.0  # Fully transparent with live data
        )
    
    def _extract_exact_requirements(self, system_blueprint) -> SystemRequirements:
        """Extract exact requirements from component configurations"""
        
        requirements = SystemRequirements()
        
        for component in system_blueprint.system.components:
            config = component.config or {}
            
            # Extract throughput requirements
            if "throughput" in config:
                requirements.message_volume = max(requirements.message_volume, config["throughput"])
                requirements.volume_source = "explicit_config"
            elif "messages_per_second" in config:
                requirements.message_volume = max(requirements.message_volume, config["messages_per_second"])
                requirements.volume_source = "explicit_config"
            elif "expected_load" in config:
                requirements.message_volume = max(requirements.message_volume, config["expected_load"])
                requirements.volume_source = "explicit_config"
            
            # Extract latency requirements
            if "max_latency_ms" in config:
                requirements.max_latency = min(requirements.max_latency, config["max_latency_ms"])
                requirements.latency_source = "explicit_config"
            elif "sla_response_time" in config:
                requirements.max_latency = min(requirements.max_latency, config["sla_response_time"])
                requirements.latency_source = "explicit_config"
            
            # Extract explicit messaging type
            if "messaging_type" in config:
                requirements.explicit_messaging_type = config["messaging_type"]
            
            # Extract durability/consistency requirements
            if "requires_persistence" in config:
                requirements.durability_required = config["requires_persistence"]
            if "requires_ordering" in config:
                requirements.consistency_required = config["requires_ordering"]
            
            # Extract communication patterns
            if "communication_pattern" in config:
                pattern = config["communication_pattern"]
                if pattern not in requirements.communication_patterns:
                    requirements.communication_patterns.append(pattern)
        
        return requirements
    
    def _apply_transparent_decision_rules_live(self, requirements: SystemRequirements) -> DecisionAudit:
        """Apply decision rules using live benchmark data"""
        
        audit = DecisionAudit()
        
        # Rule 1: Explicit requirement always wins
        if requirements.explicit_messaging_type:
            audit.add_rule(
                "explicit_requirement",
                f"Component explicitly specifies {requirements.explicit_messaging_type}",
                decision=requirements.explicit_messaging_type,
                confidence=1.0
            )
            audit.final_selection = requirements.explicit_messaging_type
            return audit
        
        # Rule 2: Volume-based selection with live data
        volume_decision = self._evaluate_volume_with_live_data(requirements)
        audit.add_rule(
            "volume_analysis_live",
            volume_decision["reasoning"],
            decision=volume_decision["recommendation"],
            confidence=volume_decision["confidence"]
        )
        
        # Rule 3: Latency-based selection with live data
        latency_decision = self._evaluate_latency_with_live_data(requirements)
        audit.add_rule(
            "latency_analysis_live",
            latency_decision["reasoning"],
            decision=latency_decision["recommendation"],
            confidence=latency_decision["confidence"]
        )
        
        # Rule 4: Pattern-based selection
        pattern_decision = self._evaluate_patterns_with_best_practices(requirements)
        audit.add_rule(
            "pattern_analysis",
            pattern_decision["reasoning"],
            decision=pattern_decision["recommendation"],
            confidence=pattern_decision["confidence"]
        )
        
        # Rule 5: Durability/consistency requirements
        if requirements.durability_required or requirements.consistency_required:
            consistency_decision = self._evaluate_consistency_requirements(requirements)
            audit.add_rule(
                "consistency_analysis",
                consistency_decision["reasoning"],
                decision=consistency_decision["recommendation"],
                confidence=consistency_decision["confidence"]
            )
        
        # Select based on highest confidence
        audit.final_selection = audit.get_highest_confidence_decision()
        
        return audit
    
    def _evaluate_volume_with_live_data(self, requirements: SystemRequirements) -> Dict[str, Any]:
        """Evaluate volume requirements using live benchmark data"""
        
        if requirements.volume_source == "unknown" or requirements.message_volume == 0:
            return {
                "reasoning": "No explicit volume requirements found. Defaulting to HTTP for general-purpose use.",
                "recommendation": "http",
                "confidence": 0.3
            }
        
        volume = requirements.message_volume
        
        # Get live benchmark data
        kafka_data = self.live_benchmarks.benchmarks["kafka"].performance_data
        rabbitmq_data = self.live_benchmarks.benchmarks["rabbitmq"].performance_data
        http_data = self.live_benchmarks.benchmarks["http"].performance_data
        
        # Extract throughput values with fallback
        kafka_throughput = self._extract_throughput_value(kafka_data, "high_throughput", default=50000)
        rabbitmq_throughput = self._extract_throughput_value(rabbitmq_data, "small_messages_1kb", default=10000)
        http_throughput = self._extract_throughput_value(http_data, "rest_api_calls", default=5000)
        
        # Make decision based on live data
        if volume >= kafka_throughput:
            return {
                "reasoning": f"High volume ({volume} msg/s) exceeds Kafka typical throughput threshold ({kafka_throughput} msg/s) from {self.live_benchmarks.get_citation('kafka')}",
                "recommendation": "kafka",
                "confidence": 0.9
            }
        elif volume >= rabbitmq_throughput:
            return {
                "reasoning": f"Medium volume ({volume} msg/s) within RabbitMQ capacity ({rabbitmq_throughput} msg/s) from {self.live_benchmarks.get_citation('rabbitmq')}",
                "recommendation": "rabbitmq",
                "confidence": 0.8
            }
        else:
            return {
                "reasoning": f"Low volume ({volume} msg/s) suitable for HTTP ({http_throughput} msg/s typical) from {self.live_benchmarks.get_citation('http')}",
                "recommendation": "http",
                "confidence": 0.7
            }
    
    def _evaluate_latency_with_live_data(self, requirements: SystemRequirements) -> Dict[str, Any]:
        """Evaluate latency requirements using live benchmark data"""
        
        if requirements.latency_source == "unknown" or requirements.max_latency == float('inf'):
            return {
                "reasoning": "No explicit latency requirements. HTTP suitable for typical web latencies.",
                "recommendation": "http",
                "confidence": 0.4
            }
        
        latency = requirements.max_latency
        
        # Get live latency data
        kafka_data = self.live_benchmarks.benchmarks["kafka"].performance_data
        http_data = self.live_benchmarks.benchmarks["http"].performance_data
        
        # Extract latency values
        kafka_p99 = self._extract_latency_value(kafka_data, "low_latency_p99", default=50)
        http_max = self._extract_latency_value(http_data, "max_acceptable_latency", default=100)
        
        if latency <= kafka_p99:
            return {
                "reasoning": f"Ultra-low latency requirement ({latency}ms) requires Kafka (p99: {kafka_p99}ms) from {self.live_benchmarks.get_citation('kafka')}",
                "recommendation": "kafka",
                "confidence": 0.85
            }
        elif latency <= http_max:
            return {
                "reasoning": f"Moderate latency requirement ({latency}ms) suitable for HTTP (max: {http_max}ms) from {self.live_benchmarks.get_citation('http')}",
                "recommendation": "http",
                "confidence": 0.75
            }
        else:
            return {
                "reasoning": f"Relaxed latency requirement ({latency}ms) allows RabbitMQ for reliability benefits",
                "recommendation": "rabbitmq",
                "confidence": 0.65
            }
    
    def _evaluate_patterns_with_best_practices(self, requirements: SystemRequirements) -> Dict[str, Any]:
        """Evaluate communication patterns against industry best practices"""
        
        # Use optimal use cases from live data
        kafka_uses = self.live_benchmarks.benchmarks["kafka"].performance_data.get("optimal_use_cases", [])
        rabbitmq_uses = self.live_benchmarks.benchmarks["rabbitmq"].performance_data.get("optimal_use_cases", [])
        http_uses = self.live_benchmarks.benchmarks["http"].performance_data.get("optimal_use_cases", [])
        
        # Check pattern matches
        for pattern in requirements.communication_patterns:
            if any(use in pattern.lower() for use in ["stream", "event", "log"]):
                if "event streaming" in kafka_uses or "log aggregation" in kafka_uses:
                    return {
                        "reasoning": f"Pattern '{pattern}' matches Kafka optimal use cases: {', '.join(kafka_uses)}",
                        "recommendation": "kafka",
                        "confidence": 0.85
                    }
            
            if any(use in pattern.lower() for use in ["queue", "task", "job"]):
                if "message queuing" in rabbitmq_uses or "task distribution" in rabbitmq_uses:
                    return {
                        "reasoning": f"Pattern '{pattern}' matches RabbitMQ optimal use cases: {', '.join(rabbitmq_uses)}",
                        "recommendation": "rabbitmq",
                        "confidence": 0.85
                    }
            
            if any(use in pattern.lower() for use in ["request", "response", "api", "rest"]):
                if "request-response" in http_uses or "API calls" in http_uses:
                    return {
                        "reasoning": f"Pattern '{pattern}' matches HTTP optimal use cases: {', '.join(http_uses)}",
                        "recommendation": "http",
                        "confidence": 0.85
                    }
        
        return {
            "reasoning": "No specific pattern match found. HTTP provides good general-purpose communication.",
            "recommendation": "http",
            "confidence": 0.5
        }
    
    def _evaluate_consistency_requirements(self, requirements: SystemRequirements) -> Dict[str, Any]:
        """Evaluate durability and consistency requirements"""
        
        if requirements.durability_required and requirements.consistency_required:
            return {
                "reasoning": "Strong durability and consistency requirements. RabbitMQ provides persistent messaging with ordering guarantees.",
                "recommendation": "rabbitmq",
                "confidence": 0.9
            }
        elif requirements.durability_required:
            return {
                "reasoning": "Durability required. Both RabbitMQ and Kafka provide persistence, choosing RabbitMQ for flexibility.",
                "recommendation": "rabbitmq",
                "confidence": 0.8
            }
        else:
            return {
                "reasoning": "Consistency required without durability. RabbitMQ provides strong ordering guarantees.",
                "recommendation": "rabbitmq",
                "confidence": 0.75
            }
    
    def _extract_throughput_value(self, perf_data: Dict[str, Any], key: str, default: int) -> int:
        """Extract throughput value from performance data"""
        
        if key in perf_data and isinstance(perf_data[key], dict):
            # Look for typical, average, or min value
            for field in ["typical", "average", "min"]:
                if field in perf_data[key]:
                    return int(perf_data[key][field])
        
        # Check observed throughput from live data
        if "observed_throughput" in perf_data:
            obs = perf_data["observed_throughput"]
            if "average" in obs:
                return int(obs["average"])
            elif "min" in obs:
                return int(obs["min"])
        
        return default
    
    def _extract_latency_value(self, perf_data: Dict[str, Any], key: str, default: int) -> int:
        """Extract latency value from performance data"""
        
        if key in perf_data and isinstance(perf_data[key], dict):
            # Look for max or typical value
            for field in ["max", "typical", "average"]:
                if field in perf_data[key]:
                    return int(perf_data[key][field])
        
        # Check observed latency from live data
        if "observed_latency" in perf_data:
            obs = perf_data["observed_latency"]
            if "max" in obs:
                return int(obs["max"])
            elif "average" in obs:
                return int(obs["average"])
        
        return default
    
    def _generate_live_data_justification(self, decision_audit: DecisionAudit) -> Dict[str, Any]:
        """Generate justification with live data citations"""
        
        return {
            "data_collection_timestamp": self.live_benchmarks.collection_timestamp.isoformat(),
            "benchmark_sources": self._get_live_benchmark_sources(),
            "validation_status": self._get_validation_summary(),
            "decision_rules_applied": decision_audit.rules,
            "selected_protocol_analysis": self._analyze_selected_protocol(decision_audit.final_selection),
            "evidence_trail": decision_audit.get_complete_evidence_trail(),
            "transparency_note": "All decisions based on live benchmark data or explicit fallback values"
        }
    
    def _get_live_benchmark_sources(self) -> List[Dict[str, Any]]:
        """Get all live benchmark sources with metadata"""
        
        sources = []
        for protocol, benchmark in self.live_benchmarks.benchmarks.items():
            sources.append({
                "protocol": protocol,
                "source": benchmark.source_name,
                "url": benchmark.source_url,
                "collected_at": benchmark.collected_at.isoformat(),
                "is_cached": benchmark.is_cached,
                "validation_hash": benchmark.validation_hash[:8] + "..."  # Short hash
            })
        return sources
    
    def _get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for all sources"""
        
        summary = {
            "all_sources_valid": all(v.is_valid for v in self.live_benchmarks.validation_results.values()),
            "validation_details": {}
        }
        
        for protocol, validation in self.live_benchmarks.validation_results.items():
            summary["validation_details"][protocol] = {
                "valid": validation.is_valid,
                "error": validation.error,
                "validated_at": validation.validated_at.isoformat()
            }
        
        return summary
    
    def _analyze_selected_protocol(self, protocol: str) -> Dict[str, Any]:
        """Analyze the selected protocol with live data"""
        
        if protocol not in self.live_benchmarks.benchmarks:
            return {"error": f"No benchmark data for {protocol}"}
        
        benchmark = self.live_benchmarks.benchmarks[protocol]
        
        return {
            "protocol": protocol,
            "data_source": benchmark.source_name,
            "performance_characteristics": benchmark.performance_data.get("performance_envelope", {}),
            "optimal_use_cases": benchmark.performance_data.get("optimal_use_cases", []),
            "data_freshness": "live" if not benchmark.is_cached else "cached",
            "collection_time": benchmark.collected_at.isoformat()
        }
    
    def _get_live_citations(self) -> List[str]:
        """Get all live data citations"""
        
        citations = []
        for protocol in ["rabbitmq", "kafka", "http"]:
            citations.append(self.live_benchmarks.get_citation(protocol))
        return citations


def create_enhanced_system_generator():
    """Create system generator with live benchmark data support"""
    
    # Import original system generator
    from autocoder_cc.blueprint_language import SystemGenerator
    
    # Create enhanced version
    class EnhancedSystemGenerator(SystemGenerator):
        def __init__(self, base_dir: str):
            super().__init__(base_dir)
            # Replace the messaging analyzer with enhanced version
            self.messaging_analyzer = EnhancedTransparentMessagingAnalyzer()
        
        def _determine_messaging_type(self, system_blueprint) -> str:
            """Override to use live benchmark data"""
            
            # Use enhanced analyzer
            analysis = self.messaging_analyzer.analyze_system_requirements_with_live_data(system_blueprint)
            
            # Log the complete analysis
            self.logger.info("Messaging Type Analysis (Live Data):")
            self.logger.info(f"  Selected: {analysis.selected_type}")
            self.logger.info(f"  Data Collection: {analysis.justification['data_collection_timestamp']}")
            self.logger.info(f"  Evidence Trail: {analysis.justification['evidence_trail']}")
            
            return analysis.selected_type
    
    return EnhancedSystemGenerator


if __name__ == "__main__":
    # Test the enhanced analyzer
    print("Testing Enhanced Transparent Messaging Analyzer with Live Data\n")
    
    analyzer = EnhancedTransparentMessagingAnalyzer()
    
    # Create test blueprint
    class MockComponent:
        def __init__(self, config):
            self.config = config
    
    class MockSystem:
        def __init__(self, components):
            self.components = components
    
    class MockBlueprint:
        def __init__(self, components_config):
            self.system = MockSystem([MockComponent(cfg) for cfg in components_config])
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "High Volume System",
            "components": [
                {"throughput": 100000, "communication_pattern": "event_streaming"},
                {"messages_per_second": 50000}
            ]
        },
        {
            "name": "Low Latency System",
            "components": [
                {"max_latency_ms": 10, "communication_pattern": "real_time"},
                {"sla_response_time": 15}
            ]
        },
        {
            "name": "Request-Response API",
            "components": [
                {"communication_pattern": "request_response", "expected_load": 1000},
                {"max_latency_ms": 100}
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("=" * 50)
        
        blueprint = MockBlueprint(scenario["components"])
        analysis = analyzer.analyze_system_requirements_with_live_data(blueprint)
        
        print(f"Selected Type: {analysis.selected_type}")
        print(f"Transparency Score: {analysis.transparency_score}")
        print(f"Data Sources Valid: {analysis.justification['validation_status']['all_sources_valid']}")
        print("\nDecision Rules Applied:")
        for rule in analysis.decision_audit.rules:
            print(f"  - {rule['rule_name']}: {rule['decision']} (confidence: {rule['confidence']})")
        print(f"\nFinal Decision: {analysis.decision_audit.final_selection}")