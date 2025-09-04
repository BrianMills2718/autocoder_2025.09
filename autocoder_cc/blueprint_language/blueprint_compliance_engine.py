"""
Blueprint Compliance Engine
Enforces architectural consistency between blueprint declarations and generated code.
"""

import logging
import re
import ast
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Compliance check severity levels"""
    CRITICAL = "critical"  # Must be fixed - deployment will fail
    HIGH = "high"         # Should be fixed - functionality incomplete
    MEDIUM = "medium"     # Should be fixed - best practices
    LOW = "low"          # Nice to have - optimization opportunity

@dataclass
class ComplianceViolation:
    """Represents a blueprint compliance violation"""
    level: ComplianceLevel
    component: str
    violation_type: str
    description: str
    expected: str
    actual: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None

@dataclass 
class ComplianceReport:
    """Complete compliance assessment report"""
    violations: List[ComplianceViolation]
    passed_checks: List[str]
    summary: Dict[str, int]
    is_compliant: bool

class ArchitecturalPattern:
    """Defines an architectural pattern that must be enforced"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def check_compliance(self, blueprint: Dict[str, Any], generated_files: Dict[str, str]) -> List[ComplianceViolation]:
        """Check if generated code complies with this pattern"""
        raise NotImplementedError("Subclasses must implement check_compliance")

class MessagingArchitecturePattern(ArchitecturalPattern):
    """Enforces messaging/queue architectural consistency"""
    
    def __init__(self):
        super().__init__(
            "messaging_architecture",
            "Ensures messaging infrastructure matches code implementation"
        )
    
    def check_compliance(self, blueprint: Dict[str, Any], generated_files: Dict[str, str]) -> List[ComplianceViolation]:
        violations = []
        
        # Check if RabbitMQ is declared in infrastructure
        docker_compose = generated_files.get("docker-compose.yml", "")
        requirements_txt = generated_files.get("requirements.txt", "")
        
        has_rabbitmq_infra = "rabbitmq:" in docker_compose
        has_messaging_deps = any(lib in requirements_txt for lib in ["pika", "celery", "kombu", "aio-pika"])
        
        if has_rabbitmq_infra and not has_messaging_deps:
            violations.append(ComplianceViolation(
                level=ComplianceLevel.CRITICAL,
                component="messaging",
                violation_type="missing_dependencies",
                description="RabbitMQ infrastructure declared but messaging libraries missing from requirements.txt",
                expected="pika, celery, or aio-pika in requirements.txt",
                actual="No messaging libraries found",
                file_path="requirements.txt",
                fix_suggestion="Add 'pika>=1.3.0' or 'aio-pika>=9.0.0' to requirements.txt"
            ))
        
        # Check if components use messaging when RabbitMQ is available
        if has_rabbitmq_infra:
            for file_path, content in generated_files.items():
                if file_path.endswith(".py") and "components/" in file_path:
                    has_rabbitmq_imports = any(lib in content for lib in ["pika", "aio_pika", "celery"])
                    has_rabbitmq_config = "rabbitmq" in content.lower() or "amqp" in content.lower()
                    
                    if not has_rabbitmq_imports and not has_rabbitmq_config:
                        violations.append(ComplianceViolation(
                            level=ComplianceLevel.HIGH,
                            component=file_path,
                            violation_type="missing_messaging_integration",
                            description="Component should integrate with declared RabbitMQ infrastructure",
                            expected="RabbitMQ client code or messaging configuration",
                            actual="No messaging integration found",
                            file_path=file_path,
                            fix_suggestion="Add RabbitMQ client initialization and message handling"
                        ))
        
        return violations

