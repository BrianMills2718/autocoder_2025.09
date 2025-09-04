#!/usr/bin/env python3
"""
Validation Pipeline for CI/CD Integration
=========================================

Integrates comprehensive validation with CI/CD pipelines including:
- Automated validation report generation
- Exit codes for CI/CD systems
- Webhook integration for notifications
- Validation gate enforcement
- Performance regression detection
"""

import os
import json
import time
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from validation_scanner import ValidationScanner, ValidationReport


@dataclass
class PipelineConfig:
    """Configuration for validation pipeline"""
    project_path: str
    validation_config_path: Optional[str] = None
    output_dir: str = "validation_reports"
    fail_on_critical: bool = True
    fail_on_high: bool = True
    fail_on_medium: bool = False
    max_validation_score_threshold: float = 80.0  # Minimum score to pass
    performance_baseline_path: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_webhook: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of validation pipeline execution"""
    passed: bool
    validation_score: float
    exit_code: int
    report_path: str
    duration_seconds: float
    issues_summary: Dict[str, int]
    performance_regression: bool = False
    baseline_comparison: Optional[Dict] = None


class ValidationPipeline:
    """Main validation pipeline orchestrator for CI/CD"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.scanner = ValidationScanner(config.validation_config_path)
        
        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup pipeline logging"""
        logger = get_logger('validation_pipeline')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - PIPELINE - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = Path(self.config.output_dir) / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def run_validation(self) -> PipelineResult:
        """Run complete validation pipeline"""
        start_time = time.time()
        self.logger.info(f"Starting validation pipeline for {self.config.project_path}")
        
        try:
            # Run validation scan
            self.logger.info("Executing validation scan...")
            validation_report = self.scanner.scan_directory(self.config.project_path)
            
            # Generate report files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_base = Path(self.config.output_dir) / f"validation_report_{timestamp}"
            
            # Export in multiple formats
            json_report_path = f"{report_base}.json"
            html_report_path = f"{report_base}.html"
            csv_report_path = f"{report_base}.csv"
            junit_report_path = f"{report_base}.xml"
            
            self.scanner.export_report(validation_report, json_report_path, 'json')
            self.scanner.export_report(validation_report, html_report_path, 'html')
            self.scanner.export_report(validation_report, csv_report_path, 'csv')
            self._export_junit_xml(validation_report, junit_report_path)
            
            # Performance comparison
            performance_regression, baseline_comparison = self._check_performance_regression(validation_report)
            
            # Determine pass/fail
            passed, exit_code = self._evaluate_results(validation_report)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Create pipeline result
            result = PipelineResult(
                passed=passed,
                validation_score=validation_report.validation_score,
                exit_code=exit_code,
                report_path=json_report_path,
                duration_seconds=round(duration, 2),
                issues_summary=validation_report.issues_by_severity,
                performance_regression=performance_regression,
                baseline_comparison=baseline_comparison
            )
            
            # Generate summary
            self._generate_pipeline_summary(result, validation_report)
            
            # Send notifications
            if self.config.webhook_url or self.config.slack_webhook:
                self._send_notifications(result, validation_report)
            
            # Update baseline if successful
            if passed and self.config.performance_baseline_path:
                self._update_performance_baseline(validation_report)
            
            self.logger.info(f"Validation pipeline completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Validation pipeline failed: {str(e)}")
            end_time = time.time()
            
            return PipelineResult(
                passed=False,
                validation_score=0.0,
                exit_code=2,
                report_path="",
                duration_seconds=round(end_time - start_time, 2),
                issues_summary={"critical": 1, "error": str(e)}
            )
    
    def _evaluate_results(self, report: ValidationReport) -> tuple[bool, int]:
        """Evaluate validation results and determine pass/fail"""
        critical_count = report.issues_by_severity.get('critical', 0)
        high_count = report.issues_by_severity.get('high', 0)
        medium_count = report.issues_by_severity.get('medium', 0)
        
        # Check critical issues
        if self.config.fail_on_critical and critical_count > 0:
            self.logger.error(f"FAIL: {critical_count} critical issues found")
            return False, 1
        
        # Check high severity issues
        if self.config.fail_on_high and high_count > 0:
            self.logger.error(f"FAIL: {high_count} high severity issues found")
            return False, 1
        
        # Check medium severity issues
        if self.config.fail_on_medium and medium_count > 0:
            self.logger.error(f"FAIL: {medium_count} medium severity issues found")
            return False, 1
        
        # Check validation score threshold
        if report.validation_score < self.config.max_validation_score_threshold:
            self.logger.error(f"FAIL: Validation score {report.validation_score} below threshold {self.config.max_validation_score_threshold}")
            return False, 1
        
        self.logger.info(f"PASS: Validation score {report.validation_score}, issues within acceptable limits")
        return True, 0
    
    def _check_performance_regression(self, report: ValidationReport) -> tuple[bool, Optional[Dict]]:
        """Check for performance regression against baseline"""
        if not self.config.performance_baseline_path:
            return False, None
        
        baseline_path = Path(self.config.performance_baseline_path)
        if not baseline_path.exists():
            self.logger.info("No performance baseline found, creating initial baseline")
            return False, None
        
        try:
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
            
            current_scan_time = report.scan_duration_seconds
            baseline_scan_time = baseline.get('scan_duration_seconds', 0)
            
            # Check for 20% performance regression
            regression_threshold = 1.2
            if current_scan_time > baseline_scan_time * regression_threshold:
                regression_detected = True
                self.logger.warning(f"Performance regression detected: {current_scan_time:.2f}s vs baseline {baseline_scan_time:.2f}s")
            else:
                regression_detected = False
                self.logger.info(f"Performance within acceptable range: {current_scan_time:.2f}s vs baseline {baseline_scan_time:.2f}s")
            
            comparison = {
                'current_scan_time': current_scan_time,
                'baseline_scan_time': baseline_scan_time,
                'regression_percentage': ((current_scan_time - baseline_scan_time) / baseline_scan_time) * 100,
                'regression_detected': regression_detected
            }
            
            return regression_detected, comparison
            
        except Exception as e:
            self.logger.error(f"Failed to check performance regression: {str(e)}")
            return False, None
    
    def _update_performance_baseline(self, report: ValidationReport):
        """Update performance baseline with current results"""
        if not self.config.performance_baseline_path:
            return
        
        baseline_data = {
            'scan_duration_seconds': report.scan_duration_seconds,
            'total_files_scanned': report.total_files_scanned,
            'validation_score': report.validation_score,
            'updated_timestamp': report.scan_timestamp
        }
        
        try:
            with open(self.config.performance_baseline_path, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            self.logger.info(f"Updated performance baseline: {self.config.performance_baseline_path}")
        except Exception as e:
            self.logger.error(f"Failed to update performance baseline: {str(e)}")
    
    def _generate_pipeline_summary(self, result: PipelineResult, report: ValidationReport):
        """Generate human-readable pipeline summary"""
        summary_path = Path(self.config.output_dir) / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        status_emoji = "✅" if result.passed else "❌"
        
        summary_content = f"""# Validation Pipeline Summary
        
