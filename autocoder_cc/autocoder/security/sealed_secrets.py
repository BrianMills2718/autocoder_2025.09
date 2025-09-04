from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Sealed Secrets Manager for Autocoder V5.2

Implements automated secret management using Kubernetes Sealed Secrets
for production deployments. Provides secure handling of sensitive configuration
without storing secrets in version control.

## Overview

Sealed Secrets encrypt secrets at deploy time and can only be decrypted
by the Sealed Secrets controller in the target Kubernetes cluster.
This ensures secrets are never stored in plaintext in repositories.

## Key Features

1. **Automatic Secret Detection**: Scans configuration for sensitive values
2. **Sealed Secret Generation**: Creates encrypted sealed secret manifests
3. **Template Integration**: Integrates with deployment template generation
4. **Environment Validation**: Ensures secrets are properly configured
5. **Security Best Practices**: Follows Kubernetes security standards

## Usage

```python
from autocoder_cc.security.sealed_secrets import SealedSecretsManager

manager = SealedSecretsManager(
    namespace="production",
    controller_url="https://sealed-secrets.kube-system.svc.cluster.local:8080"
)

# Detect and seal secrets from configuration
sealed_manifest = await manager.create_sealed_secret(
    secret_name="app-secrets",
    secret_data={
        "DATABASE_PASSWORD": "supersecret123",
        "JWT_SECRET": "jwt-signing-key",
        "API_KEY": "external-api-key"
    }
)

# Generate deployment with sealed secrets reference
deployment = manager.generate_deployment_with_secrets(
    app_name="my-app",
    sealed_secret_name="app-secrets"
)
```
"""

import base64
import json
import yaml
import logging
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import re
import os

from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.autocoder.security.process_executor import ProcessExecutor, SubprocessExecutor
from autocoder_cc.autocoder.security.filesystem_manager import FileSystemManager, TempFileManager


def find_kubeseal_binary() -> str:
    """Find kubeseal binary in common locations"""
    search_paths = [
        "kubeseal",  # System PATH
        os.path.expanduser("~/.local/bin/kubeseal"),  # User local
        "/usr/local/bin/kubeseal",  # System local
        "/usr/bin/kubeseal"  # System global
    ]
    
    for path in search_paths:
        if Path(path).exists():
            return path
        # Check if it's available in PATH
        try:
            result = subprocess.run(["which", path], capture_output=True, text=True)
            if result.returncode == 0:
                return path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    raise RuntimeError("kubeseal binary not found in any standard location")


@dataclass
class SecretField:
    """Represents a secret field that needs to be sealed."""
    name: str
    value: str
    description: str
    required: bool = True
    category: str = "general"  # database, auth, api, etc.


@dataclass
class SealedSecretManifest:
    """Represents a Sealed Secret Kubernetes manifest."""
    name: str
    namespace: str
    encrypted_data: Dict[str, str]
    metadata: Dict[str, Any]
    raw_yaml: str


class SealedSecretsManager:
    """
    Manages Sealed Secrets for secure deployment of sensitive configuration.
    
    This manager automatically detects secrets in configuration, encrypts them
    using the Sealed Secrets controller, and generates appropriate Kubernetes
    manifests for secure deployment.
    """
    
    def __init__(
        self,
        namespace: str = "default",
        controller_url: Optional[str] = None,
        kubeseal_binary: Optional[str] = None,
        process_executor: Optional[ProcessExecutor] = None,
        filesystem_manager: Optional[FileSystemManager] = None
    ):
        self.namespace = namespace
        self.controller_url = controller_url
        self.kubeseal_binary = kubeseal_binary or find_kubeseal_binary()
        self.logger = get_logger(self.__class__.__name__)
        self.error_handler = ConsistentErrorHandler("SealedSecretsManager")
        
        # Inject dependencies with defaults
        self.process_executor = process_executor or SubprocessExecutor()
        self.filesystem_manager = filesystem_manager or TempFileManager()
        
        # Secret detection patterns
        self.secret_patterns = {
            "password": re.compile(r'.*password.*', re.IGNORECASE),
            "secret": re.compile(r'.*secret.*', re.IGNORECASE),
            "key": re.compile(r'.*(?:api_?key|private_?key|secret_?key).*', re.IGNORECASE),
            "token": re.compile(r'.*token.*', re.IGNORECASE),
            "credentials": re.compile(r'.*(?:cred|auth).*', re.IGNORECASE),
        }
        
        # Environment variable prefixes that indicate secrets
        self.secret_env_prefixes = [
            "SECRET_", "PASSWORD_", "TOKEN_", "KEY_", "PRIVATE_"
        ]
    
    @handle_errors("SealedSecretsManager", operation="detect_secrets")
    def detect_secrets_in_config(self, config: Dict[str, Any]) -> List[SecretField]:
        """
        Automatically detect potential secrets in configuration.
        
        Args:
            config: Configuration dictionary to scan
            
        Returns:
            List of detected secret fields
        """
        secrets = []
        
        def scan_dict(data: Dict[str, Any], prefix: str = "") -> None:
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    scan_dict(value, full_key)
                elif isinstance(value, str) and self._is_likely_secret(key, value):
                    secrets.append(SecretField(
                        name=self._sanitize_secret_name(full_key),
                        value=value,
                        description=f"Auto-detected secret: {full_key}",
                        category=self._categorize_secret(key)
                    ))
        
        scan_dict(config)
        
        self.logger.info(f"Detected {len(secrets)} potential secrets in configuration")
        return secrets
    
    def _is_likely_secret(self, key: str, value: str) -> bool:
        """Determine if a key-value pair is likely a secret."""
        # Check key patterns
        for pattern_name, pattern in self.secret_patterns.items():
            if pattern.match(key):
                return True
        
        # Check environment variable prefixes
        key_upper = key.upper()
        for prefix in self.secret_env_prefixes:
            if key_upper.startswith(prefix):
                return True
        
        # Check value characteristics (but be careful not to flag non-secrets)
        if isinstance(value, str):
            # Long random-looking strings
            if len(value) > 20 and any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
                return True
            
            # Base64-encoded looking strings
            if len(value) > 16 and value.replace('+', '').replace('/', '').replace('=', '').isalnum():
                return True
        
        return False
    
    def _categorize_secret(self, key: str) -> str:
        """Categorize a secret based on its key name."""
        key_lower = key.lower()
        
        if any(term in key_lower for term in ['db', 'database', 'postgres', 'mysql', 'redis']):
            return "database"
        elif any(term in key_lower for term in ['jwt', 'auth', 'oauth', 'session']):
            return "authentication"
        elif any(term in key_lower for term in ['api', 'external', 'service']):
            return "api"
        elif any(term in key_lower for term in ['cert', 'tls', 'ssl', 'private']):
            return "certificates"
        else:
            return "general"
    
    def _sanitize_secret_name(self, name: str) -> str:
        """Sanitize secret name for Kubernetes compatibility."""
        # Convert to uppercase with underscores (environment variable style)
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.upper())
        return sanitized
    
    @handle_errors("SealedSecretsManager", operation="create_sealed_secret")
    async def create_sealed_secret(
        self,
        secret_name: str,
        secret_data: Dict[str, str],
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None
    ) -> SealedSecretManifest:
        """
        Create a Sealed Secret from plaintext secret data.
        
        Args:
            secret_name: Name of the secret
            secret_data: Dictionary of secret key-value pairs
            labels: Optional labels for the secret
            annotations: Optional annotations for the secret
            
        Returns:
            SealedSecretManifest containing the encrypted secret
        """
        try:
            # Validate kubeseal availability
            await self._ensure_kubeseal_available()
            
            # Create a temporary regular Kubernetes secret
            secret_manifest = self._create_secret_manifest(
                secret_name, secret_data, labels, annotations
            )
            
            # Use kubeseal to encrypt the secret
            sealed_manifest_yaml = await self._seal_secret(secret_manifest)
            
            # Parse the sealed secret
            sealed_data = yaml.safe_load(sealed_manifest_yaml)
            
            return SealedSecretManifest(
                name=secret_name,
                namespace=self.namespace,
                encrypted_data=sealed_data.get('spec', {}).get('encryptedData', {}),
                metadata=sealed_data.get('metadata', {}),
                raw_yaml=sealed_manifest_yaml
            )
            
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={
                    "secret_name": secret_name,
                    "namespace": self.namespace,
                    "operation": "create_sealed_secret"
                },
                operation="sealed_secret_creation"
            )
            raise
    
    async def _ensure_kubeseal_available(self) -> None:
        """Ensure kubeseal binary is available and functional with comprehensive validation."""
        try:
            # 1. Check if kubeseal binary exists and is executable
            result = await self.process_executor.run(
                [self.kubeseal_binary, "--version"],
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"kubeseal not working: {result.stderr}")
            
            version_output = result.stdout.strip()
            self.logger.info(f"kubeseal binary found: {version_output}")
            
            # 2. Validate kubeseal version (require minimum version) - FAIL HARD
            # Handle both "v0.18.0" and "kubeseal version: 0.18.0" formats
            version_match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', version_output)
            if version_match:
                major, minor, patch = map(int, version_match.groups())
                # Require kubeseal v0.18.0 or higher for production use - ENFORCE FAIL-HARD
                if (major, minor, patch) < (0, 18, 0):
                    raise RuntimeError(
                        f"FAIL-HARD: kubeseal version {major}.{minor}.{patch} is insufficient for production use. "
                        f"Minimum required version is v0.18.0 for security and compatibility. "
                        f"V5.0 requires minimum version enforcement - no exceptions allowed. "
                        f"Please upgrade kubeseal to v0.18.0 or higher."
                    )
            else:
                raise RuntimeError(
                    "FAIL-HARD: Could not parse kubeseal version from output. "
                    "V5.0 requires verifiable version information for security validation. "
                    "Please ensure kubeseal is properly installed and accessible."
                )
            
            # 3. Test kubeseal help command to ensure it's fully functional
            help_result = await self.process_executor.run(
                [self.kubeseal_binary, "--help"],
                timeout=5
            )
            # kubeseal --help returns exit code 2 but with help text in stderr - this is normal
            if help_result.returncode == 2 and "Usage of kubeseal:" in help_result.stderr:
                self.logger.info("kubeseal help command verified - binary is functional")
            elif help_result.returncode != 0:
                raise RuntimeError(f"kubeseal help command failed: {help_result.stderr}")
            
            # 4. Check if controller URL is accessible (if provided)
            if self.controller_url:
                await self._validate_controller_connectivity()
            else:
                self.logger.info("No controller URL provided - will use cluster-local discovery")
            
            # 5. Test basic kubeseal functionality with a dummy secret
            await self._test_kubeseal_functionality()
            
            self.logger.info("✅ kubeseal validation passed - ready for production use")
            
        except FileNotFoundError:
            raise RuntimeError(
                f"kubeseal binary not found at '{self.kubeseal_binary}'. "
                "Install kubeseal:\n"
                "  • Linux: wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/kubeseal-0.18.0-linux-amd64.tar.gz\n"
                "  • macOS: brew install kubeseal\n"
                "  • Windows: choco install kubeseal\n"
                "  • Or download from: https://github.com/bitnami-labs/sealed-secrets/releases"
            )
        except TimeoutError:
            raise RuntimeError(
                f"kubeseal command timed out. This may indicate:\n"
                "  • Binary is corrupted or incompatible\n"
                "  • System resource constraints\n"
                "  • Network connectivity issues"
            )
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={
                    "kubeseal_binary": self.kubeseal_binary,
                    "controller_url": self.controller_url,
                    "namespace": self.namespace,
                    "operation": "kubeseal_validation"
                },
                operation="kubeseal_validation"
            )
            raise
    
    async def _validate_controller_connectivity(self) -> None:
        """Validate connectivity to Sealed Secrets controller."""
        try:
            # Test controller reachability
            test_result = await self.process_executor.run(
                [self.kubeseal_binary, "--controller-name=sealed-secrets-controller", 
                 "--controller-namespace=kube-system", "--fetch-cert", "--cert=/dev/null"],
                timeout=30
            )
            
            if test_result.returncode == 0:
                self.logger.info("✅ Sealed Secrets controller is reachable")
            else:
                raise RuntimeError(
                    f"FAIL-HARD: Cannot reach Sealed Secrets controller: {test_result.stderr}. "
                    f"V5.0 requires operational Sealed Secrets controller for production deployments. "
                    f"Ensure the controller is installed and running in your cluster. "
                    f"No fallback to insecure secret handling allowed."
                )
        except TimeoutError:
            raise RuntimeError(
                "FAIL-HARD: Sealed Secrets controller connectivity test timed out. "
                "V5.0 requires responsive controller for production use. "
                "Check network connectivity and controller health."
            )
        except Exception as e:
            raise RuntimeError(
                f"FAIL-HARD: Sealed Secrets controller connectivity test failed: {e}. "
                f"V5.0 requires verified controller connectivity for secure deployments."
            )
    
    async def _test_kubeseal_functionality(self) -> None:
        """Test basic kubeseal functionality with a dummy secret."""
        try:
            # Create a minimal test secret
            test_secret = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "test-secret",
                    "namespace": self.namespace
                },
                "data": {
                    "test-key": base64.b64encode(b"test-value").decode('utf-8')
                }
            }
            
            test_yaml = yaml.dump(test_secret)
            
            # Test kubeseal encryption
            with self.filesystem_manager.temporary_file(mode='w', suffix='.yaml', delete=False) as temp_file:
                temp_file.write(test_yaml)
                temp_file.flush()
                
                try:
                    result = await self.process_executor.run(
                        [self.kubeseal_binary, "--format=yaml", 
                         "--namespace", self.namespace],
                        input_data=test_yaml,
                        timeout=15
                    )
                    
                    if result.returncode == 0:
                        # Validate the output looks like a proper SealedSecret
                        try:
                            sealed_secret = yaml.safe_load(result.stdout)
                            if (sealed_secret.get('kind') == 'SealedSecret' and 
                                'spec' in sealed_secret and 
                                'encryptedData' in sealed_secret.get('spec', {})):
                                self.logger.info("✅ kubeseal functionality test passed")
                            else:
                                raise RuntimeError(
                                    "FAIL-HARD: kubeseal output does not appear to be a valid SealedSecret. "
                                    "V5.0 requires functional sealing capabilities for secure deployment."
                                )
                        except yaml.YAMLError as e:
                            raise RuntimeError(
                                f"FAIL-HARD: kubeseal produced invalid YAML: {e}. "
                                "V5.0 requires proper YAML output for secure deployment manifests."
                            )
                    else:
                        raise RuntimeError(
                            f"FAIL-HARD: kubeseal test failed: {result.stderr}. "
                            f"V5.0 requires functional kubeseal operation for production security."
                        )
                        
                finally:
                    # Clean up temp file
                    self.filesystem_manager.remove_file(temp_file.name)
                        
        except Exception as e:
            raise RuntimeError(
                f"FAIL-HARD: kubeseal functionality test failed: {e}. "
                f"V5.0 requires verified kubeseal functionality for secure deployment."
            )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate SealedSecretsManager configuration and return status."""
        config_status = {
            "namespace": self.namespace,
            "controller_url": self.controller_url,
            "kubeseal_binary": self.kubeseal_binary,
            "validation_status": "pending",
            "issues": [],
            "recommendations": []
        }
        
        # Validate namespace format
        if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', self.namespace):
            config_status["issues"].append(
                f"Invalid namespace '{self.namespace}' - must follow Kubernetes naming conventions"
            )
        
        # Check kubeseal binary path
        if not self.kubeseal_binary or self.kubeseal_binary.strip() == "":
            config_status["issues"].append("kubeseal binary path is empty")
        
        # Validate controller URL format if provided
        if self.controller_url:
            if not (self.controller_url.startswith('http://') or self.controller_url.startswith('https://')):
                config_status["issues"].append(
                    f"Invalid controller URL '{self.controller_url}' - must start with http:// or https://"
                )
        else:
            config_status["recommendations"].append(
                "Consider specifying controller_url for more reliable connectivity"
            )
        
        if not config_status["issues"]:
            config_status["validation_status"] = "valid"
        else:
            config_status["validation_status"] = "invalid"
        
        return config_status
    
    def _create_secret_manifest(
        self,
        secret_name: str,
        secret_data: Dict[str, str],
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a standard Kubernetes secret manifest."""
        # Encode secret values as base64
        encoded_data = {}
        for key, value in secret_data.items():
            encoded_data[key] = base64.b64encode(value.encode('utf-8')).decode('utf-8')
        
        # Build metadata
        metadata = {
            "name": secret_name,
            "namespace": self.namespace
        }
        
        if labels:
            metadata["labels"] = labels
        
        if annotations:
            metadata["annotations"] = annotations
        
        # Create the secret manifest
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": metadata,
            "type": "Opaque",
            "data": encoded_data
        }
        
        return yaml.dump(secret_manifest, default_flow_style=False)
    
    async def _seal_secret(self, secret_manifest: str) -> str:
        """Use kubeseal to encrypt a secret manifest."""
        with self.filesystem_manager.temporary_file(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write(secret_manifest)
            temp_file.flush()
            
            try:
                # Build kubeseal command
                cmd = [self.kubeseal_binary, "-o", "yaml"]
                
                if self.controller_url:
                    cmd.extend(["--controller-namespace", "kube-system"])
                    cmd.extend(["--controller-name", "sealed-secrets-controller"])
                
                # Run kubeseal
                result = await self.process_executor.run(
                    cmd,
                    input_data=secret_manifest,
                    timeout=30
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"kubeseal failed: {result.stderr}")
                
                return result.stdout
                
            finally:
                # Clean up temporary file
                self.filesystem_manager.remove_file(temp_file.name)
    
    def generate_deployment_with_secrets(
        self,
        app_name: str,
        sealed_secret_name: str,
        container_image: str = "app:latest",
        port: int = 8000,
        additional_env: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a Kubernetes deployment that references sealed secrets.
        
        Args:
            app_name: Name of the application
            sealed_secret_name: Name of the sealed secret to reference
            container_image: Container image to deploy
            port: Container port
            additional_env: Additional environment variables (non-secret)
            
        Returns:
            YAML string containing the deployment manifest
        """
        # Build environment variables
        env_vars = []
        
        # Add non-secret environment variables
        if additional_env:
            for key, value in additional_env.items():
                env_vars.append({
                    "name": key,
                    "value": value
                })
        
        # Reference all secrets from the sealed secret
        env_vars.append({
            "name": "SECRETS_FROM",
            "valueFrom": {
                "secretKeyRef": {
                    "name": sealed_secret_name,
                    "key": "secrets"
                }
            }
        })
        
        # Create deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name,
                "namespace": self.namespace,
                "labels": {
                    "app": app_name,
                    "managed-by": "autocoder-v5.2"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": app_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": app_name
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": app_name,
                            "image": container_image,
                            "ports": [{
                                "containerPort": port,
                                "protocol": "TCP"
                            }],
                            "envFrom": [{
                                "secretRef": {
                                    "name": sealed_secret_name
                                }
                            }],
                            "env": env_vars,
                            "resources": {
                                "requests": {
                                    "memory": "128Mi",
                                    "cpu": "100m"
                                },
                                "limits": {
                                    "memory": "512Mi",
                                    "cpu": "500m"
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": port
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/ready",
                                    "port": port
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }],
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "fsGroup": 1000
                        }
                    }
                }
            }
        }
        
        return yaml.dump(deployment, default_flow_style=False)
    
    def generate_secret_usage_documentation(
        self,
        sealed_secret_name: str,
        secret_fields: List[SecretField]
    ) -> str:
        """
        Generate documentation for secret usage and management.
        
        Args:
            sealed_secret_name: Name of the sealed secret
            secret_fields: List of secret fields in the secret
            
        Returns:
            Markdown documentation string
        """
        doc = f"""# Sealed Secrets Documentation

## Secret: {sealed_secret_name}

This document describes the sealed secrets used in this deployment and how to manage them.

### Overview

This deployment uses Kubernetes Sealed Secrets to securely manage sensitive configuration.
Sealed Secrets encrypt secrets at build time and can only be decrypted by the Sealed Secrets
controller in the target Kubernetes cluster.

### Secret Fields

The following secret fields are configured:

| Field Name | Category | Required | Description |
|------------|----------|----------|-------------|
"""
        
        # Group secrets by category
        by_category = {}
        for field in secret_fields:
            category = field.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(field)
        
        # Add fields to documentation
        for category, fields in by_category.items():
            for field in fields:
                required = "Yes" if field.required else "No"
                doc += f"| `{field.name}` | {field.category} | {required} | {field.description} |\n"
        
        doc += f"""
### Updating Secrets

To update secrets in this deployment:

1. **Update Secret Values**: Modify the secret values in your secure configuration store
2. **Recreate Sealed Secret**: Run the sealed secret generation process:
   ```bash
   # Generate new sealed secret
   autocoder generate-sealed-secret --name {sealed_secret_name} --namespace {self.namespace}
   ```
3. **Apply Updated Secret**: Apply the new sealed secret to the cluster:
   ```bash
   kubectl apply -f {sealed_secret_name}-sealed.yaml
   ```
4. **Restart Deployment**: Restart the deployment to pick up new secrets:
   ```bash
   kubectl rollout restart deployment/{sealed_secret_name}
   ```

### Security Best Practices

1. **Never Commit Plaintext Secrets**: Always use sealed secrets for sensitive data
2. **Rotate Secrets Regularly**: Update secrets according to your security policy
3. **Monitor Secret Access**: Use Kubernetes RBAC to control secret access
4. **Backup Sealed Secrets**: Store sealed secret manifests in version control

### Troubleshooting

#### Secret Not Available
If pods report missing secrets:
1. Verify the sealed secret exists: `kubectl get sealedsecrets`
2. Check secret decryption: `kubectl get secrets`
3. Verify RBAC permissions for the service account

#### Secret Decryption Failed
If secrets fail to decrypt:
1. Ensure Sealed Secrets controller is running
2. Verify the sealed secret was created for the correct cluster
3. Check controller logs for decryption errors

For more information, see the [Sealed Secrets documentation](https://sealed-secrets.netlify.app/).
"""
        
        return doc
    
    @handle_errors("SealedSecretsManager", operation="validate_sealed_secrets_setup")
    async def validate_sealed_secrets_setup(self) -> Dict[str, Any]:
        """
        Validate that the Sealed Secrets setup is working correctly.
        
        Returns:
            Dictionary containing validation results
        """
        results = {
            "kubeseal_available": False,
            "controller_reachable": False,
            "can_encrypt": False,
            "errors": []
        }
        
        try:
            # Test kubeseal availability
            await self._ensure_kubeseal_available()
            results["kubeseal_available"] = True
            
            # Test encryption capability
            test_secret = self._create_secret_manifest(
                "test-secret",
                {"test": "value"}
            )
            
            sealed_output = await self._seal_secret(test_secret)
            if "kind: SealedSecret" in sealed_output:
                results["can_encrypt"] = True
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results


