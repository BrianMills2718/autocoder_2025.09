#!/usr/bin/env python3
"""
Secure Secret Generation Utility

This script helps users generate cryptographically secure secrets
for production deployments using the SecretsManager.

Usage:
    python tools/generate_secrets.py --type password
    python tools/generate_secrets.py --type jwt_secret
    python tools/generate_secrets.py --type api_key --prefix myapp
    python tools/generate_secrets.py --all-secrets system-name
"""

import argparse
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from autocoder_cc.production.secrets_manager import SecretsManager, SecretSpec


def generate_single_secret(secret_type: str, length: int = 32, prefix: str = None):
    """Generate a single secret of the specified type"""
    manager = SecretsManager()
    
    if secret_type == "password":
        secret = manager._generate_password(length)
    elif secret_type == "api_key":
        secret = manager._generate_api_key(length, prefix)
    elif secret_type == "jwt_secret":
        secret = manager._generate_jwt_secret()
    elif secret_type == "encryption_key":
        secret = manager._generate_encryption_key()
    else:
        secret = manager._generate_secure_string(length)
    
    return secret


def generate_system_secrets(system_name: str):
    """Generate all secrets needed for a system"""
    manager = SecretsManager()
    
    # Standard secrets for most systems
    required_secrets = [
        SecretSpec("DATABASE_PASSWORD", "password", "PostgreSQL password", length=32),
        SecretSpec("REDIS_PASSWORD", "password", "Redis password", length=32),
        SecretSpec("JWT_SECRET", "jwt_secret", "JWT signing secret"),
        SecretSpec("API_SECRET_KEY", "api_key", "API authentication key"),
        SecretSpec("GRAFANA_ADMIN_PASSWORD", "password", "Grafana admin password", length=24),
        SecretSpec("RABBITMQ_PASSWORD", "password", "RabbitMQ password", length=32),
    ]
    
    secrets = manager.generate_secrets_manifest(system_name, required_secrets)
    
    return secrets, required_secrets


def generate_env_file(secrets: dict, output_file: str = None):
    """Generate a .env file with the secrets"""
    lines = [
        "# Generated secrets for production deployment",
        "# CRITICAL: Keep this file secure and never commit to version control",
        "",
        "# Database Configuration",
        f"POSTGRES_PASSWORD={secrets.get('DATABASE_PASSWORD', '')}",
        f"REDIS_PASSWORD={secrets.get('REDIS_PASSWORD', '')}",
        "",
        "# Security Configuration", 
        f"JWT_SECRET_KEY={secrets.get('JWT_SECRET', '')}",
        f"API_SECRET_KEY={secrets.get('API_SECRET_KEY', '')}",
        "",
        "# Service Configuration",
        f"GRAFANA_ADMIN_PASSWORD={secrets.get('GRAFANA_ADMIN_PASSWORD', '')}",
        f"RABBITMQ_PASSWORD={secrets.get('RABBITMQ_PASSWORD', '')}",
        "",
        "# Production Environment",
        "ENVIRONMENT=production",
        "DEBUG_MODE=false",
        ""
    ]
    
    content = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(content)
        print(f"Secrets written to {output_file}")
    else:
        print(content)


def main():
    parser = argparse.ArgumentParser(description="Generate secure secrets for production deployment")
    
    # Single secret generation
    parser.add_argument("--type", choices=["password", "api_key", "jwt_secret", "encryption_key", "random"],
                       help="Type of secret to generate")
    parser.add_argument("--length", type=int, default=32,
                       help="Length of the secret (default: 32)")
    parser.add_argument("--prefix", type=str,
                       help="Prefix for API keys")
    
    # System secrets generation
    parser.add_argument("--system", type=str,
                       help="Generate all secrets for a system")
    parser.add_argument("--output", type=str,
                       help="Output file for generated secrets (.env format)")
    
    # Options
    parser.add_argument("--validate", action="store_true",
                       help="Validate that secrets are secure")
    
    args = parser.parse_args()
    
    if args.system:
        # Generate all secrets for a system
        print(f"Generating secure secrets for system: {args.system}")
        print("=" * 50)
        
        secrets, specs = generate_system_secrets(args.system)
        
        # Display secrets
        for spec in specs:
            secret_value = secrets.get(spec.name, '')
            print(f"{spec.name}: {secret_value}")
            print(f"  Description: {spec.description}")
            print(f"  Type: {spec.type}")
            print(f"  Length: {len(secret_value)} characters")
            print()
        
        # Validate secrets
        if args.validate:
            manager = SecretsManager()
            errors = manager.validate_secrets(secrets)
            if errors:
                print("⚠️  Validation errors:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("✅ All secrets passed validation")
        
        # Generate .env file if requested
        if args.output:
            generate_env_file(secrets, args.output)
        elif not args.output and input("\nGenerate .env file? (y/N): ").lower().startswith('y'):
            env_file = f"{args.system}.env"
            generate_env_file(secrets, env_file)
    
    elif args.type:
        # Generate single secret
        secret = generate_single_secret(args.type, args.length, args.prefix)
        print(f"Generated {args.type}: {secret}")
        print(f"Length: {len(secret)} characters")
        
        # Validate if requested
        if args.validate:
            manager = SecretsManager()
            errors = manager.validate_secrets({args.type: secret})
            if errors:
                print("⚠️  Validation errors:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("✅ Secret passed validation")
    
    else:
        # Show usage examples
        print("Secure Secret Generation Utility")
        print("=" * 40)
        print()
        print("Generate a secure password:")
        print("  python tools/generate_secrets.py --type password --length 32")
        print()
        print("Generate a JWT secret:")
        print("  python tools/generate_secrets.py --type jwt_secret")
        print()
        print("Generate an API key with prefix:")
        print("  python tools/generate_secrets.py --type api_key --prefix myapp")
        print()
        print("Generate all secrets for a system:")
        print("  python tools/generate_secrets.py --system my-system --output my-system.env")
        print()
        print("Quick password generation:")
        password = generate_single_secret("password", 32)
        print(f"Sample secure password: {password}")


if __name__ == "__main__":
    main()