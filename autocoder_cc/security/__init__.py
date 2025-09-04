"""
Security Framework Package - Task 16 Implementation

Comprehensive security implementation including input validation,
security auditing, and secure deployment capabilities.
"""

from .input_validator import (
    InputValidator,
    ValidationResult,
    SecurityViolation
)

from .security_auditor import (
    SecurityAuditor,
    AuditEvent,
    AuditEventType,
    RiskLevel,
    SecurityMetrics,
    AuditTrailValidation,
    SecurityError,
    audit_context
)

from .secure_deployment import (
    SecureDeploymentFramework,
    SecurityPolicy,
    SecretConfig,
    DeploymentSecurityConfig,
    SecurityPostureReport
)

__all__ = [
    # Input Validation
    'InputValidator',
    'ValidationResult', 
    'SecurityViolation',
    
    # Security Auditing
    'SecurityAuditor',
    'AuditEvent',
    'AuditEventType',
    'RiskLevel',
    'SecurityMetrics',
    'AuditTrailValidation',
    'SecurityError',
    'audit_context',
    
    # Secure Deployment
    'SecureDeploymentFramework',
    'SecurityPolicy',
    'SecretConfig',
    'DeploymentSecurityConfig',
    'SecurityPostureReport'
]

# Package version
__version__ = "1.0.0"

# Package description
__description__ = "Comprehensive security framework for AutoCoder4_CC"