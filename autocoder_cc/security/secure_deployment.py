"""
Secure Deployment Framework - Task 16 Security Implementation

Secure system deployment with hardening, security policies, encrypted configurations,
secrets management, and security posture validation.
"""

import os
import json
import yaml
import base64
import secrets
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import subprocess
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    policy_name: str
    policy_type: str
    rules: List[Dict[str, Any]]
    enforcement_level: str  # strict, moderate, permissive
    exceptions: List[str]


@dataclass
class SecretConfig:
    """Secret configuration"""
    secret_name: str
    secret_type: str  # password, api_key, certificate, etc.
    encrypted_value: str
    metadata: Dict[str, Any]


@dataclass
class DeploymentSecurityConfig:
    """Deployment security configuration"""
    encryption_enabled: bool
    network_policies: List[SecurityPolicy]
    access_policies: List[SecurityPolicy]
    secrets_management: Dict[str, SecretConfig]
    hardening_rules: List[str]
    compliance_requirements: List[str]


@dataclass
class SecurityPostureReport:
    """Security posture assessment report"""
    deployment_name: str
    security_score: float
    compliance_score: float
    vulnerabilities: List[Dict[str, Any]]
    recommendations: List[str]
    hardening_status: Dict[str, str]
    encryption_status: Dict[str, str]