## Result: {status_emoji} {'PASSED' if result.passed else 'FAILED'}

**Validation Score:** {result.validation_score}/100
**Duration:** {result.duration_seconds}s
**Files Scanned:** {report.total_files_scanned}
**Total Issues:** {report.total_issues_found}

## Issues Breakdown

| Severity | Count |
|----------|--------|
"""
        
        for severity, count in result.issues_summary.items():
            summary_content += f"| {severity.title()} | {count} |\n"
        
        if result.performance_regression:
            summary_content += f"""
## Performance Regression Detected ⚠️

Performance has regressed by {result.baseline_comparison.get('regression_percentage', 0):.1f}%
- Current scan time: {result.baseline_comparison.get('current_scan_time', 0):.2f}s
- Baseline scan time: {result.baseline_comparison.get('baseline_scan_time', 0):.2f}s
"""
        
        summary_content += f"""
## Report Files

- JSON Report: {result.report_path}
- HTML Report: {result.report_path.replace('.json', '.html')}
- CSV Report: {result.report_path.replace('.json', '.csv')}

## CI/CD Integration

Exit code: {result.exit_code}
- 0: All validations passed
- 1: Validation failures found
- 2: Pipeline execution error

Generated at: {datetime.now().isoformat()}
"""
        
        try:
            with open(summary_path, 'w') as f:
                f.write(summary_content)
            self.logger.info(f"Pipeline summary written to: {summary_path}")
        except Exception as e:
            self.logger.error(f"Failed to write pipeline summary: {str(e)}")
    
    def _send_notifications(self, result: PipelineResult, report: ValidationReport):
        """Send notifications to configured webhooks"""
        if self.config.slack_webhook:
            self._send_slack_notification(result, report)
        
        if self.config.webhook_url:
            self._send_webhook_notification(result, report)
    
    def _send_slack_notification(self, result: PipelineResult, report: ValidationReport):
        """Send Slack notification"""
        try:
            import requests
            
            status_color = "good" if result.passed else "danger"
            status_text = "PASSED ✅" if result.passed else "FAILED ❌"
            
            payload = {
                "attachments": [
                    {
                        "color": status_color,
                        "title": f"Validation Pipeline {status_text}",
                        "fields": [
                            {"title": "Validation Score", "value": f"{result.validation_score}/100", "short": True},
                            {"title": "Duration", "value": f"{result.duration_seconds}s", "short": True},
                            {"title": "Total Issues", "value": str(report.total_issues_found), "short": True},
                            {"title": "Files Scanned", "value": str(report.total_files_scanned), "short": True}
                        ],
                        "footer": "Autocoder Validation Pipeline",
                        "ts": int(time.time())
                    }
                ]
            }
            
            response = requests.post(self.config.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info("Slack notification sent successfully")
            else:
                self.logger.error(f"Failed to send Slack notification: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _send_webhook_notification(self, result: PipelineResult, report: ValidationReport):
        """Send generic webhook notification"""
        try:
            import requests
            
            payload = {
                "validation_result": asdict(result),
                "report_summary": {
                    "validation_score": report.validation_score,
                    "total_issues": report.total_issues_found,
                    "issues_by_severity": report.issues_by_severity,
                    "scan_timestamp": report.scan_timestamp
                }
            }
            
            response = requests.post(self.config.webhook_url, json=payload, timeout=10)
            if response.status_code in [200, 201, 202]:
                self.logger.info("Webhook notification sent successfully")
            else:
                self.logger.error(f"Failed to send webhook notification: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")
    
    def _export_junit_xml(self, report: ValidationReport, output_path: str):
        """Export validation report as JUnit XML for CI/CD integration"""
        try:
            import xml.etree.ElementTree as ET
            
            # Create root test suite
            testsuite = ET.Element('testsuite')
            testsuite.set('name', 'Enterprise Validation')
            testsuite.set('timestamp', report.scan_timestamp)
            testsuite.set('tests', str(report.total_files_scanned))
            testsuite.set('failures', str(report.total_issues_found))
            testsuite.set('time', str(report.scan_duration_seconds))
            
            # Add properties
            properties = ET.SubElement(testsuite, 'properties')
            
            prop_score = ET.SubElement(properties, 'property')
            prop_score.set('name', 'validation_score')
            prop_score.set('value', str(report.validation_score))
            
            prop_critical = ET.SubElement(properties, 'property')
            prop_critical.set('name', 'critical_issues')
            prop_critical.set('value', str(report.issues_by_severity.get('critical', 0)))
            
            prop_high = ET.SubElement(properties, 'property')
            prop_high.set('name', 'high_issues')
            prop_high.set('value', str(report.issues_by_severity.get('high', 0)))
            
            # Group issues by file for test cases
            issues_by_file = {}
            for issue in report.issues:
                file_path = issue.file_path
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
            
            # Create test cases for each file
            for file_path, file_issues in issues_by_file.items():
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', 'ValidationScanner')
                testcase.set('name', file_path)
                testcase.set('time', '0')
                
                # If there are issues, mark as failure
                if file_issues:
                    failure = ET.SubElement(testcase, 'failure')
                    failure.set('message', f"{len(file_issues)} validation issues found")
                    
                    # Create detailed failure message
                    failure_details = []
                    for issue in file_issues:
                        failure_details.append(
                            f"Line {issue.line_number}: [{issue.severity.upper()}] "
                            f"{issue.issue_type} - {issue.description}"
                        )
                    
                    failure.text = '\n'.join(failure_details)
            
            # Add test cases for files with no issues (passing tests)
            scanned_files = report.total_files_scanned
            files_with_issues = len(issues_by_file)
            passing_files = scanned_files - files_with_issues
            
            if passing_files > 0:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', 'ValidationScanner')
                testcase.set('name', f'{passing_files}_files_passed_validation')
                testcase.set('time', '0')
            
            # Update test count
            testsuite.set('tests', str(len(issues_by_file) + (1 if passing_files > 0 else 0)))
            
            # Write XML
            tree = ET.ElementTree(testsuite)
            ET.indent(tree, space="  ", level=0)  # Pretty formatting
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"JUnit XML report generated: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate JUnit XML report: {str(e)}")


def create_github_actions_workflow() -> str:
    """Generate GitHub Actions workflow for validation pipeline"""
    return """name: Validation Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run Validation Pipeline
      run: |
        python tools/validation_pipeline.py \\
          --project-path . \\
          --fail-on-critical \\
          --fail-on-high \\
          --score-threshold 85 \\
          --output-dir validation_reports \\
          --performance-baseline .github/validation_baseline.json
      env:
        VALIDATION_WEBHOOK: ${{ secrets.VALIDATION_WEBHOOK }}
        SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    
    - name: Upload Validation Reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: validation-reports
        path: validation_reports/
        
    - name: Comment PR with Results
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const fs = require('fs');
          try {
            const summaryPath = 'validation_reports/pipeline_summary_latest.md';
            if (fs.existsSync(summaryPath)) {
              const summary = fs.readFileSync(summaryPath, 'utf8');
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: summary
              });
            }
          } catch (error) {
            console.log('Could not post validation summary to PR');
          }
