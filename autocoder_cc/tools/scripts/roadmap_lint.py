#!/usr/bin/env python3
"""
Roadmap Linter - Status Tag and Checkbox Validation
Validates consistency between roadmap status tags and actual implementation

This script ensures that:
- Features marked as complete (✔️) actually exist in codebase
- Checkboxes match status tags
- No orphaned status tags without corresponding features
"""
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class StatusType(Enum):
    """Types of status indicators"""
    CHECKMARK = "✔️"
    IN_PROGRESS = "🚧"
    PLANNED = "🗓️"
    DEFERRED = "➖"
    REFRESH = "🔄"


@dataclass
class RoadmapItem:
    """A roadmap item with status information"""
    name: str
    status: StatusType
    line_number: int
    context: str
    file_path: Path


@dataclass
class LintResult:
    """Result of roadmap linting"""
    item: RoadmapItem
    issue_type: str
    message: str
    severity: str  # error, warning, info


class RoadmapLinter:
    """
    Lints the Enterprise Roadmap for consistency issues.
    
    Features:
    - Status tag validation
    - Checkbox consistency checking
    - Implementation verification
    - Orphaned status detection
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.roadmap_file = self.repo_root / "docs" / "Enterprise_roadmap_v3.md"
        self.results: List[LintResult] = []
        self.roadmap_items: List[RoadmapItem] = []
        
    def lint_roadmap(self) -> List[LintResult]:
        """Run all linting checks on the roadmap"""
        print("🔍 Starting roadmap linting...")
        
        if not self.roadmap_file.exists():
            self.results.append(LintResult(
                item=RoadmapItem("", StatusType.PLANNED, 0, "", self.roadmap_file),
                issue_type="missing_file",
                message="Enterprise_roadmap_v3.md not found",
                severity="error"
            ))
            return self.results
        
        # 1. Extract roadmap items
        self._extract_roadmap_items()
        
        # 2. Validate status tags
        self._validate_status_tags()
        
        # 3. Check checkbox consistency
        self._check_checkbox_consistency()
        
        # 4. Verify completed features exist
        self._verify_completed_features()
        
        # 5. Check for orphaned status tags
        self._check_orphaned_status_tags()
        
        return self.results
    
    def _extract_roadmap_items(self):
        """Extract all roadmap items with status tags (improved for inline and summary lines)"""
        print("📋 Extracting roadmap items...")
        
        try:
            content = self.roadmap_file.read_text()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Look for any status tag anywhere in the line
                status_tag_match = re.search(r'(✔️|🚧|🗓️|➖|🔄)', line)
                if status_tag_match:
                    status_char = status_tag_match.group(1)
                    status = self._char_to_status(status_char)
                    # Try to extract a feature/task name
                    # Remove markdown formatting, numbers, and status tags
                    # e.g. "### ✔️ Cycle 26 COMPLETED: ..." or "1. ✔️ Standardized Configuration Attribute (CRITICAL): ..."
                    cleaned = re.sub(r'[\-*#>\[\]\d\.]', '', line)
                    cleaned = re.sub(r'(✔️|🚧|🗓️|➖|🔄)', '', cleaned)
                    cleaned = cleaned.strip()
                    # Use the first part of the line before a colon or dash as the name, or the whole cleaned line
                    name = cleaned.split(':')[0].split('-')[0].strip() if (':' in cleaned or '-' in cleaned) else cleaned
                    if not name:
                        name = cleaned
                    self.roadmap_items.append(RoadmapItem(
                        name=name,
                        status=status,
                        line_number=line_num,
                        context=line.strip(),
                        file_path=self.roadmap_file
                    ))
            print(f"   Found {len(self.roadmap_items)} roadmap items")
        except Exception as e:
            print(f"   Error extracting roadmap items: {e}")
    
    def _char_to_status(self, status_char: str) -> StatusType:
        """Convert status character to StatusType enum"""
        status_map = {
            "✔️": StatusType.CHECKMARK,
            "🚧": StatusType.IN_PROGRESS,
            "🗓️": StatusType.PLANNED,
            "➖": StatusType.DEFERRED,
            "🔄": StatusType.REFRESH
        }
        return status_map.get(status_char, StatusType.PLANNED)
    
    def _validate_status_tags(self):
        """Validate that status tags are properly formatted"""
        print("🏷️ Validating status tags...")
        
        for item in self.roadmap_items:
            # Check for empty or whitespace-only names
            if not item.name or item.name.isspace():
                self.results.append(LintResult(
                    item=item,
                    issue_type="empty_name",
                    message="Roadmap item has empty or whitespace-only name",
                    severity="error"
                ))
            
            # Check for inconsistent status usage
            if item.status == StatusType.CHECKMARK:
                # Completed items should have clear, specific names
                if len(item.name) < 3:
                    self.results.append(LintResult(
                        item=item,
                        issue_type="vague_completed_item",
                        message="Completed item has very short name - may be too vague",
                        severity="warning"
                    ))
    
    def _check_checkbox_consistency(self):
        """Check consistency between checkboxes and status tags"""
        print("☑️ Checking checkbox consistency...")
        
        # Group items by name to find duplicates
        items_by_name: Dict[str, List[RoadmapItem]] = {}
        for item in self.roadmap_items:
            if item.name not in items_by_name:
                items_by_name[item.name] = []
            items_by_name[item.name].append(item)
        
        # Check for duplicate items with different statuses
        for name, items in items_by_name.items():
            if len(items) > 1:
                statuses = [item.status for item in items]
                if len(set(statuses)) > 1:
                    self.results.append(LintResult(
                        item=items[0],
                        issue_type="inconsistent_status",
                        message=f"Item '{name}' appears multiple times with different statuses: {[s.value for s in statuses]}",
                        severity="error"
                    ))
    
    def _verify_completed_features(self):
        """Verify that completed features actually exist in codebase"""
        print("✅ Verifying completed features...")
        
        for item in self.roadmap_items:
            if item.status == StatusType.CHECKMARK:
                if not self._feature_exists_in_code(item.name):
                    self.results.append(LintResult(
                        item=item,
                        issue_type="missing_implementation",
                        message=f"Feature marked as complete (✔️) but implementation not found in codebase",
                        severity="error"
                    ))
    
    def _feature_exists_in_code(self, feature_name: str) -> bool:
        """Check if a feature exists in the codebase"""
        # Convert feature name to potential code identifiers
        code_identifiers = [
            feature_name.lower().replace(' ', '_'),
            feature_name.lower().replace(' ', ''),
            feature_name.replace(' ', ''),
            feature_name.lower()
        ]
        
        # Check for files, classes, or functions that match
        for py_file in self.repo_root.rglob("*.py"):
            if "test" not in str(py_file) and "example" not in str(py_file):
                try:
                    content = py_file.read_text()
                    
                    for identifier in code_identifiers:
                        if identifier in content:
                            return True
                            
                except Exception:
                    continue
        
        return False
    
    def _check_orphaned_status_tags(self):
        """Check for status tags without clear feature names"""
        print("👻 Checking for orphaned status tags...")
        
        for item in self.roadmap_items:
            # Check for very generic names that might be orphaned
            generic_patterns = [
                r'^[A-Z][a-z]+$',  # Single word like "Feature"
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Two words like "Some Feature"
            ]
            
            for pattern in generic_patterns:
                if re.match(pattern, item.name):
                    # Check if this generic name appears in codebase
                    if not self._feature_exists_in_code(item.name):
                        self.results.append(LintResult(
                            item=item,
                            issue_type="orphaned_status",
                            message=f"Status tag for '{item.name}' may be orphaned - no clear implementation found",
                            severity="warning"
                        ))
    
    def generate_report(self) -> Dict[str, any]:
        """Generate linting report"""
        total_items = len(self.roadmap_items)
        total_issues = len(self.results)
        errors = len([r for r in self.results if r.severity == "error"])
        warnings = len([r for r in self.results if r.severity == "warning"])
        infos = len([r for r in self.results if r.severity == "info"])
        
        # Group issues by type
        issues_by_type: Dict[str, int] = {}
        for result in self.results:
            issue_type = result.issue_type
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        return {
            "summary": {
                "total_items": total_items,
                "total_issues": total_issues,
                "errors": errors,
                "warnings": warnings,
                "infos": infos,
                "health_score": max(0, 100 - (errors * 10) - (warnings * 5))
            },
            "issues_by_type": issues_by_type,
            "results": [
                {
                    "name": r.item.name,
                    "status": r.item.status.value,
                    "line_number": r.item.line_number,
                    "issue_type": r.issue_type,
                    "message": r.message,
                    "severity": r.severity
                }
                for r in self.results
            ]
        }
    
    def print_report(self):
        """Print linting report to console"""
        report = self.generate_report()
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("📋 ROADMAP LINTING REPORT")
        print("="*60)
        
        print(f"📈 Health Score: {summary['health_score']:.1f}%")
        print(f"📋 Total Items: {summary['total_items']}")
        print(f"❌ Errors: {summary['errors']}")
        print(f"⚠️ Warnings: {summary['warnings']}")
        print(f"ℹ️ Info: {summary['infos']}")
        
        if summary['errors'] > 0:
            print(f"\n🔴 ERRORS ({summary['errors']}):")
            for result in self.results:
                if result.severity == "error":
                    print(f"   Line {result.item.line_number}: {result.item.name}")
                    print(f"      {result.message}")
        
        if summary['warnings'] > 0:
            print(f"\n⚠️ WARNINGS ({summary['warnings']}):")
            for result in self.results:
                if result.severity == "warning":
                    print(f"   Line {result.item.line_number}: {result.item.name}")
                    print(f"      {result.message}")
        
        if report["issues_by_type"]:
            print(f"\n📊 Issues by Type:")
            for issue_type, count in report["issues_by_type"].items():
                print(f"   {issue_type}: {count}")
        
        print("\n" + "="*60)


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Roadmap Linter')
    parser.add_argument('--repo-root', type=Path, default=Path.cwd(), help='Repository root directory')
    parser.add_argument('--output', type=Path, help='Output JSON report file')
    parser.add_argument('--fail-on-errors', action='store_true', help='Exit with error code on linting errors')
    
    args = parser.parse_args()
    
    # Run linting
    linter = RoadmapLinter(args.repo_root)
    results = linter.lint_roadmap()
    
    # Print report
    linter.print_report()
    
    # Save report if requested
    if args.output:
        report = linter.generate_report()
        args.output.write_text(json.dumps(report, indent=2))
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with error code if requested and there are errors
    if args.fail_on_errors:
        report = linter.generate_report()
        if report["summary"]["errors"] > 0:
            print("\n❌ Linting failed - exiting with error code")
            sys.exit(1)
    
    print("\n✅ Linting completed")


if __name__ == "__main__":
    main() 