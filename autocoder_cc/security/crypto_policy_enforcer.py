#!/usr/bin/env python3
"""
Cryptographic Policy Enforcer
Loads and enforces environment-specific cryptographic policies for JWT algorithms
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

# Simple logger for testing without dependencies
def get_logger(name: str):
    """Simple logger for testing"""
    import logging
    return logging.getLogger(name)

class CryptoPolicyError(Exception):
    """Raised when cryptographic policy violations occur"""
    pass

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class JWTPolicy:
    """JWT algorithm policy for an environment"""
    allowed_algorithms: List[str]
    default_algorithm: str
    blocked_algorithms: List[str]
    minimum_key_size: int
    enforce_key_rotation: bool

@dataclass
class CryptographicPolicy:
    """Complete cryptographic policy configuration"""
    environment: Environment
    jwt_policy: JWTPolicy
    deprecated_algorithms: List[str]
    forbidden_algorithms: List[str]
    compliance_requirements: List[str]

class CryptoPolicyEnforcer:
    """Enforces cryptographic policies based on environment configuration"""
    
    def __init__(self, policy_file: Optional[Path] = None):
        self.logger = get_logger(__name__)
        self.policy_file = policy_file or Path("config/cryptographic_policy.yaml")
        self.current_environment = self._detect_environment()
        self.policy = self._load_policy()
        
        self.logger.info(f"Crypto policy enforcer initialized for environment: {self.current_environment.value}")
        self.logger.info(f"Allowed JWT algorithms: {self.policy.jwt_policy.allowed_algorithms}")
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            self.logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_policy(self) -> CryptographicPolicy:
        """Load cryptographic policy from configuration file"""
        if not self.policy_file.exists():
            raise CryptoPolicyError(f"Cryptographic policy file not found: {self.policy_file}")
        
        try:
            with open(self.policy_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Get environment-specific configuration
            env_config = config["environments"][self.current_environment.value]
            jwt_config = env_config["jwt"]
            
            # Extract blocked algorithms
            blocked_algorithms = []
            for alg, settings in jwt_config.get("algorithms", {}).items():
                if isinstance(settings, dict) and not settings.get("enabled", True):
                    blocked_algorithms.append(alg)
            
            jwt_policy = JWTPolicy(
                allowed_algorithms=jwt_config["allowed_algorithms"],
                default_algorithm=jwt_config["default_algorithm"],
                blocked_algorithms=blocked_algorithms,
                minimum_key_size=jwt_config.get("minimum_key_size", 256),
                enforce_key_rotation=jwt_config.get("enforce_key_rotation", False)
            )
            
            policy = CryptographicPolicy(
                environment=self.current_environment,
                jwt_policy=jwt_policy,
                deprecated_algorithms=config["global_policies"]["deprecated_algorithms"],
                forbidden_algorithms=config["global_policies"]["forbidden_algorithms"],
                compliance_requirements=env_config.get("compliance", {}).get("required_standards", [])
            )
            
            self.logger.info(f"Loaded cryptographic policy for {self.current_environment.value}")
            return policy
            
        except (yaml.YAMLError, KeyError, TypeError) as e:
            raise CryptoPolicyError(f"Failed to load cryptographic policy: {e}")
    
    def get_allowed_jwt_algorithms(self) -> List[str]:
        """Get list of allowed JWT algorithms for current environment"""
        return self.policy.jwt_policy.allowed_algorithms.copy()
    
    def get_default_jwt_algorithm(self) -> str:
        """Get default JWT algorithm for current environment"""
        return self.policy.jwt_policy.default_algorithm
    
    def validate_jwt_algorithm(self, algorithm: str) -> bool:
        """Validate if a JWT algorithm is allowed in current environment"""
        # Check if algorithm is forbidden globally
        if algorithm in self.policy.forbidden_algorithms:
            self.logger.error(f"JWT algorithm '{algorithm}' is globally forbidden")
            return False
        
        # Check if algorithm is blocked in current environment
        if algorithm in self.policy.jwt_policy.blocked_algorithms:
            self.logger.error(f"JWT algorithm '{algorithm}' is blocked in {self.current_environment.value}")
            return False
        
        # Check if algorithm is allowed in current environment
        if algorithm not in self.policy.jwt_policy.allowed_algorithms:
            self.logger.error(f"JWT algorithm '{algorithm}' not allowed in {self.current_environment.value}. Allowed: {self.policy.jwt_policy.allowed_algorithms}")
            return False
        
        # Warn if algorithm is deprecated
        if algorithm in self.policy.deprecated_algorithms:
            self.logger.warning(f"JWT algorithm '{algorithm}' is deprecated and should be migrated")
        
        return True
    
    def enforce_jwt_algorithm(self, algorithm: str) -> str:
        """Enforce JWT algorithm policy, raising exception if violation"""
        if not self.validate_jwt_algorithm(algorithm):
            allowed = ", ".join(self.policy.jwt_policy.allowed_algorithms)
            raise CryptoPolicyError(
                f"JWT algorithm '{algorithm}' violates cryptographic policy for {self.current_environment.value}. "
                f"Allowed algorithms: {allowed}"
            )
        
        self.logger.debug(f"JWT algorithm '{algorithm}' approved for {self.current_environment.value}")
        return algorithm
    
    def get_jwt_decode_algorithms(self) -> List[str]:
        """Get algorithms list suitable for jwt.decode() based on policy"""
        algorithms = self.get_allowed_jwt_algorithms()
        
        # Log policy enforcement
        self.logger.debug(f"JWT decode algorithms for {self.current_environment.value}: {algorithms}")
        
        return algorithms
    
    def validate_environment_compliance(self) -> Dict[str, Any]:
        """Validate current policy meets compliance requirements"""
        compliance_status = {
            "environment": self.current_environment.value,
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # Check production security requirements
        if self.current_environment == Environment.PRODUCTION:
            # Production should not allow HS256
            if "HS256" in self.policy.jwt_policy.allowed_algorithms:
                compliance_status["violations"].append(
                    "Production environment allows HS256 algorithm (security risk)"
                )
                compliance_status["compliant"] = False
            
            # Production should require asymmetric algorithms
            asymmetric_algos = [alg for alg in self.policy.jwt_policy.allowed_algorithms 
                              if alg.startswith(('RS', 'ES', 'PS'))]
            if not asymmetric_algos:
                compliance_status["violations"].append(
                    "Production environment requires at least one asymmetric algorithm (RS256, ES256, etc.)"
                )
                compliance_status["compliant"] = False
        
        # Check for deprecated algorithms
        deprecated_in_use = set(self.policy.jwt_policy.allowed_algorithms) & set(self.policy.deprecated_algorithms)
        if deprecated_in_use:
            compliance_status["warnings"].append(
                f"Using deprecated algorithms: {', '.join(deprecated_in_use)}"
            )
        
        # Log compliance status
        if compliance_status["compliant"]:
            self.logger.info(f"Cryptographic policy compliance: PASSED for {self.current_environment.value}")
        else:
            self.logger.error(f"Cryptographic policy compliance: FAILED for {self.current_environment.value}")
            for violation in compliance_status["violations"]:
                self.logger.error(f"  Violation: {violation}")
        
        for warning in compliance_status["warnings"]:
            self.logger.warning(f"  Warning: {warning}")
        
        return compliance_status
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get comprehensive policy summary for current environment"""
        return {
            "environment": self.current_environment.value,
            "jwt_policy": {
                "allowed_algorithms": self.policy.jwt_policy.allowed_algorithms,
                "default_algorithm": self.policy.jwt_policy.default_algorithm,
                "blocked_algorithms": self.policy.jwt_policy.blocked_algorithms,
                "minimum_key_size": self.policy.jwt_policy.minimum_key_size
            },
            "global_policies": {
                "deprecated_algorithms": self.policy.deprecated_algorithms,
                "forbidden_algorithms": self.policy.forbidden_algorithms
            },
            "compliance_requirements": self.policy.compliance_requirements
        }

