#!/usr/bin/env python3
"""
Schema Version Validator

This module implements schema version validation for blueprints as recommended in the assessment.
It enforces the required schema_version field and validates version compatibility.

Based on assessment recommendation: "Add required schema_version field; registry rejects missing"
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml
from packaging import version as pkg_version


class SchemaVersionError(Exception):
    """Raised when schema version validation fails."""
    pass


class SchemaVersionValidator:
    """Validates schema versions in blueprints."""
    
    # Supported schema version range
    MIN_SUPPORTED_VERSION = "1.0.0"
    MAX_SUPPORTED_VERSION = "2.x"
    
    def __init__(self):
        self.supported_versions = self._parse_version_range()
    
    def _parse_version_range(self) -> List[str]:
        """Parse the supported version range into a list of supported versions."""
        # For now, support 1.0.0 through 1.9.9
        # In a real implementation, you'd have a more sophisticated version mapping
        supported = []
        for major in range(1, 2):  # 1.x series
            for minor in range(0, 10):  # 0-9
                for patch in range(0, 10):  # 0-9
                    supported.append(f"{major}.{minor}.{patch}")
        return supported
    
    def validate_blueprint(self, blueprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate schema version in a blueprint.
        
        Args:
            blueprint_data: Parsed blueprint data
            
        Returns:
            Validation result with details
            
        Raises:
            SchemaVersionError: If validation fails
        """
        result = {
            'valid': True,
            'schema_version': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if schema_version is present
            if 'system' not in blueprint_data:
                result['errors'].append("Blueprint missing 'system' section")
                result['valid'] = False
                return result
            
            system_section = blueprint_data['system']
            
            if 'schema_version' not in system_section:
                result['errors'].append("Blueprint missing required 'schema_version' field")
                result['valid'] = False
                return result
            
            schema_version = system_section['schema_version']
            result['schema_version'] = schema_version
            
            # Validate schema version format
            if not self._is_valid_version_format(schema_version):
                result['errors'].append(f"Invalid schema version format: {schema_version}")
                result['valid'] = False
                return result
            
            # Check if version is supported
            if not self._is_version_supported(schema_version):
                result['errors'].append(
                    f"Schema version {schema_version} is not supported. "
                    f"Supported range: {self.MIN_SUPPORTED_VERSION} - {self.MAX_SUPPORTED_VERSION}"
                )
                result['valid'] = False
                return result
            
            # Check for version-specific validation rules
            version_warnings = self._validate_version_specific_rules(schema_version, blueprint_data)
            result['warnings'].extend(version_warnings)
            
            if result['errors']:
                result['valid'] = False
                raise SchemaVersionError(f"Schema version validation failed: {'; '.join(result['errors'])}")
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
            result['valid'] = False
            return result
    
    def _is_valid_version_format(self, version_str: str) -> bool:
        """Check if version string follows semantic versioning format."""
        # Basic semantic versioning pattern: major.minor.patch
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version_str))
    
    def _is_version_supported(self, version_str: str) -> bool:
        """Check if version is within supported range."""
        try:
            version = pkg_version.parse(version_str)
            min_version = pkg_version.parse(self.MIN_SUPPORTED_VERSION)
            max_version = pkg_version.parse("2.0.0")  # 2.x means < 2.0.0
            
            return min_version <= version < max_version
        except pkg_version.InvalidVersion:
            return False
    
    def _validate_version_specific_rules(self, schema_version: str, blueprint_data: Dict[str, Any]) -> List[str]:
        """Apply version-specific validation rules."""
        warnings = []
        
        try:
            version = pkg_version.parse(schema_version)
            
            # Version 1.0.0 specific rules
            if version.major == 1 and version.minor == 0:
                warnings.extend(self._validate_v1_0_0_rules(blueprint_data))
            
            # Version 1.1.0+ specific rules
            if version >= pkg_version.parse("1.1.0"):
                warnings.extend(self._validate_v1_1_plus_rules(blueprint_data))
            
        except pkg_version.InvalidVersion:
            warnings.append(f"Could not parse schema version {schema_version} for specific validation")
        
        return warnings
    
    def _validate_v1_0_0_rules(self, blueprint_data: Dict[str, Any]) -> List[str]:
        """Validate rules specific to schema version 1.0.0."""
        warnings = []
        
        # Check for deprecated patterns in 1.0.0
        if 'components' in blueprint_data.get('system', {}):
            for component in blueprint_data['system']['components']:
                if 'config' in component:
                    warnings.append(
                        f"Component '{component.get('name', 'unknown')}' uses deprecated 'config' field. "
                        "Use 'configuration' instead."
                    )
        
        return warnings
    
    def _validate_v1_1_plus_rules(self, blueprint_data: Dict[str, Any]) -> List[str]:
        """Validate rules specific to schema version 1.1.0 and above."""
        warnings = []
        
        # Check for required fields in newer versions
        if 'components' in blueprint_data.get('system', {}):
            for component in blueprint_data['system']['components']:
                if 'configuration' not in component:
                    warnings.append(
                        f"Component '{component.get('name', 'unknown')}' missing 'configuration' field "
                        "required in schema version 1.1.0+"
                    )
        
        return warnings
    
    def get_migration_path(self, from_version: str, to_version: str) -> Optional[str]:
        """
        Get migration path between schema versions.
        
        Args:
            from_version: Current schema version
            to_version: Target schema version
            
        Returns:
            Migration instructions or None if no migration needed
        """
        try:
            from_ver = pkg_version.parse(from_version)
            to_ver = pkg_version.parse(to_version)
            
            if from_ver >= to_ver:
                return None  # No migration needed
            
            # Build migration path
            migrations = []
            
            # 1.0.0 to 1.1.0 migration
            if from_ver < pkg_version.parse("1.1.0") <= to_ver:
                migrations.append(
                    "1. Replace all 'config' fields with 'configuration' in component definitions"
                )
            
            # Add more migration steps as needed
            
            if migrations:
                return "\n".join(migrations)
            
            return None
            
        except pkg_version.InvalidVersion:
            return f"Invalid version format: {from_version} or {to_version}"


