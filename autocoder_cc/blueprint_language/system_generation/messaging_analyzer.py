#!/usr/bin/env python3
"""
Messaging Analyzer - Emergency Refactoring from system_generator.py

Extracted from system_generator.py:
- EvidenceBasedMessagingAnalyzer (lines 620-925)
- TransparentMessagingAnalyzer (lines 965-1256) 
- MessagingRequirementsAnalyzer (lines 1257-1282)

Evidence-based messaging analysis using live benchmark data.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

from ..system_generation import (
    BenchmarkCollectionError,
    SourceValidationError,
    SourceValidationResult,
    LiveBenchmarkData,
    EvidenceBasedAnalysis,
    SystemRequirements,
)
from .benchmark_collector import LiveIndustryBenchmarkCollector_LEGACY
from .decision_audit import DecisionAudit, TransparentAnalysis


class EvidenceBasedMessagingAnalyzer:
    """Messaging analysis using verifiable evidence and live benchmark data"""
    
    def __init__(self):
        self.benchmark_collector = LiveIndustryBenchmarkCollector_LEGACY()
        self.decision_audit_log = []
    
    def analyze_system_requirements_with_evidence(self, system_blueprint) -> EvidenceBasedAnalysis:
        """Perform evidence-based analysis with full audit trail and citations"""
        
        # Collect live benchmark data with validation
        live_benchmarks = self.benchmark_collector.collect_live_benchmarks()
        
        # Extract exact requirements from component configurations
        requirements = self._extract_measurable_requirements(system_blueprint)
        
        # Apply evidence-based decision rules with citations
        decision_result = self._apply_evidence_based_rules(requirements, live_benchmarks)
        
        # Generate complete justification with sources
        justification = self._generate_cited_justification(decision_result, live_benchmarks)
        
        return EvidenceBasedAnalysis(
            requirements=requirements,
            decision_result=decision_result,
            live_benchmarks=live_benchmarks,
            justification=justification,
            audit_trail=self.decision_audit_log,
            evidence_quality_score=self._calculate_evidence_quality(live_benchmarks)
        )
    
    def _extract_measurable_requirements(self, system_blueprint) -> SystemRequirements:
        """Extract exact, measurable requirements from component configurations"""
        
        requirements = SystemRequirements()
        
        # Extract explicit volume requirements
        for component in system_blueprint.system.components:
            config = component.config or {}
            
            # Look for explicit throughput specifications
            if "throughput" in config:
                requirements.message_volume += config["throughput"]
                requirements.volume_source = "explicit_config"
            elif "messages_per_second" in config:
                requirements.message_volume += config["messages_per_second"]
                requirements.volume_source = "explicit_config"
            else:
                # NO ESTIMATION - mark as unknown
                requirements.volume_source = "unknown"
                
            # Look for explicit latency requirements
            if "max_latency" in config:
                requirements.max_latency = min(requirements.max_latency, config["max_latency"])
                requirements.latency_source = "explicit_config"
            elif "timeout" in config:
                requirements.max_latency = min(requirements.max_latency, config["timeout"])
                requirements.latency_source = "timeout_inference"
            else:
                requirements.latency_source = "unknown"
                
            # Look for explicit messaging type preference
            if "messaging_type" in config:
                requirements.explicit_messaging_type = config["messaging_type"]
                
            # Look for explicit durability requirements
            if "durability" in config:
                requirements.durability_required = config["durability"]
            elif "persistent" in config:
                requirements.durability_required = config["persistent"]
                
        return requirements
    
    def _apply_evidence_based_rules(self, requirements: SystemRequirements, live_benchmarks: LiveBenchmarkData) -> Dict[str, Any]:
        """Apply evidence-based decision rules with complete audit trail"""
        
        # Clear previous audit log
        self.decision_audit_log = []
        
        # Rule 1: Check explicit messaging requirements
        if requirements.explicit_messaging_type:
            decision = {
                "rule_name": "explicit_requirement",
                "reasoning": f"System explicitly requires {requirements.explicit_messaging_type}",
                "selected_type": requirements.explicit_messaging_type,
                "confidence": 1.0,
                "evidence_sources": ["component_configuration"]
            }
            self.decision_audit_log.append(decision)
            return decision
        
        # Rule 2: Volume-based selection using live benchmarks
        volume_decision = self._evaluate_volume_with_live_data(requirements, live_benchmarks)
        self.decision_audit_log.append(volume_decision)
        
        # Rule 3: Latency-based selection using live benchmarks
        latency_decision = self._evaluate_latency_with_live_data(requirements, live_benchmarks)
        self.decision_audit_log.append(latency_decision)
        
        # Rule 4: Pattern-based selection using industry best practices
        pattern_decision = self._evaluate_communication_patterns(requirements)
        self.decision_audit_log.append(pattern_decision)
        
        # Final selection based on highest confidence rule
        highest_confidence_decision = max(self.decision_audit_log, key=lambda x: x["confidence"])
        
        return {
            "selected_type": highest_confidence_decision["selected_type"],
            "primary_rule": highest_confidence_decision["rule_name"],
            "confidence": highest_confidence_decision["confidence"],
            "all_rules": self.decision_audit_log
        }
    
    def _evaluate_volume_with_live_data(self, requirements: SystemRequirements, live_benchmarks: LiveBenchmarkData) -> Dict[str, Any]:
        """Evaluate volume requirements using live benchmark data"""
        
        if requirements.volume_source == "unknown" or requirements.message_volume == 0:
            return {
                "rule_name": "volume_analysis",
                "reasoning": "No explicit volume requirements found in component configurations. Using HTTP as safe default for unknown loads.",
                "selected_type": "http",
                "confidence": 0.5,
                "evidence_sources": ["default_policy"]
            }
        
        volume = requirements.message_volume
        
        # Use live benchmarks for decision
        kafka_benchmarks = live_benchmarks.benchmarks.get("kafka", {}).get("performance_envelope", {})
        rabbitmq_benchmarks = live_benchmarks.benchmarks.get("rabbitmq", {}).get("performance_envelope", {})
        http_benchmarks = live_benchmarks.benchmarks.get("http", {}).get("performance_envelope", {})
        
        # Extract values from live data with explicit error handling
        try:
            kafka_min = kafka_benchmarks["high_throughput"]["min"]
            rabbitmq_typical = rabbitmq_benchmarks["small_messages_1kb"]["typical"]
            http_typical = http_benchmarks["rest_api_calls"]["typical"]
        except KeyError as e:
            raise BenchmarkCollectionError(
                f"CRITICAL: Missing required benchmark data for volume analysis: {e}. "
                f"Live benchmark data structure is incomplete."
            )
        
        # Data quality is always 1.0 since we only accept live data
        base_confidence = 1.0
        
        if volume >= kafka_min:
            return {
                "rule_name": "volume_analysis",
                "reasoning": f"High volume requirement ({volume} msg/s) exceeds Kafka minimum threshold ({kafka_min} msg/s) from live benchmark data",
                "selected_type": "kafka",
                "confidence": 0.9 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "kafka_performance_envelope"]
            }
        elif volume >= rabbitmq_typical:
            return {
                "rule_name": "volume_analysis",
                "reasoning": f"Medium volume requirement ({volume} msg/s) fits RabbitMQ typical capacity ({rabbitmq_typical} msg/s) from live benchmark data",
                "selected_type": "rabbitmq",
                "confidence": 0.8 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "rabbitmq_performance_envelope"]
            }
        else:
            return {
                "rule_name": "volume_analysis",
                "reasoning": f"Low volume requirement ({volume} msg/s) within HTTP capacity ({http_typical} msg/s) from live benchmark data",
                "selected_type": "http",
                "confidence": 0.7 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "http_performance_envelope"]
            }
    
    def _evaluate_latency_with_live_data(self, requirements: SystemRequirements, live_benchmarks: LiveBenchmarkData) -> Dict[str, Any]:
        """Evaluate latency requirements using live benchmark data"""
        
        if requirements.latency_source == "unknown" or requirements.max_latency == float('inf'):
            return {
                "rule_name": "latency_analysis",
                "reasoning": "No explicit latency requirements found. Using HTTP as reasonable default for typical web applications.",
                "selected_type": "http",
                "confidence": 0.4,
                "evidence_sources": ["default_policy"]
            }
        
        latency = requirements.max_latency
        
        # Use ONLY live benchmarks for decision - fail if data missing
        kafka_benchmarks = live_benchmarks.benchmarks.get("kafka", {}).get("performance_envelope", {})
        http_benchmarks = live_benchmarks.benchmarks.get("http", {}).get("performance_envelope", {})
        
        # Extract values from live data with explicit error handling
        try:
            kafka_p99 = kafka_benchmarks["low_latency_p99"]["max"]
            http_max = http_benchmarks["max_acceptable_latency"]
        except KeyError as e:
            raise BenchmarkCollectionError(
                f"CRITICAL: Missing required benchmark data for latency analysis: {e}. "
                f"Live benchmark data structure is incomplete."
            )
        
        # Data quality is always 1.0 since we only accept live data
        base_confidence = 1.0
        
        if latency <= kafka_p99:
            return {
                "rule_name": "latency_analysis",
                "reasoning": f"Very low latency requirement ({latency}ms) within Kafka p99 latency ({kafka_p99}ms) from live benchmark data",
                "selected_type": "kafka",
                "confidence": 0.8 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "kafka_latency_metrics"]
            }
        elif latency <= http_max:
            return {
                "rule_name": "latency_analysis",
                "reasoning": f"Moderate latency requirement ({latency}ms) acceptable for HTTP ({http_max}ms max) from live benchmark data",
                "selected_type": "http",
                "confidence": 0.7 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "http_latency_metrics"]
            }
        else:
            return {
                "rule_name": "latency_analysis",
                "reasoning": f"Relaxed latency requirement ({latency}ms) allows any messaging type. Choosing RabbitMQ for reliability.",
                "selected_type": "rabbitmq",
                "confidence": 0.6 * base_confidence,
                "evidence_sources": ["live_benchmark_data", "reliability_policy"]
            }
    
    def _evaluate_communication_patterns(self, requirements: SystemRequirements) -> Dict[str, Any]:
        """Evaluate communication patterns using industry best practices"""
        
        if requirements.durability_required and requirements.consistency_required:
            return {
                "rule_name": "pattern_analysis",
                "reasoning": "System requires both durability and consistency. RabbitMQ provides strong message persistence and ordering guarantees.",
                "selected_type": "rabbitmq",
                "confidence": 0.9,
                "evidence_sources": ["durability_requirements", "consistency_requirements"]
            }
        
        if "streaming" in requirements.communication_patterns:
            return {
                "rule_name": "pattern_analysis",
                "reasoning": "System has streaming communication patterns. Kafka is optimized for high-throughput event streaming.",
                "selected_type": "kafka",
                "confidence": 0.8,
                "evidence_sources": ["communication_patterns", "streaming_optimization"]
            }
        
        if "request_response" in requirements.communication_patterns:
            return {
                "rule_name": "pattern_analysis",
                "reasoning": "System has request-response patterns. HTTP is ideal for synchronous communication.",
                "selected_type": "http",
                "confidence": 0.8,
                "evidence_sources": ["communication_patterns", "synchronous_optimization"]
            }
        
        return {
            "rule_name": "pattern_analysis",
            "reasoning": "No specific communication patterns identified. Using HTTP as versatile default.",
            "selected_type": "http",
            "confidence": 0.5,
            "evidence_sources": ["default_policy"]
        }
    
    def _generate_cited_justification(self, decision_result: Dict[str, Any], live_benchmarks: LiveBenchmarkData) -> Dict[str, Any]:
        """Generate complete, citable justification for messaging type selection"""
        
        return {
            "benchmark_sources": self._get_all_benchmark_sources(live_benchmarks),
            "decision_rules_applied": decision_result.get("all_rules", []),
            "data_quality_assessment": {
                "overall_score": live_benchmarks.data_quality_score,
                "collection_timestamp": live_benchmarks.collection_timestamp.isoformat(),
                "source_validation_results": {
                    protocol: {
                        "is_valid": result.is_valid,
                        "error": result.error,
                        "timestamp": result.timestamp.isoformat() if result.timestamp else None
                    }
                    for protocol, result in live_benchmarks.validation_results.items()
                }
            },
            "selected_messaging_type": decision_result["selected_type"],
            "primary_decision_rule": decision_result["primary_rule"],
            "confidence_score": decision_result["confidence"],
            "evidence_trail": [rule["reasoning"] for rule in decision_result.get("all_rules", [])]
        }
    
    def _get_all_benchmark_sources(self, live_benchmarks: LiveBenchmarkData) -> List[Dict[str, str]]:
        """Get all benchmark sources with validation status"""
        sources = []
        for protocol, source_config in live_benchmarks.data_sources.items():
            validation_result = live_benchmarks.validation_results.get(protocol)
            sources.append({
                "protocol": protocol,
                "source_url": source_config.get("api_endpoint", "unknown"),
                "validation_status": "valid" if validation_result and validation_result.is_valid else "fallback",
                "data_quality": "live" if validation_result and validation_result.is_valid else "backup"
            })
        return sources
    
    def _calculate_evidence_quality(self, live_benchmarks: LiveBenchmarkData) -> float:
        """Calculate overall evidence quality score"""
        return live_benchmarks.data_quality_score


class TransparentMessagingAnalyzer:
    """Messaging type selection with fully transparent, citation-based decisions using live data"""
    
    def __init__(self):
        # Initialize evidence-based analyzer with live benchmark collection
        self.evidence_analyzer = EvidenceBasedMessagingAnalyzer()
    
    def analyze_system_requirements_transparent(self, system_blueprint) -> TransparentAnalysis:
        """Perform comprehensive analysis using live evidence-based system"""
        
        # Use evidence-based analyzer for complete live analysis
        evidence_analysis = self.evidence_analyzer.analyze_system_requirements_with_evidence(system_blueprint)
        
        # Convert to legacy TransparentAnalysis format for compatibility
        decision_audit = DecisionAudit()
        decision_audit.final_selection = evidence_analysis.decision_result["selected_type"]
        
        # Convert evidence audit trail to decision audit format
        for rule in evidence_analysis.audit_trail:
            decision_audit.add_rule(
                rule_name=rule["rule_name"],
                reasoning=rule["reasoning"],
                decision=rule["selected_type"],
                confidence=rule["confidence"]
            )
        
        return TransparentAnalysis(
            requirements=evidence_analysis.requirements,
            decision_audit=decision_audit,
            selected_type=evidence_analysis.decision_result["selected_type"],
            justification=evidence_analysis.justification,
            benchmark_citations=self._extract_citations_from_evidence(evidence_analysis),
            transparency_score=evidence_analysis.evidence_quality_score
        )
    
    def _extract_citations_from_evidence(self, evidence_analysis: EvidenceBasedAnalysis) -> List[str]:
        """Extract citations from live evidence analysis"""
        citations = []
        for source in evidence_analysis.justification.get("benchmark_sources", []):
            citation = f"{source['protocol'].upper()} - {source['source_url']} (Quality: {source['data_quality']})"
            citations.append(citation)
        return citations


# Legacy method for compatibility
class MessagingRequirementsAnalyzer(TransparentMessagingAnalyzer):
    """Legacy wrapper for backward compatibility"""
    
    def analyze_system_requirements(self, system_blueprint):
        """Legacy method - converts to new transparent analysis"""
        transparent_analysis = self.analyze_system_requirements_transparent(system_blueprint)
        
        # Convert to legacy format for compatibility
        return type('MessagingAnalysis', (), {
            'selected_type': transparent_analysis.selected_type,
            'justification': transparent_analysis.justification,
            'benchmark_comparison': {
                'citations': transparent_analysis.benchmark_citations,
                'selected_benchmark': {
                    'type': transparent_analysis.selected_type
                }
            },
            'confidence_score': transparent_analysis.justification['confidence_assessment']['overall_confidence'],
            'decision_evidence': {
                'requirements': transparent_analysis.requirements,
                'decision_audit': transparent_analysis.decision_audit
            }
        })()