class SecureDeploymentFramework:
    """Secure system deployment with comprehensive hardening"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize secure deployment framework"""
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Security defaults
        self.security_defaults = self._load_security_defaults()
        
        # Hardening templates
        self.hardening_templates = self._load_hardening_templates()
        
        # Compliance requirements
        self.compliance_frameworks = self._load_compliance_frameworks()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for secrets management"""
        return Fernet.generate_key()
    
    def _load_security_defaults(self) -> Dict[str, Any]:
        """Load default security configurations"""
        return {
            "network_security": {
                "deny_all_default": True,
                "allowed_ports": [80, 443],
                "tls_min_version": "1.2",
                "disable_legacy_protocols": True
            },
            "access_control": {
                "default_permissions": "read-only",
                "require_authentication": True,
                "session_timeout": 3600,
                "max_failed_attempts": 3
            },
            "container_security": {
                "run_as_non_root": True,
                "read_only_filesystem": True,
                "no_new_privileges": True,
                "drop_all_capabilities": True,
                "allowed_capabilities": []
            },
            "monitoring": {
                "enable_audit_logging": True,
                "log_level": "INFO",
                "alert_on_security_events": True,
                "retention_days": 90
            }
        }
    
    def _load_hardening_templates(self) -> Dict[str, Any]:
        """Load hardening templates for different deployment types"""
        return {
            "kubernetes": {
                "pod_security_standards": "restricted",
                "network_policies": "default_deny",
                "service_mesh": "istio_with_mtls",
                "rbac": "least_privilege",
                "admission_controllers": [
                    "PodSecurityPolicy",
                    "ResourceQuota",
                    "LimitRanger",
                    "ValidatingAdmissionWebhook"
                ]
            },
            "docker": {
                "user_namespace": True,
                "apparmor_profile": "docker-default",
                "seccomp_profile": "default",
                "read_only_containers": True,
                "no_new_privileges": True
            },
            "linux": {
                "firewall_enabled": True,
                "selinux_enforcing": True,
                "disable_unused_services": True,
                "kernel_hardening": True,
                "file_permissions": "restrictive"
            }
        }
    
    def _load_compliance_frameworks(self) -> Dict[str, Any]:
        """Load compliance framework requirements"""
        return {
            "cis_kubernetes": {
                "version": "1.6.0",
                "controls": [
                    "1.1.1 Ensure that the API server pod specification file permissions are set to 644 or more restrictive",
                    "1.1.2 Ensure that the API server pod specification file ownership is set to root:root",
                    "1.2.1 Ensure that the --anonymous-auth argument is set to false",
                    "1.2.2 Ensure that the --basic-auth-file argument is not set",
                    "1.2.3 Ensure that the --token-auth-file parameter is not set"
                ]
            },
            "nist_800_53": {
                "version": "Rev 5",
                "controls": [
                    "AC-2 Account Management",
                    "AC-3 Access Enforcement",
                    "AC-6 Least Privilege",
                    "AU-2 Event Logging",
                    "CM-2 Baseline Configuration",
                    "SC-8 Transmission Confidentiality"
                ]
            },
            "pci_dss": {
                "version": "4.0",
                "requirements": [
                    "1. Install and maintain network security controls",
                    "2. Apply secure configurations to all system components",
                    "3. Protect stored account data",
                    "4. Protect cardholder data with strong cryptography during transmission"
                ]
            }
        }
    
    def create_secure_deployment_config(self, 
                                      system_name: str,
                                      deployment_type: str,
                                      security_requirements: List[str],
                                      secrets: Dict[str, str]) -> DeploymentSecurityConfig:
        """Create secure deployment configuration"""
        
        # Generate network policies
        network_policies = self._generate_network_policies(system_name, deployment_type)
        
        # Generate access policies
        access_policies = self._generate_access_policies(system_name, security_requirements)
        
        # Encrypt and manage secrets
        encrypted_secrets = self._encrypt_secrets(secrets)
        
        # Generate hardening rules
        hardening_rules = self._generate_hardening_rules(deployment_type, security_requirements)
        
        # Determine compliance requirements
        compliance_requirements = self._determine_compliance_requirements(security_requirements)
        
        return DeploymentSecurityConfig(
            encryption_enabled=True,
            network_policies=network_policies,
            access_policies=access_policies,
            secrets_management=encrypted_secrets,
            hardening_rules=hardening_rules,
            compliance_requirements=compliance_requirements
        )
    
    def _generate_network_policies(self, system_name: str, deployment_type: str) -> List[SecurityPolicy]:
        """Generate network security policies"""
        policies = []
        
        # Default deny policy
        default_deny = SecurityPolicy(
            policy_name=f"{system_name}-default-deny",
            policy_type="network",
            rules=[
                {
                    "action": "deny",
                    "direction": "ingress",
                    "source": "all",
                    "destination": "all",
                    "ports": "all"
                },
                {
                    "action": "deny", 
                    "direction": "egress",
                    "source": "all",
                    "destination": "all",
                    "ports": "all"
                }
            ],
            enforcement_level="strict",
            exceptions=[]
        )
        policies.append(default_deny)
        
        # Allow specific ingress
        ingress_policy = SecurityPolicy(
            policy_name=f"{system_name}-ingress-allow",
            policy_type="network",
            rules=[
                {
                    "action": "allow",
                    "direction": "ingress",
                    "source": "load-balancer",
                    "destination": f"{system_name}-service",
                    "ports": [80, 443],
                    "protocol": "tcp"
                }
            ],
            enforcement_level="strict",
            exceptions=[]
        )
        policies.append(ingress_policy)
        
        # Allow specific egress (DNS, external APIs)
        egress_policy = SecurityPolicy(
            policy_name=f"{system_name}-egress-allow",
            policy_type="network",
            rules=[
                {
                    "action": "allow",
                    "direction": "egress",
                    "source": f"{system_name}-pods",
                    "destination": "dns-service",
                    "ports": [53],
                    "protocol": "udp"
                },
                {
                    "action": "allow",
                    "direction": "egress",
                    "source": f"{system_name}-pods",
                    "destination": "external-apis",
                    "ports": [443],
                    "protocol": "tcp"
                }
            ],
            enforcement_level="strict",
            exceptions=[]
        )
        policies.append(egress_policy)
        
        return policies
    
    def _generate_access_policies(self, system_name: str, security_requirements: List[str]) -> List[SecurityPolicy]:
        """Generate access control policies"""
        policies = []
        
        # RBAC policy
        rbac_policy = SecurityPolicy(
            policy_name=f"{system_name}-rbac",
            policy_type="access_control",
            rules=[
                {
                    "role": "admin",
                    "permissions": ["read", "write", "delete"],
                    "resources": ["all"],
                    "conditions": ["mfa_required", "ip_whitelist"]
                },
                {
                    "role": "operator",
                    "permissions": ["read", "write"],
                    "resources": ["config", "logs"],
                    "conditions": ["authenticated"]
                },
                {
                    "role": "viewer",
                    "permissions": ["read"],
                    "resources": ["logs", "metrics"],
                    "conditions": ["authenticated"]
                }
            ],
            enforcement_level="strict",
            exceptions=[]
        )
        policies.append(rbac_policy)
        
        # Pod security policy
        pod_security_policy = SecurityPolicy(
            policy_name=f"{system_name}-pod-security",
            policy_type="pod_security",
            rules=[
                {
                    "runAsNonRoot": True,
                    "runAsUser": {"rule": "MustRunAs", "ranges": [{"min": 1000, "max": 65535}]},
                    "fsGroup": {"rule": "MustRunAs", "ranges": [{"min": 1000, "max": 65535}]},
                    "allowPrivilegeEscalation": False,
                    "requiredDropCapabilities": ["ALL"],
                    "allowedCapabilities": [],
                    "readOnlyRootFilesystem": True,
                    "volumes": ["configMap", "secret", "emptyDir", "persistentVolumeClaim"]
                }
            ],
            enforcement_level="strict",
            exceptions=[]
        )
        policies.append(pod_security_policy)
        
        return policies
    
    def _encrypt_secrets(self, secrets: Dict[str, str]) -> Dict[str, SecretConfig]:
        """Encrypt secrets for secure storage"""
        encrypted_secrets = {}
        
        for secret_name, secret_value in secrets.items():
            # Determine secret type
            secret_type = self._determine_secret_type(secret_name, secret_value)
            
            # Encrypt the secret
            encrypted_value = self.cipher_suite.encrypt(secret_value.encode()).decode()
            
            # Create metadata
            metadata = {
                "created_at": str(pd.Timestamp.now()),
                "algorithm": "Fernet",
                "key_id": hashlib.sha256(self.encryption_key).hexdigest()[:16],
                "rotation_required": False
            }
            
            encrypted_secrets[secret_name] = SecretConfig(
                secret_name=secret_name,
                secret_type=secret_type,
                encrypted_value=encrypted_value,
                metadata=metadata
            )
        
        return encrypted_secrets
    
    def _determine_secret_type(self, name: str, value: str) -> str:
        """Determine the type of secret based on name and value"""
        name_lower = name.lower()
        
        if 'password' in name_lower or 'passwd' in name_lower:
            return 'password'
        elif 'key' in name_lower and ('api' in name_lower or 'access' in name_lower):
            return 'api_key'
        elif 'token' in name_lower:
            return 'token'
        elif 'cert' in name_lower or 'certificate' in name_lower:
            return 'certificate'
        elif 'private' in name_lower and 'key' in name_lower:
            return 'private_key'
        elif value.startswith('-----BEGIN'):
            return 'certificate_or_key'
        else:
            return 'generic_secret'
    
    def _generate_hardening_rules(self, deployment_type: str, security_requirements: List[str]) -> List[str]:
        """Generate hardening rules based on deployment type"""
        base_rules = [
            "Enable container image scanning",
            "Use minimal base images (distroless/alpine)",
            "Run containers as non-root user",
            "Set read-only root filesystem",
            "Drop all capabilities unless required",
            "Disable privilege escalation",
            "Set resource limits and requests",
            "Enable network policies",
            "Use secrets for sensitive data",
            "Enable logging and monitoring"
        ]
        
        # Add deployment-specific rules
        if deployment_type == "kubernetes":
            base_rules.extend([
                "Enable Pod Security Standards",
                "Configure RBAC with least privilege",
                "Enable admission controllers",
                "Use service mesh with mTLS",
                "Configure network segmentation",
                "Enable audit logging",
                "Use Kubernetes secrets encryption at rest"
            ])
        
        elif deployment_type == "docker":
            base_rules.extend([
                "Use Docker secrets for sensitive data",
                "Enable Docker Content Trust",
                "Configure AppArmor/SELinux profiles",
                "Use user namespaces",
                "Limit container resources",
                "Disable inter-container communication"
            ])
        
        # Add security requirement specific rules
        if "pci_compliance" in security_requirements:
            base_rules.extend([
                "Encrypt all data transmissions",
                "Implement strong access controls",
                "Regular security scanning",
                "Maintain audit logs for 1 year"
            ])
        
        if "hipaa_compliance" in security_requirements:
            base_rules.extend([
                "Encrypt data at rest and in transit",
                "Implement access logging",
                "Regular risk assessments",
                "Data backup and recovery procedures"
            ])
        
        return base_rules
    
    def _determine_compliance_requirements(self, security_requirements: List[str]) -> List[str]:
        """Determine compliance requirements based on security needs"""
        compliance_reqs = []
        
        # Map security requirements to compliance frameworks
        compliance_mapping = {
            "pci_compliance": ["PCI DSS 4.0"],
            "hipaa_compliance": ["HIPAA Security Rule"],
            "gdpr_compliance": ["GDPR Article 32"],
            "soc2_compliance": ["SOC 2 Type II"],
            "iso27001_compliance": ["ISO 27001:2013"],
            "nist_compliance": ["NIST Cybersecurity Framework"]
        }
        
        for req in security_requirements:
            if req in compliance_mapping:
                compliance_reqs.extend(compliance_mapping[req])
        
        # Add baseline security standards
        if not compliance_reqs:
            compliance_reqs.append("CIS Controls v8")
        
        return compliance_reqs
    
    def generate_kubernetes_manifests(self, config: DeploymentSecurityConfig, system_name: str) -> Dict[str, str]:
        """Generate hardened Kubernetes manifests"""
        manifests = {}
        
        # Generate NetworkPolicy
        network_policy = self._generate_network_policy_manifest(config.network_policies, system_name)
        manifests["network-policy.yaml"] = network_policy
        
        # Generate PodSecurityPolicy
        pod_security_policy = self._generate_pod_security_policy_manifest(config.access_policies, system_name)
        manifests["pod-security-policy.yaml"] = pod_security_policy
        
        # Generate RBAC
        rbac_manifests = self._generate_rbac_manifests(config.access_policies, system_name)
        manifests.update(rbac_manifests)
        
        # Generate Secret manifests
        secrets_manifest = self._generate_secrets_manifest(config.secrets_management, system_name)
        manifests["secrets.yaml"] = secrets_manifest
        
        # Generate ConfigMap with security configurations
        config_map = self._generate_security_configmap(config, system_name)
        manifests["security-config.yaml"] = config_map
        
        # Generate ServiceMonitor for security monitoring
        service_monitor = self._generate_service_monitor_manifest(system_name)
        manifests["service-monitor.yaml"] = service_monitor
        
        return manifests
    
    def _generate_network_policy_manifest(self, network_policies: List[SecurityPolicy], system_name: str) -> str:
        """Generate NetworkPolicy manifest"""
        policies = []
        
        for policy in network_policies:
            if policy.policy_type == "network":
                policy_manifest = {
                    "apiVersion": "networking.k8s.io/v1",
                    "kind": "NetworkPolicy",
                    "metadata": {
                        "name": policy.policy_name,
                        "namespace": system_name,
                        "labels": {
                            "app": system_name,
                            "security-policy": "true"
                        }
                    },
                    "spec": {
                        "podSelector": {
                            "matchLabels": {
                                "app": system_name
                            }
                        },
                        "policyTypes": ["Ingress", "Egress"],
                        "ingress": [],
                        "egress": []
                    }
                }
                
                # Process rules
                for rule in policy.rules:
                    if rule["direction"] == "ingress" and rule["action"] == "allow":
                        ingress_rule = {
                            "from": [{"podSelector": {"matchLabels": {"role": "load-balancer"}}}],
                            "ports": [{"protocol": "TCP", "port": port} for port in rule.get("ports", [80, 443])]
                        }
                        policy_manifest["spec"]["ingress"].append(ingress_rule)
                    elif rule["direction"] == "egress" and rule["action"] == "allow":
                        egress_rule = {
                            "to": [{"namespaceSelector": {"matchLabels": {"name": "kube-system"}}}],
                            "ports": [{"protocol": rule.get("protocol", "TCP").upper(), "port": port} for port in rule.get("ports", [53])]
                        }
                        policy_manifest["spec"]["egress"].append(egress_rule)
                
                policies.append(policy_manifest)
        
        return yaml.dump_all(policies, default_flow_style=False)
    
    def _generate_pod_security_policy_manifest(self, access_policies: List[SecurityPolicy], system_name: str) -> str:
        """Generate PodSecurityPolicy manifest"""
        for policy in access_policies:
            if policy.policy_type == "pod_security":
                rule = policy.rules[0]  # Take first rule as template
                
                psp_manifest = {
                    "apiVersion": "policy/v1beta1",
                    "kind": "PodSecurityPolicy",
                    "metadata": {
                        "name": f"{system_name}-psp",
                        "labels": {
                            "app": system_name,
                            "security-policy": "true"
                        }
                    },
                    "spec": {
                        "privileged": False,
                        "allowPrivilegeEscalation": rule.get("allowPrivilegeEscalation", False),
                        "requiredDropCapabilities": rule.get("requiredDropCapabilities", ["ALL"]),
                        "allowedCapabilities": rule.get("allowedCapabilities", []),
                        "volumes": rule.get("volumes", ["configMap", "secret", "emptyDir"]),
                        "hostNetwork": False,
                        "hostIPC": False,
                        "hostPID": False,
                        "runAsUser": rule.get("runAsUser", {"rule": "MustRunAsNonRoot"}),
                        "fsGroup": rule.get("fsGroup", {"rule": "RunAsAny"}),
                        "readOnlyRootFilesystem": rule.get("readOnlyRootFilesystem", True),
                        "seLinux": {
                            "rule": "RunAsAny"
                        }
                    }
                }
                
                return yaml.dump(psp_manifest, default_flow_style=False)
        
        return ""
    
    def _generate_rbac_manifests(self, access_policies: List[SecurityPolicy], system_name: str) -> Dict[str, str]:
        """Generate RBAC manifests"""
        manifests = {}
        
        for policy in access_policies:
            if policy.policy_type == "access_control":
                roles = []
                role_bindings = []
                
                for rule in policy.rules:
                    role_name = f"{system_name}-{rule['role']}"
                    
                    # Create Role
                    role = {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "Role",
                        "metadata": {
                            "name": role_name,
                            "namespace": system_name
                        },
                        "rules": [
                            {
                                "apiGroups": [""],
                                "resources": rule["resources"],
                                "verbs": rule["permissions"]
                            }
                        ]
                    }
                    roles.append(role)
                    
                    # Create RoleBinding
                    role_binding = {
                        "apiVersion": "rbac.authorization.k8s.io/v1",
                        "kind": "RoleBinding",
                        "metadata": {
                            "name": f"{role_name}-binding",
                            "namespace": system_name
                        },
                        "subjects": [
                            {
                                "kind": "ServiceAccount",
                                "name": f"{system_name}-{rule['role']}",
                                "namespace": system_name
                            }
                        ],
                        "roleRef": {
                            "kind": "Role",
                            "name": role_name,
                            "apiGroup": "rbac.authorization.k8s.io"
                        }
                    }
                    role_bindings.append(role_binding)
                
                manifests["rbac-roles.yaml"] = yaml.dump_all(roles, default_flow_style=False)
                manifests["rbac-bindings.yaml"] = yaml.dump_all(role_bindings, default_flow_style=False)
        
        return manifests
    
    def _generate_secrets_manifest(self, secrets_management: Dict[str, SecretConfig], system_name: str) -> str:
        """Generate Kubernetes Secrets manifest"""
        secrets_data = {}
        
        for secret_name, secret_config in secrets_management.items():
            # Decode the encrypted value for Kubernetes (it will be base64 encoded again by kubectl)
            decrypted_value = self.cipher_suite.decrypt(secret_config.encrypted_value.encode()).decode()
            secrets_data[secret_name] = base64.b64encode(decrypted_value.encode()).decode()
        
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{system_name}-secrets",
                "namespace": system_name,
                "labels": {
                    "app": system_name,
                    "managed-by": "autocoder-security"
                }
            },
            "type": "Opaque",
            "data": secrets_data
        }
        
        return yaml.dump(secret_manifest, default_flow_style=False)
    
    def _generate_security_configmap(self, config: DeploymentSecurityConfig, system_name: str) -> str:
        """Generate ConfigMap with security configurations"""
        security_config = {
            "hardening_rules": "\n".join(config.hardening_rules),
            "compliance_requirements": "\n".join(config.compliance_requirements),
            "encryption_enabled": str(config.encryption_enabled).lower(),
            "security_policies_count": str(len(config.network_policies) + len(config.access_policies))
        }
        
        configmap_manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{system_name}-security-config",
                "namespace": system_name,
                "labels": {
                    "app": system_name,
                    "config-type": "security"
                }
            },
            "data": security_config
        }
        
        return yaml.dump(configmap_manifest, default_flow_style=False)
    
    def _generate_service_monitor_manifest(self, system_name: str) -> str:
        """Generate ServiceMonitor for security monitoring"""
        service_monitor = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": f"{system_name}-security-monitor",
                "namespace": system_name,
                "labels": {
                    "app": system_name,
                    "monitoring": "security"
                }
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": system_name
                    }
                },
                "endpoints": [
                    {
                        "port": "metrics",
                        "path": "/metrics",
                        "interval": "30s",
                        "scrapeTimeout": "10s"
                    }
                ]
            }
        }
        
        return yaml.dump(service_monitor, default_flow_style=False)
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value"""
        try:
            return self.cipher_suite.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            raise
    
    def rotate_secrets(self, secrets_management: Dict[str, SecretConfig]) -> Dict[str, SecretConfig]:
        """Rotate secrets by generating new encryption"""
        rotated_secrets = {}
        
        for secret_name, secret_config in secrets_management.items():
            # Decrypt with old key
            decrypted_value = self.decrypt_secret(secret_config.encrypted_value)
            
            # Re-encrypt with current key
            new_encrypted_value = self.cipher_suite.encrypt(decrypted_value.encode()).decode()
            
            # Update metadata
            new_metadata = secret_config.metadata.copy()
            new_metadata["rotated_at"] = str(pd.Timestamp.now())
            new_metadata["rotation_required"] = False
            
            rotated_secrets[secret_name] = SecretConfig(
                secret_name=secret_name,
                secret_type=secret_config.secret_type,
                encrypted_value=new_encrypted_value,
                metadata=new_metadata
            )
        
        return rotated_secrets
    
    def validate_deployment_security_posture(self, 
                                           deployment_manifests: Dict[str, str],
                                           system_name: str) -> SecurityPostureReport:
        """Validate deployment security posture"""
        vulnerabilities = []
        recommendations = []
        hardening_status = {}
        encryption_status = {}
        
        # Analyze manifests for security issues
        for manifest_name, manifest_content in deployment_manifests.items():
            try:
                docs = list(yaml.safe_load_all(manifest_content))
                
                for doc in docs:
                    if not doc:
                        continue
                    
                    # Check for security misconfigurations
                    violations = self._analyze_manifest_security(doc, manifest_name)
                    vulnerabilities.extend(violations)
                    
            except yaml.YAMLError as e:
                vulnerabilities.append({
                    "type": "yaml_error",
                    "severity": "medium",
                    "description": f"YAML parsing error in {manifest_name}: {e}",
                    "recommendation": "Fix YAML syntax errors"
                })
        
        # Check hardening status
        hardening_status = self._check_hardening_status(deployment_manifests)
        
        # Check encryption status
        encryption_status = self._check_encryption_status(deployment_manifests)
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(vulnerabilities, hardening_status, encryption_status)
        
        # Calculate security scores
        security_score = self._calculate_security_score(vulnerabilities, hardening_status)
        compliance_score = self._calculate_compliance_score(hardening_status, encryption_status)
        
        return SecurityPostureReport(
            deployment_name=system_name,
            security_score=security_score,
            compliance_score=compliance_score,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            hardening_status=hardening_status,
            encryption_status=encryption_status
        )
    
    def _analyze_manifest_security(self, manifest: Dict[str, Any], manifest_name: str) -> List[Dict[str, Any]]:
        """Analyze individual manifest for security issues"""
        violations = []
        
        kind = manifest.get("kind", "")
        spec = manifest.get("spec", {})
        
        if kind == "Pod" or (kind == "Deployment" and "template" in spec):
            pod_spec = spec.get("template", {}).get("spec", {}) if kind == "Deployment" else spec
            
            # Check security context
            violations.extend(self._check_pod_security_context(pod_spec, manifest_name))
            
            # Check container security
            containers = pod_spec.get("containers", [])
            for container in containers:
                violations.extend(self._check_container_security(container, manifest_name))
        
        elif kind == "Service":
            # Check service security
            violations.extend(self._check_service_security(spec, manifest_name))
        
        elif kind == "Ingress":
            # Check ingress security
            violations.extend(self._check_ingress_security(spec, manifest_name))
        
        return violations
    
    def _check_pod_security_context(self, pod_spec: Dict[str, Any], manifest_name: str) -> List[Dict[str, Any]]:
        """Check pod security context"""
        violations = []
        security_context = pod_spec.get("securityContext", {})
        
        # Check runAsNonRoot
        if not security_context.get("runAsNonRoot", False):
            violations.append({
                "type": "security_context",
                "severity": "high",
                "description": f"Pod in {manifest_name} may run as root",
                "recommendation": "Set securityContext.runAsNonRoot: true"
            })
        
        # Check fsGroup
        if "fsGroup" not in security_context:
            violations.append({
                "type": "security_context",
                "severity": "medium",
                "description": f"Pod in {manifest_name} lacks fsGroup configuration",
                "recommendation": "Set securityContext.fsGroup to a non-root group ID"
            })
        
        return violations
    
    def _check_container_security(self, container: Dict[str, Any], manifest_name: str) -> List[Dict[str, Any]]:
        """Check container security configuration"""
        violations = []
        security_context = container.get("securityContext", {})
        
        # Check allowPrivilegeEscalation
        if security_context.get("allowPrivilegeEscalation", True):
            violations.append({
                "type": "container_security",
                "severity": "high",
                "description": f"Container in {manifest_name} allows privilege escalation",
                "recommendation": "Set securityContext.allowPrivilegeEscalation: false"
            })
        
        # Check readOnlyRootFilesystem
        if not security_context.get("readOnlyRootFilesystem", False):
            violations.append({
                "type": "container_security",
                "severity": "medium",
                "description": f"Container in {manifest_name} has writable root filesystem",
                "recommendation": "Set securityContext.readOnlyRootFilesystem: true"
            })
        
        # Check capabilities
        capabilities = security_context.get("capabilities", {})
        if not capabilities.get("drop") or "ALL" not in capabilities.get("drop", []):
            violations.append({
                "type": "container_security",
                "severity": "high",
                "description": f"Container in {manifest_name} doesn't drop all capabilities",
                "recommendation": "Set securityContext.capabilities.drop: ['ALL']"
            })
        
        # Check resource limits
        resources = container.get("resources", {})
        if not resources.get("limits"):
            violations.append({
                "type": "resource_limits",
                "severity": "medium",
                "description": f"Container in {manifest_name} lacks resource limits",
                "recommendation": "Set resources.limits for CPU and memory"
            })
        
        return violations
    
    def _check_service_security(self, service_spec: Dict[str, Any], manifest_name: str) -> List[Dict[str, Any]]:
        """Check service security configuration"""
        violations = []
        
        # Check service type
        service_type = service_spec.get("type", "ClusterIP")
        if service_type == "NodePort":
            violations.append({
                "type": "service_exposure",
                "severity": "medium",
                "description": f"Service in {manifest_name} uses NodePort",
                "recommendation": "Consider using ClusterIP with Ingress instead"
            })
        elif service_type == "LoadBalancer":
            violations.append({
                "type": "service_exposure",
                "severity": "low",
                "description": f"Service in {manifest_name} uses LoadBalancer",
                "recommendation": "Ensure proper firewall rules are in place"
            })
        
        return violations
    
    def _check_ingress_security(self, ingress_spec: Dict[str, Any], manifest_name: str) -> List[Dict[str, Any]]:
        """Check ingress security configuration"""
        violations = []
        
        # Check TLS configuration
        tls = ingress_spec.get("tls", [])
        if not tls:
            violations.append({
                "type": "ingress_security",
                "severity": "high",
                "description": f"Ingress in {manifest_name} lacks TLS configuration",
                "recommendation": "Add TLS configuration with valid certificates"
            })
        
        return violations
    
    def _check_hardening_status(self, deployment_manifests: Dict[str, str]) -> Dict[str, str]:
        """Check hardening implementation status"""
        status = {
            "network_policies": "not_implemented",
            "pod_security_policies": "not_implemented",
            "rbac": "not_implemented",
            "secrets_management": "not_implemented",
            "monitoring": "not_implemented"
        }
        
        for manifest_name, manifest_content in deployment_manifests.items():
            try:
                docs = list(yaml.safe_load_all(manifest_content))
                
                for doc in docs:
                    if not doc:
                        continue
                    
                    kind = doc.get("kind", "")
                    
                    if kind == "NetworkPolicy":
                        status["network_policies"] = "implemented"
                    elif kind == "PodSecurityPolicy":
                        status["pod_security_policies"] = "implemented"
                    elif kind in ["Role", "RoleBinding", "ClusterRole", "ClusterRoleBinding"]:
                        status["rbac"] = "implemented"
                    elif kind == "Secret":
                        status["secrets_management"] = "implemented"
                    elif kind == "ServiceMonitor":
                        status["monitoring"] = "implemented"
                        
            except yaml.YAMLError:
                continue
        
        return status
    
    def _check_encryption_status(self, deployment_manifests: Dict[str, str]) -> Dict[str, str]:
        """Check encryption implementation status"""
        status = {
            "secrets_encrypted": "unknown",
            "tls_enabled": "unknown",
            "data_at_rest": "unknown"
        }
        
        # Check for secrets
        secrets_found = False
        tls_found = False
        
        for manifest_name, manifest_content in deployment_manifests.items():
            try:
                docs = list(yaml.safe_load_all(manifest_content))
                
                for doc in docs:
                    if not doc:
                        continue
                    
                    kind = doc.get("kind", "")
                    
                    if kind == "Secret":
                        secrets_found = True
                        status["secrets_encrypted"] = "enabled"
                    elif kind == "Ingress":
                        spec = doc.get("spec", {})
                        if spec.get("tls"):
                            tls_found = True
                            status["tls_enabled"] = "enabled"
                            
            except yaml.YAMLError:
                continue
        
        if not secrets_found:
            status["secrets_encrypted"] = "not_implemented"
        if not tls_found:
            status["tls_enabled"] = "not_implemented"
        
        # Data at rest encryption is typically cluster-level
        status["data_at_rest"] = "cluster_dependent"
        
        return status
    
    def _generate_security_recommendations(self, 
                                         vulnerabilities: List[Dict[str, Any]],
                                         hardening_status: Dict[str, str],
                                         encryption_status: Dict[str, str]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # High severity vulnerabilities
        high_severity = [v for v in vulnerabilities if v.get("severity") == "high"]
        if high_severity:
            recommendations.append(f"Address {len(high_severity)} high-severity security issues immediately")
        
        # Hardening recommendations
        for component, status in hardening_status.items():
            if status == "not_implemented":
                recommendations.append(f"Implement {component.replace('_', ' ')} for better security")
        
        # Encryption recommendations
        for component, status in encryption_status.items():
            if status == "not_implemented":
                recommendations.append(f"Enable {component.replace('_', ' ')} to protect sensitive data")
        
        # General recommendations
        if len(vulnerabilities) > 10:
            recommendations.append("Consider implementing a security scanning pipeline")
        
        if not recommendations:
            recommendations.append("Security posture is good - consider regular security reviews")
        
        return recommendations
    
    def _calculate_security_score(self, vulnerabilities: List[Dict[str, Any]], hardening_status: Dict[str, str]) -> float:
        """Calculate overall security score (0-100)"""
        base_score = 100.0
        
        # Deduct points for vulnerabilities
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            if severity == "critical":
                base_score -= 20
            elif severity == "high":
                base_score -= 10
            elif severity == "medium":
                base_score -= 5
            elif severity == "low":
                base_score -= 2
        
        # Deduct points for missing hardening
        implemented_count = sum(1 for status in hardening_status.values() if status == "implemented")
        total_count = len(hardening_status)
        hardening_ratio = implemented_count / total_count if total_count > 0 else 0
        
        base_score = base_score * (0.5 + 0.5 * hardening_ratio)  # At least 50% score with no hardening
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_compliance_score(self, hardening_status: Dict[str, str], encryption_status: Dict[str, str]) -> float:
        """Calculate compliance score (0-100)"""
        total_controls = len(hardening_status) + len(encryption_status)
        implemented_controls = 0
        
        for status in hardening_status.values():
            if status == "implemented":
                implemented_controls += 1
        
        for status in encryption_status.values():
            if status in ["enabled", "cluster_dependent"]:
                implemented_controls += 1
        
        return (implemented_controls / total_controls * 100) if total_controls > 0 else 0


# Import pandas if available for timestamp handling
try:
    import pandas as pd
except ImportError:
    # Fallback for timestamp handling
    import datetime
    class pd:
        @staticmethod
        def Timestamp():
            return datetime.datetime
        
        @staticmethod
        def now():
            return datetime.datetime.now()