"""


def create_gitlab_ci_config() -> str:
    """Generate GitLab CI configuration for validation pipeline"""
    return """stages:
  - validation

validation:
  stage: validation
  image: python:3.9
  before_script:
    - pip install -r requirements.txt
  script:
    - python tools/validation_pipeline.py 
        --project-path . 
        --fail-on-critical 
        --fail-on-high 
        --score-threshold 85 
        --output-dir validation_reports
        --performance-baseline .gitlab/validation_baseline.json
  artifacts:
    when: always
    reports:
      junit: validation_reports/*.xml
    paths:
      - validation_reports/
    expire_in: 1 week
  only:
    - merge_requests
    - main
    - develop
"""


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Validation Pipeline for CI/CD')
    parser.add_argument('--project-path', required=True, help='Path to project to validate')
    parser.add_argument('--config', help='Path to validation configuration file')
    parser.add_argument('--output-dir', default='validation_reports', help='Output directory for reports')
    parser.add_argument('--fail-on-critical', action='store_true', help='Fail pipeline on critical issues')
    parser.add_argument('--fail-on-high', action='store_true', help='Fail pipeline on high severity issues')
    parser.add_argument('--fail-on-medium', action='store_true', help='Fail pipeline on medium severity issues')
    parser.add_argument('--score-threshold', type=float, default=80.0, help='Minimum validation score to pass')
    parser.add_argument('--performance-baseline', help='Path to performance baseline file')
    parser.add_argument('--webhook-url', help='Webhook URL for notifications')
    parser.add_argument('--slack-webhook', help='Slack webhook URL')
    parser.add_argument('--generate-github-workflow', action='store_true', help='Generate GitHub Actions workflow')
    parser.add_argument('--generate-gitlab-ci', action='store_true', help='Generate GitLab CI configuration')
    
    args = parser.parse_args()
    
    # Generate CI/CD configurations if requested
    if args.generate_github_workflow:
        workflow_content = create_github_actions_workflow()
        workflow_path = Path('.github/workflows/validation.yml')
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        with open(workflow_path, 'w') as f:
            f.write(workflow_content)
        print(f"GitHub Actions workflow generated: {workflow_path}")
        return 0
    
    if args.generate_gitlab_ci:
        gitlab_content = create_gitlab_ci_config()
        with open('.gitlab-ci.yml', 'w') as f:
            f.write(gitlab_content)
        print("GitLab CI configuration generated: .gitlab-ci.yml")
        return 0
    
    # Create pipeline configuration
    config = PipelineConfig(
        project_path=args.project_path,
        validation_config_path=args.config,
        output_dir=args.output_dir,
        fail_on_critical=args.fail_on_critical,
        fail_on_high=args.fail_on_high,
        fail_on_medium=args.fail_on_medium,
        max_validation_score_threshold=args.score_threshold,
        performance_baseline_path=args.performance_baseline,
        webhook_url=args.webhook_url or os.getenv('VALIDATION_WEBHOOK'),
        slack_webhook=args.slack_webhook or os.getenv('SLACK_WEBHOOK')
    )
    
    # Run validation pipeline
    pipeline = ValidationPipeline(config)
    result = pipeline.run_validation()
    
    # Print summary
    print(f"\nValidation Pipeline {'PASSED' if result.passed else 'FAILED'}")
    print(f"Validation Score: {result.validation_score}/100")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Report: {result.report_path}")
    
    if result.performance_regression:
        print("⚠️  Performance regression detected")
    
    return result.exit_code


if __name__ == '__main__':
    exit(main())