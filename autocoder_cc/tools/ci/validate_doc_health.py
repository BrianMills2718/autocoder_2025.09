#!/usr/bin/env python3
"""
Documentation Health Score Validator for CI/CD
Validates documentation health score against configurable thresholds
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any


class DocumentationHealthValidator:
    """Validates documentation health scores with configurable thresholds"""
    
    DEFAULT_HEALTH_THRESHOLD = 90
    DEFAULT_HIGH_ISSUES_THRESHOLD = 0
    
    def __init__(self, health_threshold: int = None, high_issues_threshold: int = None):
        self.health_threshold = health_threshold or self.DEFAULT_HEALTH_THRESHOLD
        self.high_issues_threshold = high_issues_threshold or self.DEFAULT_HIGH_ISSUES_THRESHOLD
        
    def validate_health_report(self, report_file: str) -> bool:
        """
        Validates documentation health report against thresholds
        
        Args:
            report_file: Path to JSON health report
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            report_path = Path(report_file)
            if not report_path.exists():
                print(f"::error ::Health report file not found: {report_file}")
                return False
                
            with open(report_path, 'r') as f:
                data = json.load(f)
                
            return self._validate_report_data(data)
            
        except json.JSONDecodeError as e:
            print(f"::error ::Invalid JSON in health report: {e}")
            return False
        except Exception as e:
            print(f"::error ::Error reading health report: {e}")
            return False
            
    def _validate_report_data(self, data: Dict[str, Any]) -> bool:
        """Validates the actual report data"""
        score = data.get('health_score', 0)
        high_issues = data.get('statistics', {}).get('high_issues', 0)
        
        print(f"📊 Health score: {score}")
        print(f"⚠️  High priority issues: {high_issues}")
        print(f"🎯 Required health score: ≥{self.health_threshold}")
        print(f"🎯 Max high priority issues: ≤{self.high_issues_threshold}")
        
        validation_passed = True
        
        if score < self.health_threshold:
            print(f"::error ::Documentation health score {score} below threshold ({self.health_threshold})")
            validation_passed = False
            
        if high_issues > self.high_issues_threshold:
            print(f"::error ::{high_issues} high priority documentation issues detected (max: {self.high_issues_threshold})")
            validation_passed = False
            
        if validation_passed:
            print("✅ Documentation health check passed")
        else:
            print("❌ Documentation health check failed")
            
        return validation_passed
        
    def get_health_summary(self, report_file: str) -> Dict[str, Any]:
        """Get summary of health report for debugging"""
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
                
            return {
                'health_score': data.get('health_score', 0),
                'high_issues': data.get('statistics', {}).get('high_issues', 0),
                'total_issues': data.get('statistics', {}).get('total_issues', 0),
                'coverage': data.get('coverage', {}),
                'validation_passed': self._validate_report_data(data)
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Validate documentation health score')
    parser.add_argument('report_file', help='Path to JSON health report file')
    parser.add_argument('--health-threshold', type=int, default=90, 
                       help='Minimum health score threshold (default: 90)')
    parser.add_argument('--max-high-issues', type=int, default=0,
                       help='Maximum high priority issues allowed (default: 0)')
    parser.add_argument('--summary', action='store_true',
                       help='Print summary and exit with success')
    
    args = parser.parse_args()
    
    validator = DocumentationHealthValidator(
        health_threshold=args.health_threshold,
        high_issues_threshold=args.max_high_issues
    )
    
    if args.summary:
        summary = validator.get_health_summary(args.report_file)
        print(json.dumps(summary, indent=2))
        sys.exit(0)
        
    success = validator.validate_health_report(args.report_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()