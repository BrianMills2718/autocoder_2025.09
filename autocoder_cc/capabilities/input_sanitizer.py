from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Comprehensive Input Sanitization for APIEndpoint Components

This module provides enterprise-grade input validation and sanitization
to prevent injection attacks and ensure data integrity for API endpoints.

Implements Gemini-identified critical improvement:
"Additional input sanitization may be necessary for certain components,
particularly those exposed to external input (APIEndpoints)."
"""

import re
import html
import urllib.parse
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass
from enum import Enum
import bleach
from pydantic import BaseModel, Field, validator, ValidationError


class SanitizationType(Enum):
    """Types of input sanitization to apply"""
    HTML_ESCAPE = "html_escape"
    URL_ENCODE = "url_encode"
    SQL_ESCAPE = "sql_escape"
    SCRIPT_REMOVAL = "script_removal"
    WHITESPACE_NORMALIZE = "whitespace_normalize"
    LENGTH_LIMIT = "length_limit"
    PATTERN_VALIDATE = "pattern_validate"
    XSS_PREVENTION = "xss_prevention"
    JSON_SANITIZE = "json_sanitize"


class ValidationSeverity(Enum):
    """Severity levels for validation violations"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationViolation:
    """Represents an input validation violation"""
    field_name: str
    violation_type: str
    severity: ValidationSeverity
    description: str
    original_value: Any
    sanitized_value: Any
    context: Dict[str, Any]


class InputSanitizationError(Exception):
    """Raised when input sanitization fails critically"""
    def __init__(self, message: str, violations: List[ValidationViolation]):
        super().__init__(message)
        self.violations = violations