class DatabaseArchitecturePattern(ArchitecturalPattern):
    """Enforces database architectural consistency"""
    
    def __init__(self):
        super().__init__(
            "database_architecture", 
            "Ensures database infrastructure matches code implementation"
        )
    
    def check_compliance(self, blueprint: Dict[str, Any], generated_files: Dict[str, str]) -> List[ComplianceViolation]:
        violations = []
        
        docker_compose = generated_files.get("docker-compose.yml", "")
        requirements_txt = generated_files.get("requirements.txt", "")
        
        # Check PostgreSQL consistency
        has_postgres_infra = "postgres:" in docker_compose
        has_postgres_deps = any(lib in requirements_txt for lib in ["psycopg2", "asyncpg", "databases"])
        
        if has_postgres_infra and not has_postgres_deps:
            violations.append(ComplianceViolation(
                level=ComplianceLevel.CRITICAL,
                component="database",
                violation_type="missing_database_dependencies",
                description="PostgreSQL infrastructure declared but database libraries missing",
                expected="psycopg2-binary, asyncpg, or databases in requirements.txt",
                actual="No PostgreSQL libraries found",
                file_path="requirements.txt",
                fix_suggestion="Add 'asyncpg>=0.28.0' and 'databases>=0.7.0' to requirements.txt"
            ))
        
        # Check Redis consistency  
        has_redis_infra = "redis:" in docker_compose
        has_redis_deps = any(lib in requirements_txt for lib in ["redis", "aioredis"])
        
        if has_redis_infra and not has_redis_deps:
            violations.append(ComplianceViolation(
                level=ComplianceLevel.HIGH,
                component="caching",
                violation_type="missing_cache_dependencies", 
                description="Redis infrastructure declared but Redis libraries missing",
                expected="redis or aioredis in requirements.txt",
                actual="No Redis libraries found",
                file_path="requirements.txt",
                fix_suggestion="Add 'redis>=4.5.0' or 'aioredis>=2.0.0' to requirements.txt"
            ))
        
        return violations

class APIArchitecturePattern(ArchitecturalPattern):
    """Enforces API architectural consistency"""
    
    def __init__(self):
        super().__init__(
            "api_architecture",
            "Ensures API components match declared endpoints and protocols"
        )
    
    def check_compliance(self, blueprint: Dict[str, Any], generated_files: Dict[str, str]) -> List[ComplianceViolation]:
        violations = []
        
        # Check if FastAPI components have proper CORS, security, validation
        for file_path, content in generated_files.items():
            if file_path.endswith(".py") and ("api" in file_path.lower() or "main.py" in file_path):
                if "FastAPI" in content:
                    # Check for security middleware
                    if "cors" not in content.lower() and "CORS" not in content:
                        violations.append(ComplianceViolation(
                            level=ComplianceLevel.MEDIUM,
                            component=file_path,
                            violation_type="missing_cors_configuration",
                            description="FastAPI application missing CORS configuration",
                            expected="CORS middleware configured",
                            actual="No CORS configuration found",
                            file_path=file_path,
                            fix_suggestion="Add CORS middleware: app.add_middleware(CORSMiddleware, ...)"
                        ))
                    
                    # Check for request validation
                    if "BaseModel" not in content and "pydantic" not in content:
                        violations.append(ComplianceViolation(
                            level=ComplianceLevel.MEDIUM,
                            component=file_path,
                            violation_type="missing_request_validation",
                            description="API endpoints missing Pydantic request validation",
                            expected="Pydantic BaseModel for request validation",
                            actual="No request validation models found",
                            file_path=file_path,
                            fix_suggestion="Add Pydantic models for request/response validation"
                        ))
        
        return violations

