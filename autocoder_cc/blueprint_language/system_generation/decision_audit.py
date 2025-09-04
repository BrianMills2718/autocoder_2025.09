#!/usr/bin/env python3
"""
Decision Audit - Emergency Refactoring from system_generator.py

Extracted from system_generator.py (lines 928-964)
Decision tracking and transparent analysis classes.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

from ..system_generation import (
    SystemRequirements,
)


@dataclass
class DecisionAudit:
    """Complete audit trail of decision-making process"""
    rules: List[Dict[str, Any]]
    final_selection: str = ""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, rule_name: str, reasoning: str, decision: str, confidence: float):
        self.rules.append({
            "rule_name": rule_name,
            "reasoning": reasoning,
            "decision": decision,
            "confidence": confidence
        })
    
    def get_highest_confidence_decision(self) -> str:
        if not self.rules:
            return "http"  # Safe default
        return max(self.rules, key=lambda r: r["confidence"])["decision"]
    
    def get_complete_evidence_trail(self) -> List[str]:
        return [f"{rule['rule_name']}: {rule['reasoning']} -> {rule['decision']} (confidence: {rule['confidence']})"
                for rule in self.rules]


@dataclass
class TransparentAnalysis:
    """Complete transparent analysis with full audit trail"""
    requirements: SystemRequirements
    decision_audit: DecisionAudit
    selected_type: str
    justification: Dict[str, Any]
    benchmark_citations: List[str]
    transparency_score: float