def validate_blueprint_file(filepath: Path) -> Dict[str, Any]:
    """
    Validate schema version in a blueprint file.
    
    Args:
        filepath: Path to blueprint file
        
    Returns:
        Validation result
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            blueprint_data = yaml.safe_load(f)
        
        validator = SchemaVersionValidator()
        result = validator.validate_blueprint(blueprint_data)
        result['file'] = str(filepath)
        
        return result
        
    except yaml.YAMLError as e:
        return {
            'file': str(filepath),
            'valid': False,
            'schema_version': None,
            'errors': [f"YAML parsing error: {str(e)}"],
            'warnings': []
        }
    except Exception as e:
        return {
            'file': str(filepath),
            'valid': False,
            'schema_version': None,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': []
        }


def validate_blueprint_directory(directory: Path, exclude_patterns: List[str] = None) -> Dict[str, Any]:
    """
    Validate schema versions in all blueprint files in a directory.
    
    Args:
        directory: Directory to scan
        exclude_patterns: Patterns to exclude
        
    Returns:
        Validation results for all files
    """
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            '.venv',
        ]
    
    results = {
        'directory': str(directory),
        'files_scanned': 0,
        'files_valid': 0,
        'files_invalid': 0,
        'total_errors': 0,
        'total_warnings': 0,
        'file_results': []
    }
    
    for filepath in directory.rglob('*.yaml'):
        if filepath.is_file():
            # Skip excluded patterns
            if any(pattern in str(filepath) for pattern in exclude_patterns):
                continue
            
            results['files_scanned'] += 1
            file_result = validate_blueprint_file(filepath)
            results['file_results'].append(file_result)
            
            if file_result['valid']:
                results['files_valid'] += 1
            else:
                results['files_invalid'] += 1
            
            results['total_errors'] += len(file_result['errors'])
            results['total_warnings'] += len(file_result['warnings'])
    
    # Also scan .yml files
    for filepath in directory.rglob('*.yml'):
        if filepath.is_file():
            # Skip excluded patterns
            if any(pattern in str(filepath) for pattern in exclude_patterns):
                continue
            
            results['files_scanned'] += 1
            file_result = validate_blueprint_file(filepath)
            results['file_results'].append(file_result)
            
            if file_result['valid']:
                results['files_valid'] += 1
            else:
                results['files_invalid'] += 1
            
            results['total_errors'] += len(file_result['errors'])
            results['total_warnings'] += len(file_result['warnings'])
    
    return results


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Validate schema versions in blueprint files')
    parser.add_argument('--file', '-f', help='Single blueprint file to validate')
    parser.add_argument('--directory', '-d', default='.', help='Directory to scan for blueprints')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    if args.file:
        # Validate single file
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File {filepath} does not exist")
            sys.exit(1)
        
        result = validate_blueprint_file(filepath)
        
        if args.output_format == 'json':
            import json
            print(json.dumps(result, indent=2))
        else:
            print(f"📄 {result['file']}")
            print(f"   Schema Version: {result['schema_version']}")
            print(f"   Valid: {'✅' if result['valid'] else '❌'}")
            
            if result['errors']:
                print("   Errors:")
                for error in result['errors']:
                    print(f"     ❌ {error}")
            
            if result['warnings']:
                print("   Warnings:")
                for warning in result['warnings']:
                    print(f"     ⚠️  {warning}")
        
        sys.exit(0 if result['valid'] else 1)
    
    else:
        # Validate directory
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory {directory} does not exist")
            sys.exit(1)
        
        results = validate_blueprint_directory(directory)
        
        if args.output_format == 'json':
            import json
            print(json.dumps(results, indent=2))
        else:
            print(f"📊 Schema Version Validation Results:")
            print(f"   Directory: {results['directory']}")
            print(f"   Files scanned: {results['files_scanned']}")
            print(f"   Files valid: {results['files_valid']}")
            print(f"   Files invalid: {results['files_invalid']}")
            print(f"   Total errors: {results['total_errors']}")
            print(f"   Total warnings: {results['total_warnings']}")
            print()
            
            if results['files_invalid'] > 0:
                print("❌ Invalid files:")
                for file_result in results['file_results']:
                    if not file_result['valid']:
                        print(f"   📁 {file_result['file']}")
                        for error in file_result['errors']:
                            print(f"      ❌ {error}")
                print()
            
            if results['total_warnings'] > 0:
                print("⚠️  Warnings:")
                for file_result in results['file_results']:
                    if file_result['warnings']:
                        print(f"   📁 {file_result['file']}")
                        for warning in file_result['warnings']:
                            print(f"      ⚠️  {warning}")
                print()
        
        sys.exit(0 if results['files_invalid'] == 0 else 1) 