def create_sealed_secrets_for_system(
    system_config: Dict[str, Any],
    namespace: str = "default",
    output_dir: Optional[Path] = None
) -> List[SealedSecretManifest]:
    """
    Convenience function to create sealed secrets for an entire system configuration.
    
    Args:
        system_config: System configuration dictionary
        namespace: Kubernetes namespace
        output_dir: Optional directory to write manifest files
        
    Returns:
        List of created sealed secret manifests
    """
    manager = SealedSecretsManager(namespace=namespace)
    
    # Detect secrets in configuration
    detected_secrets = manager.detect_secrets_in_config(system_config)
    
    if not detected_secrets:
        logging.info("No secrets detected in system configuration")
        return []
    
    # Group secrets by category for better organization
    secrets_by_category = {}
    for secret in detected_secrets:
        category = secret.category
        if category not in secrets_by_category:
            secrets_by_category[category] = {}
        secrets_by_category[category][secret.name] = secret.value
    
    # Create sealed secrets for each category
    manifests = []
    for category, secret_data in secrets_by_category.items():
        secret_name = f"app-{category}-secrets"
        
        try:
            # Note: This is a sync wrapper - in practice you'd use async
            import asyncio
            manifest = asyncio.run(manager.create_sealed_secret(
                secret_name=secret_name,
                secret_data=secret_data,
                labels={
                    "app.kubernetes.io/component": "secrets",
                    "app.kubernetes.io/managed-by": "autocoder-v5.2",
                    "autocoder.io/secret-category": category
                }
            ))
            manifests.append(manifest)
            
            # Write manifest to file if output directory specified
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                manifest_file = output_dir / f"{secret_name}-sealed.yaml"
                with open(manifest_file, 'w') as f:
                    f.write(manifest.raw_yaml)
                logging.info(f"Wrote sealed secret manifest: {manifest_file}")
            
        except Exception as e:
            logging.error(f"Failed to create sealed secret for {category}: {e}")
    
    return manifests