class SecurityArchitecturePattern(ArchitecturalPattern):
    """Enforces security best practices in generated systems"""
    
    def __init__(self):
        super().__init__(
            "security_architecture",
            "Ensures generated systems follow security best practices"
        )
    
    def check_compliance(self, blueprint: Dict[str, Any], generated_files: Dict[str, str]) -> List[ComplianceViolation]:
        violations = []
        
        # Check docker-compose.yml for hardcoded secrets
        docker_compose = generated_files.get("docker-compose.yml", "")
        if docker_compose:
            violations.extend(self._check_hardcoded_secrets(docker_compose))
        
        # Check for .env file presence
        if "docker-compose.yml" in generated_files and ".env" not in generated_files:
            violations.append(ComplianceViolation(
                level=ComplianceLevel.CRITICAL,
                component="security",
                violation_type="missing_env_file",
                description=".env file missing but docker-compose.yml references environment variables",
                expected=".env file with secure configuration",
                actual="No .env file found",
                fix_suggestion="Generate .env template with secure placeholders"
            ))
        
        return violations
    
    def _check_hardcoded_secrets(self, docker_compose_content: str) -> List[ComplianceViolation]:
        """Check for hardcoded secrets in docker-compose.yml"""
        violations = []
        
        hardcoded_patterns = [
            (r'password=([^$\s]+)', "hardcoded_password"),
            (r'PASSWORD=([^$\s]+)', "hardcoded_password"),
            (r'secret=([^$\s]+)', "hardcoded_secret"),
            (r'SECRET=([^$\s]+)', "hardcoded_secret"),
            (r'key=([^$\s]+)', "hardcoded_key")
        ]
        
        for pattern, violation_type in hardcoded_patterns:
            matches = re.findall(pattern, docker_compose_content)
            for match in matches:
                if not match.startswith("${"):  # Not an environment variable
                    violations.append(ComplianceViolation(
                        level=ComplianceLevel.CRITICAL,
                        component="security",
                        violation_type=violation_type,
                        description=f"Hardcoded secret detected: {match}",
                        expected="Environment variable reference: ${VARIABLE_NAME}",
                        actual=f"Hardcoded value: {match}",
                        fix_suggestion="Replace with environment variable and add to .env file"
                    ))
        
        return violations