# Global enforcer instance
_enforcer: Optional[CryptoPolicyEnforcer] = None

def get_crypto_enforcer() -> CryptoPolicyEnforcer:
    """Get global cryptographic policy enforcer instance"""
    global _enforcer
    if _enforcer is None:
        _enforcer = CryptoPolicyEnforcer()
    return _enforcer

def get_allowed_jwt_algorithms() -> List[str]:
    """Convenience function to get allowed JWT algorithms"""
    return get_crypto_enforcer().get_allowed_jwt_algorithms()

def validate_jwt_algorithm(algorithm: str) -> bool:
    """Convenience function to validate JWT algorithm"""
    return get_crypto_enforcer().validate_jwt_algorithm(algorithm)

def enforce_jwt_algorithm(algorithm: str) -> str:
    """Convenience function to enforce JWT algorithm policy"""
    return get_crypto_enforcer().enforce_jwt_algorithm(algorithm)

def get_jwt_decode_algorithms() -> List[str]:
    """Convenience function to get JWT decode algorithms for current environment"""
    return get_crypto_enforcer().get_jwt_decode_algorithms()

# Test and validation functions
def test_crypto_policy_enforcement():
    """Test cryptographic policy enforcement functionality"""
    print("🔐 Testing Cryptographic Policy Enforcement")
    print("=" * 50)
    
    try:
        enforcer = CryptoPolicyEnforcer()
        
        print(f"✅ Environment: {enforcer.current_environment.value}")
        print(f"✅ Policy file: {enforcer.policy_file}")
        print(f"✅ Allowed algorithms: {enforcer.get_allowed_jwt_algorithms()}")
        print(f"✅ Default algorithm: {enforcer.get_default_jwt_algorithm()}")
        
        # Test algorithm validation
        test_algorithms = ["HS256", "RS256", "ES256", "none"]
        print("\n🧪 Algorithm Validation Tests:")
        for alg in test_algorithms:
            is_valid = enforcer.validate_jwt_algorithm(alg)
            status = "✅ ALLOWED" if is_valid else "❌ BLOCKED"
            print(f"  {alg}: {status}")
        
        # Test enforcement
        print("\n🛡️ Policy Enforcement Test:")
        try:
            allowed_algs = enforcer.get_jwt_decode_algorithms()
            print(f"  JWT decode algorithms: {allowed_algs}")
        except CryptoPolicyError as e:
            print(f"  ❌ Enforcement error: {e}")
        
        # Test compliance
        print("\n📋 Compliance Validation:")
        compliance = enforcer.validate_environment_compliance()
        status = "✅ COMPLIANT" if compliance["compliant"] else "❌ NON-COMPLIANT"
        print(f"  Status: {status}")
        if compliance["violations"]:
            for violation in compliance["violations"]:
                print(f"    ❌ {violation}")
        if compliance["warnings"]:
            for warning in compliance["warnings"]:
                print(f"    ⚠️ {warning}")
        
        print("\n✅ Cryptographic policy enforcement test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_crypto_policy_enforcement()