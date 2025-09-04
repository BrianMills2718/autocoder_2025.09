#!/usr/bin/env python3
"""
Documentation Matrix Validation Script
Cross-reference matrix validation for documentation-code consistency

This script validates that all documented features exist in the codebase
and that all codebase features are documented.
"""
import ast
import os
import re
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Validation status for documentation items"""
    VALID = "valid"
    MISSING_CODE = "missing_code"
    MISSING_DOC = "missing_doc"
    INCONSISTENT = "inconsistent"


@dataclass
class ValidationResult:
    """Result of documentation validation"""
    item_name: str
    item_type: str  # file, class, function, feature
    status: ValidationStatus
    documented_location: Optional[str] = None
    code_location: Optional[str] = None
    error_message: Optional[str] = None


class DocumentationMatrixValidator:
    """
    Validates consistency between documentation and codebase.
    
    Features:
    - Cross-reference matrix validation
    - Status tag verification
    - Code example validation
    - Coverage detection
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.docs_dir = self.repo_root / "docs"
        self.autocoder_dir = self.repo_root / "autocoder"
        self.blueprint_dir = self.repo_root / "blueprint_language"
        
        # Track validation results
        self.results: List[ValidationResult] = []
        self.documented_items: Set[str] = set()
        self.code_items: Set[str] = set()
        
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks"""
        print("🔍 Starting documentation matrix validation...")
        
        # 1. Extract documented items
        self._extract_documented_items()
        
        # 2. Extract code items
        self._extract_code_items()
        
        # 3. Cross-reference validation
        self._cross_reference_validation()
        
        # 4. Status tag validation
        self._validate_status_tags()
        
        # 5. Code example validation
        self._validate_code_examples()
        
        return self.results
    
    def _extract_documented_items(self):
        """Extract items mentioned in documentation"""
        print("📋 Extracting documented items...")
        
        # Scan main documentation files
        doc_files = [
            "Enterprise_roadmap_v3.md",
            "Architecture_Combined.md", 
            "quickstart.md"
        ]
        
        for doc_file in doc_files:
            doc_path = self.docs_dir / doc_file
            if doc_path.exists():
                self._extract_from_markdown(doc_path)
        
        print(f"   Found {len(self.documented_items)} documented items")
    
    def _extract_from_markdown(self, file_path: Path):
        """Extract items from markdown file"""
        try:
            content = file_path.read_text()
            
            # Extract file references
            file_pattern = r'`([^`]+\.py)`'
            for match in re.finditer(file_pattern, content):
                self.documented_items.add(f"file:{match.group(1)}")
            
            # Extract class references
            class_pattern = r'`([A-Z][a-zA-Z0-9]*Component)`'
            for match in re.finditer(class_pattern, content):
                self.documented_items.add(f"class:{match.group(1)}")
            
            # Extract function references
            func_pattern = r'`([a-z_][a-zA-Z0-9_]*\(\)?)`'
            for match in re.finditer(func_pattern, content):
                self.documented_items.add(f"function:{match.group(1)}")
            
            # Extract feature references
            feature_pattern = r'([A-Z][a-zA-Z0-9\s]+):\s*[✔️🚧🗓️]'
            for match in re.finditer(feature_pattern, content):
                self.documented_items.add(f"feature:{match.group(1).strip()}")
                
        except Exception as e:
            print(f"   Warning: Failed to parse {file_path}: {e}")
    
    def _extract_code_items(self):
        """Extract items from codebase"""
        print("💻 Extracting code items...")
        
        # Scan Python files
        for py_file in self.repo_root.rglob("*.py"):
            if "test" not in str(py_file) and "example" not in str(py_file):
                self._extract_from_python_file(py_file)
        
        print(f"   Found {len(self.code_items)} code items")
    
    def _extract_from_python_file(self, file_path: Path):
        """Extract items from Python file"""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.code_items.add(f"class:{node.name}")
                    
                    # Check if it's a component
                    if node.name.endswith('Component'):
                        self.code_items.add(f"component:{node.name}")
                
                elif isinstance(node, ast.FunctionDef):
                    self.code_items.add(f"function:{node.name}")
            
            # Add file itself
            rel_path = file_path.relative_to(self.repo_root)
            self.code_items.add(f"file:{rel_path}")
            
        except Exception as e:
            print(f"   Warning: Failed to parse {file_path}: {e}")
    
    def _cross_reference_validation(self):
        """Cross-reference documented vs code items"""
        print("🔗 Cross-referencing documentation and code...")
        
        # Check for documented items missing from code
        for item in self.documented_items:
            if item not in self.code_items:
                self.results.append(ValidationResult(
                    item_name=item,
                    item_type=item.split(':')[0],
                    status=ValidationStatus.MISSING_CODE,
                    documented_location="documentation",
                    error_message=f"Documented item '{item}' not found in codebase"
                ))
        
        # Check for code items missing from documentation
        for item in self.code_items:
            if item not in self.documented_items:
                self.results.append(ValidationResult(
                    item_name=item,
                    item_type=item.split(':')[0],
                    status=ValidationStatus.MISSING_DOC,
                    code_location="codebase",
                    error_message=f"Code item '{item}' not documented"
                ))
    
    def _validate_status_tags(self):
        """Validate status tags in roadmap"""
        print("🏷️ Validating status tags...")
        
        roadmap_file = self.docs_dir / "Enterprise_roadmap_v3.md"
        if not roadmap_file.exists():
            return
        
        try:
            content = roadmap_file.read_text()
            
            # Find status tags
            status_pattern = r'([A-Z][a-zA-Z0-9\s]+):\s*([✔️🚧🗓️])'
            for match in re.finditer(status_pattern, content):
                feature_name = match.group(1).strip()
                status = match.group(2)
                
                # Check if completed features exist in code
                if status == "✔️":
                    if not self._feature_exists_in_code(feature_name):
                        self.results.append(ValidationResult(
                            item_name=feature_name,
                            item_type="feature",
                            status=ValidationStatus.INCONSISTENT,
                            documented_location=str(roadmap_file),
                            error_message=f"Feature marked as complete (✔️) but not found in codebase"
                        ))
                        
        except Exception as e:
            print(f"   Warning: Failed to validate status tags: {e}")
    
    def _feature_exists_in_code(self, feature_name: str) -> bool:
        """Check if a feature exists in the codebase"""
        # Convert feature name to potential code identifiers
        code_identifiers = [
            feature_name.lower().replace(' ', '_'),
            feature_name.lower().replace(' ', ''),
            feature_name.replace(' ', '')
        ]
        
        for identifier in code_identifiers:
            if any(identifier in item for item in self.code_items):
                return True
        
        return False
    
    def _validate_code_examples(self):
        """Validate code examples in documentation"""
        print("📝 Validating code examples...")
        
        # Scan for code blocks in markdown
        for doc_file in self.docs_dir.rglob("*.md"):
            try:
                content = doc_file.read_text()
                
                # Find code blocks
                code_block_pattern = r'```(?:python)?\n(.*?)\n```'
                for match in re.finditer(code_block_pattern, content, re.DOTALL):
                    code_example = match.group(1)
                    
                    # Basic syntax validation
                    try:
                        ast.parse(code_example)
                    except SyntaxError as e:
                        self.results.append(ValidationResult(
                            item_name=f"code_example_in_{doc_file.name}",
                            item_type="code_example",
                            status=ValidationStatus.INCONSISTENT,
                            documented_location=str(doc_file),
                            error_message=f"Code example has syntax error: {e}"
                        ))
                        
            except Exception as e:
                print(f"   Warning: Failed to validate code examples in {doc_file}: {e}")
    
    def generate_report(self) -> Dict[str, any]:
        """Generate validation report"""
        total_items = len(self.results)
        valid_items = len([r for r in self.results if r.status == ValidationStatus.VALID])
        missing_code = len([r for r in self.results if r.status == ValidationStatus.MISSING_CODE])
        missing_doc = len([r for r in self.results if r.status == ValidationStatus.MISSING_DOC])
        inconsistent = len([r for r in self.results if r.status == ValidationStatus.INCONSISTENT])
        
        return {
            "summary": {
                "total_items": total_items,
                "valid_items": valid_items,
                "missing_code": missing_code,
                "missing_doc": missing_doc,
                "inconsistent": inconsistent,
                "health_score": (valid_items / total_items * 100) if total_items > 0 else 100
            },
            "results": [
                {
                    "item_name": r.item_name,
                    "item_type": r.item_type,
                    "status": r.status.value,
                    "documented_location": r.documented_location,
                    "code_location": r.code_location,
                    "error_message": r.error_message
                }
                for r in self.results
            ],
            "documented_items_count": len(self.documented_items),
            "code_items_count": len(self.code_items)
        }
    
    def print_report(self):
        """Print validation report to console"""
        report = self.generate_report()
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("📊 DOCUMENTATION MATRIX VALIDATION REPORT")
        print("="*60)
        
        print(f"📈 Health Score: {summary['health_score']:.1f}%")
        print(f"📋 Total Items: {summary['total_items']}")
        print(f"✅ Valid Items: {summary['valid_items']}")
        print(f"❌ Missing Code: {summary['missing_code']}")
        print(f"📝 Missing Documentation: {summary['missing_doc']}")
        print(f"⚠️ Inconsistent: {summary['inconsistent']}")
        
        if summary['missing_code'] > 0:
            print(f"\n🔴 CRITICAL: {summary['missing_code']} documented items missing from codebase:")
            for result in self.results:
                if result.status == ValidationStatus.MISSING_CODE:
                    print(f"   - {result.item_name}: {result.error_message}")
        
        if summary['inconsistent'] > 0:
            print(f"\n⚠️ WARNING: {summary['inconsistent']} inconsistencies found:")
            for result in self.results:
                if result.status == ValidationStatus.INCONSISTENT:
                    print(f"   - {result.item_name}: {result.error_message}")
        
        print("\n" + "="*60)


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Documentation Matrix Validator')
    parser.add_argument('--repo-root', type=Path, default=Path.cwd(), help='Repository root directory')
    parser.add_argument('--output', type=Path, help='Output JSON report file')
    parser.add_argument('--fail-on-errors', action='store_true', help='Exit with error code on validation failures')
    
    args = parser.parse_args()
    
    # Run validation
    validator = DocumentationMatrixValidator(args.repo_root)
    results = validator.validate_all()
    
    # Print report
    validator.print_report()
    
    # Save report if requested
    if args.output:
        report = validator.generate_report()
        args.output.write_text(json.dumps(report, indent=2))
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with error code if requested and there are failures
    if args.fail_on_errors:
        report = validator.generate_report()
        if report["summary"]["missing_code"] > 0 or report["summary"]["inconsistent"] > 0:
            print("\n❌ Validation failed - exiting with error code")
            sys.exit(1)
    
    print("\n✅ Validation completed")


if __name__ == "__main__":
    main() 