class BlueprintComplianceEngine:
    """
    Core compliance engine that validates generated systems against blueprints.
    Ensures architectural consistency and prevents deployment of non-compliant systems.
    """
    
    def __init__(self):
        self.patterns: List[ArchitecturalPattern] = [
            MessagingArchitecturePattern(),
            DatabaseArchitecturePattern(), 
            APIArchitecturePattern(),
            SecurityArchitecturePattern()
        ]
        self.logger = logging.getLogger(__name__)
    
    def validate_system(self, blueprint_path: str, generated_system_path: str) -> ComplianceReport:
        """
        Validate a generated system against its blueprint.
        
        Args:
            blueprint_path: Path to the system blueprint YAML
            generated_system_path: Path to the generated system directory
            
        Returns:
            ComplianceReport with all violations and compliance status
        """
        try:
            # Load blueprint
            blueprint = self._load_blueprint(blueprint_path)
            
            # Load generated files
            generated_files = self._load_generated_files(generated_system_path)
            
            # Run compliance checks
            all_violations = []
            passed_checks = []
            
            for pattern in self.patterns:
                self.logger.info(f"Checking compliance for pattern: {pattern.name}")
                violations = pattern.check_compliance(blueprint, generated_files)
                
                if violations:
                    all_violations.extend(violations)
                    self.logger.warning(f"Pattern {pattern.name}: {len(violations)} violations found")
                else:
                    passed_checks.append(pattern.name)
                    self.logger.info(f"Pattern {pattern.name}: PASSED")
            
            # Generate summary
            summary = {
                "total_violations": len(all_violations),
                "critical": len([v for v in all_violations if v.level == ComplianceLevel.CRITICAL]),
                "high": len([v for v in all_violations if v.level == ComplianceLevel.HIGH]),
                "medium": len([v for v in all_violations if v.level == ComplianceLevel.MEDIUM]),
                "low": len([v for v in all_violations if v.level == ComplianceLevel.LOW])
            }
            
            # System is compliant if no critical violations
            is_compliant = summary["critical"] == 0
            
            report = ComplianceReport(
                violations=all_violations,
                passed_checks=passed_checks,
                summary=summary,
                is_compliant=is_compliant
            )
            
            self.logger.info(f"Compliance check complete: {'PASSED' if is_compliant else 'FAILED'}")
            return report
            
        except Exception as e:
            self.logger.error(f"Compliance validation failed: {e}")
            raise
    
    def _load_blueprint(self, blueprint_path: str) -> Dict[str, Any]:
        """Load and parse blueprint YAML"""
        try:
            with open(blueprint_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load blueprint from {blueprint_path}: {e}")
    
    def _load_generated_files(self, system_path: str) -> Dict[str, str]:
        """Load all generated files for analysis"""
        files = {}
        system_path = Path(system_path)
        
        if not system_path.exists():
            raise RuntimeError(f"Generated system path does not exist: {system_path}")
        
        # Load key files for compliance checking
        for file_pattern in ["**/*.py", "**/*.yml", "**/*.yaml", "**/requirements.txt", "**/Dockerfile"]:
            for file_path in system_path.glob(file_pattern):
                if file_path.is_file():
                    try:
                        relative_path = str(file_path.relative_to(system_path))
                        with open(file_path, 'r') as f:
                            files[relative_path] = f.read()
                    except Exception as e:
                        self.logger.warning(f"Could not read file {file_path}: {e}")
                        continue
        
        self.logger.info(f"Loaded {len(files)} files for compliance analysis")
        return files
    
    def generate_compliance_report(self, report: ComplianceReport, output_path: str = None) -> str:
        """Generate a detailed compliance report"""
        lines = []
        lines.append("# Blueprint Compliance Report")
        lines.append(f"Generated: {self._get_timestamp()}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(f"**Compliance Status:** {'✅ PASSED' if report.is_compliant else '❌ FAILED'}")
        lines.append(f"**Total Violations:** {report.summary['total_violations']}")
        lines.append(f"**Critical:** {report.summary['critical']}")
        lines.append(f"**High:** {report.summary['high']}")
        lines.append(f"**Medium:** {report.summary['medium']}")
        lines.append(f"**Low:** {report.summary['low']}")
        lines.append("")
        
        # Passed checks
        if report.passed_checks:
            lines.append("## ✅ Passed Compliance Checks")
            for check in report.passed_checks:
                lines.append(f"- {check}")
            lines.append("")
        
        # Violations
        if report.violations:
            lines.append("## ❌ Compliance Violations")
            
            for level in [ComplianceLevel.CRITICAL, ComplianceLevel.HIGH, ComplianceLevel.MEDIUM, ComplianceLevel.LOW]:
                level_violations = [v for v in report.violations if v.level == level]
                if level_violations:
                    lines.append(f"### {level.value.upper()} Priority")
                    
                    for violation in level_violations:
                        lines.append(f"**{violation.violation_type}** ({violation.component})")
                        lines.append(f"- **Description:** {violation.description}")
                        lines.append(f"- **Expected:** {violation.expected}")
                        lines.append(f"- **Actual:** {violation.actual}")
                        if violation.file_path:
                            lines.append(f"- **File:** {violation.file_path}")
                        if violation.fix_suggestion:
                            lines.append(f"- **Fix:** {violation.fix_suggestion}")
                        lines.append("")
        
        report_content = "\n".join(lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_content)
            self.logger.info(f"Compliance report written to {output_path}")
        
        return report_content
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reports"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Fail-fast validation function for immediate use
def validate_system_compliance(blueprint_path: str, generated_system_path: str) -> bool:
    """
    Immediate fail-fast compliance validation.
    Returns True if system is compliant, raises exception if critical violations found.
    """
    engine = BlueprintComplianceEngine()
    report = engine.validate_system(blueprint_path, generated_system_path)
    
    if not report.is_compliant:
        critical_violations = [v for v in report.violations if v.level == ComplianceLevel.CRITICAL]
        violation_details = "\n".join([f"- {v.description}" for v in critical_violations])
        
        raise RuntimeError(
            f"CRITICAL COMPLIANCE VIOLATIONS DETECTED:\n{violation_details}\n"
            f"System cannot be deployed until these issues are resolved."
        )
    
    return True