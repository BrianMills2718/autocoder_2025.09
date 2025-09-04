"""
Input Validation Framework - Task 16 Security Implementation

Comprehensive input validation and sanitization for all user inputs,
blueprint configurations, file paths, and dependency specifications.
"""

import re
import os
import ast
import json
import yaml
import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import subprocess
import pkg_resources
from packaging import version

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: Any
    violations: List[str]
    risk_level: str  # low, medium, high, critical
    remediation_actions: List[str]


@dataclass
class SecurityViolation:
    """Security violation details"""
    violation_type: str
    severity: str
    description: str
    location: Optional[str]
    remediation: str


class InputValidator:
    """Comprehensive input validation and sanitization framework"""
    
    # Dangerous patterns for code injection detection
    DANGEROUS_CODE_PATTERNS = [
        r'exec\s*\(',
        r'eval\s*\(',
        r'compile\s*\(',
        r'__import__\s*\(',
        r'globals\s*\(\)',
        r'locals\s*\(\)',
        r'getattr\s*\(',
        r'setattr\s*\(',
        r'delattr\s*\(',
        r'hasattr\s*\(',
        r'vars\s*\(',
        r'dir\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
        r'os\.system',
        r'os\.popen',
        r'os\.spawn',
        r'os\.execv',
        r'subprocess\.',
        r'commands\.',
        r'pickle\.loads',
        r'marshal\.loads',
        r'dill\.loads',
        r'shelve\.',
        r'socket\.',
        r'urllib\.request\.urlopen',
        r'urllib\.urlopen',
        r'httplib\.',
        r'ftplib\.',
        r'telnetlib\.',
        r'smtplib\.',
        r'poplib\.',
        r'imaplib\.',
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"'\s*OR\s+'.*'=.*'",
        r'"\s*OR\s+".*"=.*"',
        r"'\s*OR\s+1\s*=\s*1",
        r'"\s*OR\s+1\s*=\s*1',
        r"'\s*;\s*DROP\s+",
        r'"\s*;\s*DROP\s+',
        r"'\s*UNION\s+",
        r'"\s*UNION\s+',
        r"'\s*INSERT\s+",
        r'"\s*INSERT\s+',
        r"'\s*UPDATE\s+",
        r'"\s*UPDATE\s+',
        r"'\s*DELETE\s+",
        r'"\s*DELETE\s+',
        r"'\s*CREATE\s+",
        r'"\s*CREATE\s+',
        r"'\s*ALTER\s+",
        r'"\s*ALTER\s+',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'<\/script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<applet[^>]*>',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.\/',
        r'\.\.\\',
        r'\.\.%2f',
        r'\.\.%2F',
        r'\.\.%5c',
        r'\.\.%5C',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'..%252f',
        r'..%255c',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r';\s*rm\s+-rf',
        r';\s*cat\s+/etc/',
        r';\s*ls\s+-la',
        r';\s*ps\s+aux',
        r';\s*netstat',
        r';\s*wget\s+',
        r';\s*curl\s+',
        r';\s*nc\s+',
        r';\s*telnet\s+',
        r';\s*ssh\s+',
        r'\|\s*nc\s+',
        r'\|\s*telnet\s+',
        r'\|\s*sh\s*$',
        r'\|\s*bash\s*$',
        r'&&\s*rm\s+-rf',
        r'&\s*rm\s+-rf',
    ]
    
    # Allowed file extensions for different contexts
    ALLOWED_EXTENSIONS = {
        'blueprint': {'.yaml', '.yml', '.json'},
        'component': {'.py', '.js', '.ts', '.java', '.go', '.rs'},
        'config': {'.yaml', '.yml', '.json', '.toml', '.ini', '.env'},
        'deployment': {'.yaml', '.yml', '.json'},
        'documentation': {'.md', '.rst', '.txt'},
    }
    
    # Maximum sizes for different input types
    MAX_SIZES = {
        'blueprint_size': 10 * 1024 * 1024,  # 10MB
        'component_code_size': 5 * 1024 * 1024,  # 5MB
        'config_size': 1 * 1024 * 1024,  # 1MB
        'string_length': 10000,
        'nested_depth': 10,
        'array_length': 1000,
    }
    
    # Known vulnerable package versions
    VULNERABLE_PACKAGES = {
        'django': ['<3.2.13', '<4.0.4'],
        'flask': ['<2.0.3'],
        'requests': ['<2.28.0'],
        'urllib3': ['<1.26.12'],
        'pillow': ['<9.0.1'],
        'pyyaml': ['<6.0'],
        'jinja2': ['<3.0.3'],
        'werkzeug': ['<2.0.3'],
        'sqlalchemy': ['<1.4.37'],
        'psycopg2': ['<2.8.6'],
    }
    
    def __init__(self):
        """Initialize input validator"""
        self.validation_cache = {}
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for performance"""
        return {
            'dangerous_code': [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_CODE_PATTERNS],
            'sql_injection': [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS],
            'xss': [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS],
            'path_traversal': [re.compile(pattern, re.IGNORECASE) for pattern in self.PATH_TRAVERSAL_PATTERNS],
            'command_injection': [re.compile(pattern, re.IGNORECASE) for pattern in self.COMMAND_INJECTION_PATTERNS],
        }
    
    def validate_blueprint(self, blueprint: Union[str, Dict[str, Any]]) -> ValidationResult:
        """Validate system blueprint input"""
        violations = []
        remediation_actions = []
        
        try:
            # Convert string to dict if needed
            if isinstance(blueprint, str):
                # Check size limits
                if len(blueprint) > self.MAX_SIZES['blueprint_size']:
                    violations.append(f"Blueprint size exceeds limit: {len(blueprint)} > {self.MAX_SIZES['blueprint_size']}")
                
                # Parse blueprint
                try:
                    if blueprint.strip().startswith('{'):
                        parsed_blueprint = json.loads(blueprint)
                    else:
                        parsed_blueprint = yaml.safe_load(blueprint)
                except (json.JSONDecodeError, yaml.YAMLError) as e:
                    violations.append(f"Invalid blueprint format: {e}")
                    return ValidationResult(
                        is_valid=False,
                        sanitized_input=None,
                        violations=violations,
                        risk_level="high",
                        remediation_actions=["Fix blueprint format errors"]
                    )
            else:
                parsed_blueprint = blueprint
            
            # Validate blueprint structure
            structure_violations = self._validate_blueprint_structure(parsed_blueprint)
            violations.extend(structure_violations)
            
            # Sanitize blueprint content
            sanitized_blueprint = self._sanitize_blueprint_content(parsed_blueprint, violations, remediation_actions)
            
            # Validate nesting depth
            depth_violations = self._validate_nesting_depth(sanitized_blueprint, max_depth=self.MAX_SIZES['nested_depth'])
            violations.extend(depth_violations)
            
            # Determine risk level
            risk_level = self._calculate_risk_level(violations)
            
            return ValidationResult(
                is_valid=len(violations) == 0,
                sanitized_input=sanitized_blueprint,
                violations=violations,
                risk_level=risk_level,
                remediation_actions=remediation_actions
            )
            
        except Exception as e:
            logger.error(f"Blueprint validation error: {e}")
            return ValidationResult(
                is_valid=False,
                sanitized_input=None,
                violations=[f"Validation error: {e}"],
                risk_level="critical",
                remediation_actions=["Review blueprint format and content"]
            )
    
    def validate_component_code(self, code: str, language: str = "python") -> ValidationResult:
        """Validate component code for security issues"""
        violations = []
        remediation_actions = []
        
        # Check size limits
        if len(code) > self.MAX_SIZES['component_code_size']:
            violations.append(f"Code size exceeds limit: {len(code)} > {self.MAX_SIZES['component_code_size']}")
        
        # Check for dangerous code patterns
        code_violations = self._detect_dangerous_code_patterns(code)
        violations.extend(code_violations)
        
        # Language-specific validation
        if language.lower() == "python":
            python_violations = self._validate_python_code(code)
            violations.extend(python_violations)
        
        # Sanitize code
        sanitized_code = self._sanitize_code(code, violations, remediation_actions)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(violations)
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_input=sanitized_code,
            violations=violations,
            risk_level=risk_level,
            remediation_actions=remediation_actions
        )
    
    def validate_file_path(self, file_path: str, context: str = "general") -> ValidationResult:
        """Validate file path for security issues"""
        violations = []
        remediation_actions = []
        
        # Check for path traversal
        traversal_violations = self._detect_path_traversal(file_path)
        violations.extend(traversal_violations)
        
        # Validate file extension
        if context in self.ALLOWED_EXTENSIONS:
            allowed_extensions = self.ALLOWED_EXTENSIONS[context]
            file_extension = Path(file_path).suffix.lower()
            if file_extension and file_extension not in allowed_extensions:
                violations.append(f"File extension '{file_extension}' not allowed for context '{context}'")
                remediation_actions.append(f"Use allowed extensions: {', '.join(allowed_extensions)}")
        
        # Check for dangerous file names
        dangerous_names = ['passwd', 'shadow', 'hosts', 'fstab', 'crontab', 'sudoers']
        filename = Path(file_path).name.lower()
        if any(dangerous in filename for dangerous in dangerous_names):
            violations.append(f"Potentially dangerous file name: {filename}")
            remediation_actions.append("Avoid accessing system files")
        
        # Normalize and sanitize path
        sanitized_path = self._sanitize_file_path(file_path)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(violations)
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_input=sanitized_path,
            violations=violations,
            risk_level=risk_level,
            remediation_actions=remediation_actions
        )
    
    def validate_dependencies(self, dependencies: Union[str, List[str], Dict[str, str]]) -> ValidationResult:
        """Validate dependency specifications"""
        violations = []
        remediation_actions = []
        
        try:
            # Convert to standardized format
            if isinstance(dependencies, str):
                # Parse requirements.txt format
                dep_list = [line.strip() for line in dependencies.split('\n') if line.strip() and not line.startswith('#')]
            elif isinstance(dependencies, list):
                dep_list = dependencies
            elif isinstance(dependencies, dict):
                dep_list = [f"{name}{version}" for name, version in dependencies.items()]
            else:
                violations.append("Invalid dependencies format")
                return ValidationResult(
                    is_valid=False,
                    sanitized_input=None,
                    violations=violations,
                    risk_level="high",
                    remediation_actions=["Use valid dependency format"]
                )
            
            # Validate each dependency
            sanitized_dependencies = []
            for dep in dep_list:
                dep_violations, sanitized_dep = self._validate_single_dependency(dep)
                violations.extend(dep_violations)
                if sanitized_dep:
                    sanitized_dependencies.append(sanitized_dep)
            
            # Check for known vulnerabilities
            vuln_violations = self._check_vulnerability_database(sanitized_dependencies)
            violations.extend(vuln_violations)
            
            # Determine risk level
            risk_level = self._calculate_risk_level(violations)
            
            return ValidationResult(
                is_valid=len(violations) == 0,
                sanitized_input=sanitized_dependencies,
                violations=violations,
                risk_level=risk_level,
                remediation_actions=remediation_actions
            )
            
        except Exception as e:
            logger.error(f"Dependency validation error: {e}")
            return ValidationResult(
                is_valid=False,
                sanitized_input=None,
                violations=[f"Validation error: {e}"],
                risk_level="critical",
                remediation_actions=["Review dependency specifications"]
            )
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration for security issues"""
        violations = []
        remediation_actions = []
        
        # Check for secrets in configuration
        secrets_violations = self._detect_secrets_in_config(config)
        violations.extend(secrets_violations)
        
        # Validate URLs and endpoints
        url_violations = self._validate_urls_in_config(config)
        violations.extend(url_violations)
        
        # Check for dangerous configurations
        danger_violations = self._detect_dangerous_configurations(config)
        violations.extend(danger_violations)
        
        # Sanitize configuration
        sanitized_config = self._sanitize_configuration(config, violations, remediation_actions)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(violations)
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_input=sanitized_config,
            violations=violations,
            risk_level=risk_level,
            remediation_actions=remediation_actions
        )
    
    def _validate_blueprint_structure(self, blueprint: Dict[str, Any]) -> List[str]:
        """Validate blueprint structure"""
        violations = []
        
        # Required sections
        required_sections = ['system', 'components', 'connections', 'deployment']
        for section in required_sections:
            if section not in blueprint:
                violations.append(f"Missing required section: {section}")
        
        # Validate system section
        if 'system' in blueprint:
            system = blueprint['system']
            if not isinstance(system, dict):
                violations.append("System section must be a dictionary")
            else:
                required_system_fields = ['name', 'version']
                for field in required_system_fields:
                    if field not in system:
                        violations.append(f"Missing required system field: {field}")
                    elif not isinstance(system[field], str):
                        violations.append(f"System field '{field}' must be a string")
                    elif len(system[field]) > self.MAX_SIZES['string_length']:
                        violations.append(f"System field '{field}' exceeds maximum length")
        
        # Validate components section
        if 'components' in blueprint:
            components = blueprint['components']
            if not isinstance(components, list):
                violations.append("Components section must be a list")
            elif len(components) > self.MAX_SIZES['array_length']:
                violations.append(f"Too many components: {len(components)} > {self.MAX_SIZES['array_length']}")
            else:
                for i, component in enumerate(components):
                    if not isinstance(component, dict):
                        violations.append(f"Component {i} must be a dictionary")
                    else:
                        component_violations = self._validate_component_structure(component, i)
                        violations.extend(component_violations)
        
        return violations
    
    def _validate_component_structure(self, component: Dict[str, Any], index: int) -> List[str]:
        """Validate individual component structure"""
        violations = []
        
        required_fields = ['name', 'type', 'description']
        for field in required_fields:
            if field not in component:
                violations.append(f"Component {index} missing required field: {field}")
            elif not isinstance(component[field], str):
                violations.append(f"Component {index} field '{field}' must be a string")
        
        # Validate component type
        if 'type' in component:
            valid_types = ['source', 'transformer', 'store', 'sink', 'router', 'filter', 'aggregator']
            if component['type'].lower() not in valid_types:
                violations.append(f"Component {index} has invalid type: {component['type']}")
        
        return violations
    
    def _sanitize_blueprint_content(self, blueprint: Dict[str, Any], violations: List[str], remediation_actions: List[str]) -> Dict[str, Any]:
        """Sanitize blueprint content"""
        sanitized = {}
        
        for key, value in blueprint.items():
            if isinstance(value, str):
                sanitized_value = self._sanitize_string(value, violations, remediation_actions)
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_blueprint_content(value, violations, remediation_actions)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_blueprint_content(item, violations, remediation_actions) if isinstance(item, dict)
                    else self._sanitize_string(item, violations, remediation_actions) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_string(self, text: str, violations: List[str], remediation_actions: List[str]) -> str:
        """Sanitize string content"""
        original_text = text
        
        # Remove XSS patterns
        for pattern in self.compiled_patterns['xss']:
            if pattern.search(text):
                violations.append(f"Removed XSS pattern: {pattern.pattern}")
                remediation_actions.append("Remove or escape HTML/JavaScript content")
                text = pattern.sub('', text)
        
        # Remove SQL injection patterns
        for pattern in self.compiled_patterns['sql_injection']:
            if pattern.search(text):
                violations.append(f"Removed SQL injection pattern: {pattern.pattern}")
                remediation_actions.append("Use parameterized queries")
                text = pattern.sub('', text)
        
        # Remove command injection patterns
        for pattern in self.compiled_patterns['command_injection']:
            if pattern.search(text):
                violations.append(f"Removed command injection pattern: {pattern.pattern}")
                remediation_actions.append("Avoid shell command execution")
                text = pattern.sub('', text)
        
        # Limit length
        if len(text) > self.MAX_SIZES['string_length']:
            text = text[:self.MAX_SIZES['string_length']]
            violations.append(f"Truncated string from {len(original_text)} to {self.MAX_SIZES['string_length']} characters")
        
        return text
    
    def _detect_dangerous_code_patterns(self, code: str) -> List[str]:
        """Detect dangerous code patterns"""
        violations = []
        
        for pattern in self.compiled_patterns['dangerous_code']:
            matches = pattern.findall(code)
            if matches:
                violations.append(f"Dangerous code pattern detected: {pattern.pattern}")
        
        return violations
    
    def _validate_python_code(self, code: str) -> List[str]:
        """Validate Python code syntax and safety"""
        violations = []
        
        try:
            # Parse AST for syntax validation
            tree = ast.parse(code)
            
            # Check for dangerous AST nodes
            dangerous_nodes = {
                ast.Import: "import statements",
                ast.ImportFrom: "from-import statements", 
                ast.Exec: "exec statements",
                ast.Eval: "eval statements",
            }
            
            for node in ast.walk(tree):
                node_type = type(node)
                if node_type in dangerous_nodes:
                    if hasattr(node, 'names'):
                        for alias in node.names:
                            module_name = alias.name
                            if module_name in ['os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib']:
                                violations.append(f"Dangerous module import: {module_name}")
                    elif hasattr(node, 'module'):
                        if node.module in ['os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib']:
                            violations.append(f"Dangerous module import: {node.module}")
                
        except SyntaxError as e:
            violations.append(f"Python syntax error: {e}")
        
        return violations
    
    def _detect_path_traversal(self, file_path: str) -> List[str]:
        """Detect path traversal attempts"""
        violations = []
        
        for pattern in self.compiled_patterns['path_traversal']:
            if pattern.search(file_path):
                violations.append(f"Path traversal pattern detected: {pattern.pattern}")
        
        # Check for absolute paths to sensitive directories
        sensitive_paths = ['/etc', '/root', '/home', '/var', '/usr/bin', '/usr/sbin', '/bin', '/sbin']
        normalized_path = os.path.normpath(file_path)
        
        for sensitive in sensitive_paths:
            if normalized_path.startswith(sensitive):
                violations.append(f"Access to sensitive directory: {sensitive}")
        
        return violations
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file path"""
        # Remove path traversal sequences
        sanitized = file_path
        for pattern in self.compiled_patterns['path_traversal']:
            sanitized = pattern.sub('', sanitized)
        
        # Normalize path
        sanitized = os.path.normpath(sanitized)
        
        # Ensure path is relative
        if os.path.isabs(sanitized):
            sanitized = os.path.relpath(sanitized)
        
        return sanitized
    
    def _validate_single_dependency(self, dependency: str) -> Tuple[List[str], Optional[str]]:
        """Validate a single dependency specification"""
        violations = []
        
        # Parse dependency specification
        dep_pattern = re.compile(r'^([a-zA-Z0-9_-]+)([<>=!]+[0-9.]+.*)?$')
        match = dep_pattern.match(dependency.strip())
        
        if not match:
            violations.append(f"Invalid dependency format: {dependency}")
            return violations, None
        
        package_name, version_spec = match.groups()
        
        # Check for suspicious package names
        suspicious_patterns = [
            r'.*password.*',
            r'.*secret.*',
            r'.*token.*',
            r'.*hack.*',
            r'.*exploit.*',
            r'.*backdoor.*',
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, package_name, re.IGNORECASE):
                violations.append(f"Suspicious package name: {package_name}")
        
        # Check for typosquatting (common misspellings)
        legitimate_packages = {'requests', 'numpy', 'pandas', 'flask', 'django', 'pytest'}
        for legit in legitimate_packages:
            if self._is_similar(package_name.lower(), legit.lower()) and package_name.lower() != legit.lower():
                violations.append(f"Possible typosquatting: {package_name} (similar to {legit})")
        
        return violations, dependency if not violations else None
    
    def _is_similar(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar (simple implementation)"""
        if len(str1) == 0 or len(str2) == 0:
            return False
        
        # Simple character overlap check
        set1, set2 = set(str1), set(str2)
        overlap = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return overlap / union >= threshold
    
    def _check_vulnerability_database(self, dependencies: List[str]) -> List[str]:
        """Check dependencies against vulnerability database"""
        violations = []
        
        for dep in dependencies:
            # Parse package name and version
            dep_pattern = re.compile(r'^([a-zA-Z0-9_-]+)([<>=!]+[0-9.]+.*)?$')
            match = dep_pattern.match(dep.strip())
            
            if match:
                package_name, version_spec = match.groups()
                
                if package_name.lower() in self.VULNERABLE_PACKAGES:
                    vulnerable_versions = self.VULNERABLE_PACKAGES[package_name.lower()]
                    
                    if version_spec:
                        # Extract version number
                        version_match = re.search(r'[0-9.]+', version_spec)
                        if version_match:
                            dep_version = version_match.group()
                            
                            # Check against vulnerable versions
                            for vuln_version in vulnerable_versions:
                                if self._version_matches_constraint(dep_version, vuln_version):
                                    violations.append(f"Vulnerable package version: {package_name} {dep_version} matches {vuln_version}")
                    else:
                        violations.append(f"Package {package_name} has known vulnerabilities, specify version")
        
        return violations
    
    def _version_matches_constraint(self, version_str: str, constraint: str) -> bool:
        """Check if version matches vulnerability constraint"""
        try:
            dep_version = version.parse(version_str)
            
            if constraint.startswith('<'):
                constraint_version = version.parse(constraint[1:])
                return dep_version < constraint_version
            elif constraint.startswith('<='):
                constraint_version = version.parse(constraint[2:])
                return dep_version <= constraint_version
            elif constraint.startswith('>'):
                constraint_version = version.parse(constraint[1:])
                return dep_version > constraint_version
            elif constraint.startswith('>='):
                constraint_version = version.parse(constraint[2:])
                return dep_version >= constraint_version
            elif constraint.startswith('=='):
                constraint_version = version.parse(constraint[2:])
                return dep_version == constraint_version
            
            return False
        except Exception:
            return False
    
    def _detect_secrets_in_config(self, config: Dict[str, Any]) -> List[str]:
        """Detect secrets in configuration"""
        violations = []
        
        secret_patterns = [
            (r'password\s*[=:]\s*["\']?[^"\'\s]+', 'password'),
            (r'secret\s*[=:]\s*["\']?[^"\'\s]+', 'secret'),
            (r'token\s*[=:]\s*["\']?[^"\'\s]+', 'token'),
            (r'key\s*[=:]\s*["\']?[^"\'\s]+', 'key'),
            (r'api_key\s*[=:]\s*["\']?[^"\'\s]+', 'api_key'),
            (r'access_key\s*[=:]\s*["\']?[^"\'\s]+', 'access_key'),
            (r'private_key\s*[=:]\s*["\']?[^"\'\s]+', 'private_key'),
        ]
        
        config_str = json.dumps(config)
        
        for pattern, secret_type in secret_patterns:
            if re.search(pattern, config_str, re.IGNORECASE):
                violations.append(f"Detected {secret_type} in configuration")
        
        return violations
    
    def _validate_urls_in_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate URLs in configuration"""
        violations = []
        
        def check_urls_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    check_urls_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    check_urls_recursive(item, current_path)
            elif isinstance(obj, str):
                if self._looks_like_url(obj):
                    url_violations = self._validate_url(obj, path)
                    violations.extend(url_violations)
        
        check_urls_recursive(config)
        return violations
    
    def _looks_like_url(self, text: str) -> bool:
        """Check if text looks like a URL"""
        return text.startswith(('http://', 'https://', 'ftp://', 'ftps://'))
    
    def _validate_url(self, url: str, path: str) -> List[str]:
        """Validate individual URL"""
        violations = []
        
        try:
            parsed = urlparse(url)
            
            # Check for dangerous schemes
            dangerous_schemes = ['file', 'javascript', 'data']
            if parsed.scheme.lower() in dangerous_schemes:
                violations.append(f"Dangerous URL scheme at {path}: {parsed.scheme}")
            
            # Check for localhost/internal IPs
            if parsed.hostname:
                internal_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
                if parsed.hostname.lower() in internal_hosts:
                    violations.append(f"Internal hostname in URL at {path}: {parsed.hostname}")
                
                # Check for private IP ranges
                if self._is_private_ip(parsed.hostname):
                    violations.append(f"Private IP address in URL at {path}: {parsed.hostname}")
            
        except Exception as e:
            violations.append(f"Invalid URL at {path}: {e}")
        
        return violations
    
    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP address"""
        import ipaddress
        
        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except ValueError:
            return False
    
    def _detect_dangerous_configurations(self, config: Dict[str, Any]) -> List[str]:
        """Detect dangerous configuration patterns"""
        violations = []
        
        dangerous_configs = [
            ('debug', True, 'Debug mode enabled'),
            ('testing', True, 'Testing mode enabled'),
            ('allow_all_origins', True, 'CORS allow all origins enabled'),
            ('disable_ssl', True, 'SSL disabled'),
            ('verify_ssl', False, 'SSL verification disabled'),
            ('unsafe_mode', True, 'Unsafe mode enabled'),
        ]
        
        def check_dangerous_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check for dangerous key-value pairs
                    for danger_key, danger_value, description in dangerous_configs:
                        if key.lower() == danger_key.lower() and value == danger_value:
                            violations.append(f"Dangerous configuration at {current_path}: {description}")
                    
                    check_dangerous_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    check_dangerous_recursive(item, current_path)
        
        check_dangerous_recursive(config)
        return violations
    
    def _sanitize_configuration(self, config: Dict[str, Any], violations: List[str], remediation_actions: List[str]) -> Dict[str, Any]:
        """Sanitize configuration"""
        sanitized = {}
        
        for key, value in config.items():
            if isinstance(value, str):
                # Check for secrets and mask them
                if any(secret in key.lower() for secret in ['password', 'secret', 'token', 'key']):
                    if len(value) > 0:
                        violations.append(f"Masked secret in configuration key: {key}")
                        remediation_actions.append("Use environment variables or secret management for sensitive data")
                        sanitized[key] = "***MASKED***"
                    else:
                        sanitized[key] = value
                else:
                    sanitized[key] = self._sanitize_string(value, violations, remediation_actions)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_configuration(value, violations, remediation_actions)
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, dict):
                        sanitized_list.append(self._sanitize_configuration(item, violations, remediation_actions))
                    elif isinstance(item, str):
                        sanitized_list.append(self._sanitize_string(item, violations, remediation_actions))
                    else:
                        sanitized_list.append(item)
                sanitized[key] = sanitized_list
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_code(self, code: str, violations: List[str], remediation_actions: List[str]) -> str:
        """Sanitize code content"""
        sanitized_code = code
        
        # Remove dangerous imports
        dangerous_imports = ['os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'pickle', 'marshal']
        
        for dangerous_import in dangerous_imports:
            patterns = [
                f'import {dangerous_import}',
                f'from {dangerous_import} import',
                f'import {dangerous_import} as',
            ]
            
            for pattern in patterns:
                if pattern in sanitized_code:
                    violations.append(f"Removed dangerous import: {pattern}")
                    remediation_actions.append(f"Use safe alternatives to {dangerous_import}")
                    sanitized_code = sanitized_code.replace(pattern, f'# REMOVED: {pattern}')
        
        # Remove dangerous function calls
        dangerous_calls = ['exec(', 'eval(', 'os.system(', 'subprocess.', 'pickle.loads(']
        
        for call in dangerous_calls:
            if call in sanitized_code:
                violations.append(f"Removed dangerous function call: {call}")
                remediation_actions.append(f"Use safe alternatives to {call}")
                sanitized_code = sanitized_code.replace(call, f'# REMOVED: {call}')
        
        return sanitized_code
    
    def _validate_nesting_depth(self, obj: Any, current_depth: int = 0, max_depth: int = 10) -> List[str]:
        """Validate nesting depth to prevent stack overflow"""
        violations = []
        
        if current_depth > max_depth:
            violations.append(f"Nesting depth exceeds maximum: {current_depth} > {max_depth}")
            return violations
        
        if isinstance(obj, dict):
            for value in obj.values():
                violations.extend(self._validate_nesting_depth(value, current_depth + 1, max_depth))
        elif isinstance(obj, list):
            for item in obj:
                violations.extend(self._validate_nesting_depth(item, current_depth + 1, max_depth))
        
        return violations
    
    def _calculate_risk_level(self, violations: List[str]) -> str:
        """Calculate risk level based on violations"""
        if not violations:
            return "low"
        
        critical_keywords = ['critical', 'dangerous', 'vulnerable', 'exploit', 'injection']
        high_keywords = ['secret', 'password', 'token', 'private', 'traversal']
        medium_keywords = ['suspicious', 'warning', 'unsafe', 'deprecated']
        
        violation_text = ' '.join(violations).lower()
        
        if any(keyword in violation_text for keyword in critical_keywords):
            return "critical"
        elif any(keyword in violation_text for keyword in high_keywords):
            return "high"
        elif any(keyword in violation_text for keyword in medium_keywords):
            return "medium"
        else:
            return "low"