class InputSanitizer:
    """
    Comprehensive input sanitization for API endpoints.
    
    Provides multi-layered defense against:
    - SQL injection attacks
    - XSS attacks
    - Command injection
    - Path traversal attacks
    - Buffer overflow attempts
    - Malformed data attacks
    """
    
    def __init__(self, strict_mode: bool = True, max_string_length: int = 10000):
        self.logger = get_logger("InputSanitizer")
        self.strict_mode = strict_mode
        self.max_string_length = max_string_length
        self.violations: List[ValidationViolation] = []
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"].*['\"])",
            r"(SCRIPT|IFRAME|OBJECT|EMBED|APPLET)",
            r"(javascript:|data:|vbscript:)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/passwd",
            r"/proc/",
            r"\\windows\\",
            r"C:\\",
        ]
        
        # Command injection patterns
        self.command_injection_patterns = [
            r"[;&|`$]",
            r"\b(rm|del|format|fdisk)\b",
            r">\s*/dev/null",
            r"\|\s*sh",
            r"\|\s*bash",
        ]
        
        # Allowed HTML tags for sanitized HTML input
        self.allowed_html_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        self.allowed_html_attributes = {'*': ['class']}
    
    def sanitize_input(self, data: Any, field_name: str = "input", 
                      sanitization_types: List[SanitizationType] = None) -> Any:
        """
        Sanitize input data with comprehensive validation.
        
        Args:
            data: Input data to sanitize
            field_name: Name of the field for error reporting
            sanitization_types: List of sanitization types to apply
            
        Returns:
            Sanitized data
            
        Raises:
            InputSanitizationError: If critical violations found in strict mode
        """
        if sanitization_types is None:
            sanitization_types = [
                SanitizationType.XSS_PREVENTION,
                SanitizationType.SQL_ESCAPE,
                SanitizationType.SCRIPT_REMOVAL,
                SanitizationType.LENGTH_LIMIT,
                SanitizationType.WHITESPACE_NORMALIZE
            ]
        
        try:
            sanitized_data = self._sanitize_recursive(data, field_name, sanitization_types)
            
            # Check for critical violations
            critical_violations = [v for v in self.violations if v.severity == ValidationSeverity.CRITICAL]
            if self.strict_mode and critical_violations:
                raise InputSanitizationError(
                    f"Critical input validation violations detected: {len(critical_violations)} issues",
                    critical_violations
                )
            
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Input sanitization failed for {field_name}: {e}")
            if self.strict_mode:
                raise
            return data  # Return original data if not in strict mode
    
    def _sanitize_recursive(self, data: Any, field_path: str, 
                           sanitization_types: List[SanitizationType]) -> Any:
        """Recursively sanitize nested data structures"""
        if isinstance(data, dict):
            return {
                key: self._sanitize_recursive(
                    value, f"{field_path}.{key}", sanitization_types
                )
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                self._sanitize_recursive(
                    item, f"{field_path}[{i}]", sanitization_types
                )
                for i, item in enumerate(data)
            ]
        elif isinstance(data, str):
            return self._sanitize_string(data, field_path, sanitization_types)
        else:
            return data  # Numbers, booleans, etc. are generally safe
    
    def _sanitize_string(self, value: str, field_path: str, 
                        sanitization_types: List[SanitizationType]) -> str:
        """Sanitize string values with multiple protection layers"""
        original_value = value
        sanitized_value = value
        
        # Apply each sanitization type
        for sanitization_type in sanitization_types:
            try:
                if sanitization_type == SanitizationType.LENGTH_LIMIT:
                    sanitized_value = self._apply_length_limit(sanitized_value, field_path)
                
                elif sanitization_type == SanitizationType.WHITESPACE_NORMALIZE:
                    sanitized_value = self._normalize_whitespace(sanitized_value)
                
                elif sanitization_type == SanitizationType.HTML_ESCAPE:
                    sanitized_value = html.escape(sanitized_value)
                
                elif sanitization_type == SanitizationType.URL_ENCODE:
                    sanitized_value = urllib.parse.quote(sanitized_value, safe='')
                
                elif sanitization_type == SanitizationType.SQL_ESCAPE:
                    sanitized_value = self._escape_sql_injection(sanitized_value, field_path)
                
                elif sanitization_type == SanitizationType.XSS_PREVENTION:
                    sanitized_value = self._prevent_xss(sanitized_value, field_path)
                
                elif sanitization_type == SanitizationType.SCRIPT_REMOVAL:
                    sanitized_value = self._remove_scripts(sanitized_value, field_path)
                
                elif sanitization_type == SanitizationType.JSON_SANITIZE:
                    sanitized_value = self._sanitize_json_string(sanitized_value, field_path)
                
            except Exception as e:
                self._record_violation(
                    field_path,
                    f"sanitization_error_{sanitization_type.value}",
                    ValidationSeverity.ERROR,
                    f"Failed to apply {sanitization_type.value}: {e}",
                    original_value,
                    sanitized_value,
                    {"error": str(e), "sanitization_type": sanitization_type.value}
                )
        
        return sanitized_value
    
    def _apply_length_limit(self, value: str, field_path: str) -> str:
        """Apply length limits to prevent buffer overflow attacks"""
        if len(value) > self.max_string_length:
            self._record_violation(
                field_path,
                "length_limit_exceeded",
                ValidationSeverity.WARNING,
                f"String length {len(value)} exceeds maximum {self.max_string_length}",
                value,
                value[:self.max_string_length],
                {"original_length": len(value), "max_length": self.max_string_length}
            )
            return value[:self.max_string_length]
        return value
    
    def _normalize_whitespace(self, value: str) -> str:
        """Normalize whitespace to prevent hidden character attacks"""
        # Replace various whitespace characters with regular spaces
        normalized = re.sub(r'\s+', ' ', value.strip())
        
        # Remove null bytes and other control characters
        normalized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', normalized)
        
        return normalized
    
    def _escape_sql_injection(self, value: str, field_path: str) -> str:
        """Detect and prevent SQL injection attacks"""
        for pattern in self.sql_injection_patterns:
            matches = re.findall(pattern, value, re.IGNORECASE)
            if matches:
                self._record_violation(
                    field_path,
                    "sql_injection_attempt",
                    ValidationSeverity.CRITICAL,
                    f"Potential SQL injection detected: {matches}",
                    value,
                    value,  # Don't modify yet, just flag
                    {"pattern": pattern, "matches": matches}
                )
        
        # Escape single quotes for SQL safety
        escaped = value.replace("'", "''")
        return escaped
    
    def _prevent_xss(self, value: str, field_path: str) -> str:
        """Detect and prevent XSS attacks"""
        for pattern in self.xss_patterns:
            matches = re.findall(pattern, value, re.IGNORECASE | re.DOTALL)
            if matches:
                self._record_violation(
                    field_path,
                    "xss_attempt",
                    ValidationSeverity.CRITICAL,
                    f"Potential XSS attack detected: {matches}",
                    value,
                    value,  # Don't modify yet, just flag
                    {"pattern": pattern, "matches": matches}
                )
        
        # Use bleach for comprehensive XSS prevention
        cleaned = bleach.clean(
            value,
            tags=self.allowed_html_tags,
            attributes=self.allowed_html_attributes,
            strip=True
        )
        
        return cleaned
    
    def _remove_scripts(self, value: str, field_path: str) -> str:
        """Remove script tags and dangerous content"""
        # Remove script tags
        no_scripts = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: and data: URLs
        no_js_urls = re.sub(r'(javascript|data|vbscript):[^"\'>\s]*', '', no_scripts, flags=re.IGNORECASE)
        
        # Remove event handlers
        no_events = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', no_js_urls, flags=re.IGNORECASE)
        
        return no_events
    
    def _sanitize_json_string(self, value: str, field_path: str) -> str:
        """Sanitize JSON string content"""
        try:
            # Try to parse as JSON to validate structure
            parsed = json.loads(value)
            
            # Re-serialize with safe encoding
            sanitized = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
            return sanitized
            
        except json.JSONDecodeError:
            # Not valid JSON, treat as regular string
            return value
    
    def _check_path_traversal(self, value: str, field_path: str) -> str:
        """Check for path traversal attempts"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                self._record_violation(
                    field_path,
                    "path_traversal_attempt",
                    ValidationSeverity.CRITICAL,
                    f"Path traversal pattern detected: {pattern}",
                    value,
                    value,
                    {"pattern": pattern}
                )
        return value
    
    def _check_command_injection(self, value: str, field_path: str) -> str:
        """Check for command injection attempts"""
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                self._record_violation(
                    field_path,
                    "command_injection_attempt",
                    ValidationSeverity.CRITICAL,
                    f"Command injection pattern detected: {pattern}",
                    value,
                    value,
                    {"pattern": pattern}
                )
        return value
    
    def _record_violation(self, field_name: str, violation_type: str, 
                         severity: ValidationSeverity, description: str,
                         original_value: Any, sanitized_value: Any, 
                         context: Dict[str, Any]):
        """Record a validation violation"""
        violation = ValidationViolation(
            field_name=field_name,
            violation_type=violation_type,
            severity=severity,
            description=description,
            original_value=original_value,
            sanitized_value=sanitized_value,
            context=context
        )
        
        self.violations.append(violation)
        
        # Log the violation using structured logger methods
        message = f"Input validation violation: {description} in field {field_name}"
        
        if severity == ValidationSeverity.INFO:
            self.logger.info(message)
        elif severity == ValidationSeverity.WARNING:
            self.logger.warning(message)
        elif severity == ValidationSeverity.ERROR:
            self.logger.error(message)
        elif severity == ValidationSeverity.CRITICAL:
            self.logger.critical(message)
    
    def validate_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-level validation for API request data.
        
        Args:
            request_data: Raw request data from API endpoint
            
        Returns:
            Sanitized request data
            
        Raises:
            InputSanitizationError: If critical violations found
        """
        self.violations.clear()
        
        # Apply comprehensive sanitization
        sanitized_data = self.sanitize_input(
            request_data,
            "request",
            [
                SanitizationType.LENGTH_LIMIT,
                SanitizationType.WHITESPACE_NORMALIZE,
                SanitizationType.XSS_PREVENTION,
                SanitizationType.SQL_ESCAPE,
                SanitizationType.SCRIPT_REMOVAL
            ]
        )
        
        # Additional validation for common fields
        if isinstance(sanitized_data, dict):
            for field_name, field_value in sanitized_data.items():
                if isinstance(field_value, str):
                    # Check for path traversal in all string fields
                    self._check_path_traversal(field_value, field_name)
                    
                    # Check for command injection in all string fields
                    self._check_command_injection(field_value, field_name)
        
        return sanitized_data
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation violations"""
        summary = {
            "total_violations": len(self.violations),
            "by_severity": {},
            "by_type": {},
            "critical_count": 0,
            "violations": []
        }
        
        for violation in self.violations:
            # Count by severity
            severity_name = violation.severity.value
            summary["by_severity"][severity_name] = summary["by_severity"].get(severity_name, 0) + 1
            
            # Count by type
            summary["by_type"][violation.violation_type] = summary["by_type"].get(violation.violation_type, 0) + 1
            
            # Count critical violations
            if violation.severity == ValidationSeverity.CRITICAL:
                summary["critical_count"] += 1
            
            # Add violation details
            summary["violations"].append({
                "field": violation.field_name,
                "type": violation.violation_type,
                "severity": severity_name,
                "description": violation.description,
                "context": violation.context
            })
        
        return summary


def sanitize_api_input(data: Any, strict_mode: bool = True) -> Any:
    """
    Convenience function for API input sanitization.
    
    Args:
        data: Input data to sanitize
        strict_mode: Whether to raise exceptions on critical violations
        
    Returns:
        Sanitized data
        
    Raises:
        InputSanitizationError: If critical violations found in strict mode
    """
    sanitizer = InputSanitizer(strict_mode=strict_mode)
    return sanitizer.sanitize_input(data)


def validate_json_request(request_json: str) -> Dict[str, Any]:
    """
    Validate and sanitize JSON request data.
    
    Args:
        request_json: JSON string from request
        
    Returns:
        Parsed and sanitized JSON data
        
    Raises:
        InputSanitizationError: If validation fails
    """
    try:
        # Parse JSON
        data = json.loads(request_json)
        
        # Sanitize the parsed data
        sanitizer = InputSanitizer(strict_mode=True)
        return sanitizer.validate_request_data(data)
        
    except json.JSONDecodeError as e:
        raise InputSanitizationError(
            f"Invalid JSON format: {e}",
            [ValidationViolation(
                field_name="json_body",
                violation_type="invalid_json",
                severity=ValidationSeverity.CRITICAL,
                description=f"JSON parsing failed: {e}",
                original_value=request_json,
                sanitized_value=None,
                context={"error": str(e)}
            )]
        )