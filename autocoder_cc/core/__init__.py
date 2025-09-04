"""
Core Configuration and Settings Management
=========================================

The core module provides centralized configuration management, environment-based settings,
and production-ready configuration validation for the Autocoder4_CC system.

## Overview

This module implements a **zero-hardcoded-secrets** configuration system that:
- Loads all settings from environment variables or `.env` files
- Validates configuration using Pydantic for type safety
- Enforces production security requirements
- Provides deterministic port allocation for distributed systems

## Key Components

### Settings Class
The main configuration class that manages all system settings including:
- LLM API keys and model selection
- Database connection URLs
- Security settings (JWT, rate limiting)
- Observability endpoints
- Deployment configuration

### Configuration Validation
Production-ready validation that ensures:
- No hardcoded secrets in production
- Secure database credentials
- Proper environment-specific settings
- Required environment variables are present

## Usage

```python
from autocoder_cc.core import settings

# Access configuration
api_key = settings.get_llm_api_key()
model = settings.get_llm_model()
port = settings.get_hash_based_port("api-service", "my-system")

# Validate production settings
settings.validate_production_settings()
```

## Environment Variables

### Required (Production)
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM API key
- `JWT_SECRET_KEY`: Secure JWT signing key
- `POSTGRES_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### Optional
- `ENVIRONMENT`: "development" | "production" | "staging"
- `DEBUG_MODE`: Enable debug logging
- `ENABLE_METRICS`: Enable Prometheus metrics
- `ENABLE_TRACING`: Enable Jaeger tracing

## Security Features

- **No Hardcoded Secrets**: All secrets must be provided via environment
- **Production Validation**: Automatic checks for insecure defaults
- **Secret Validation**: Prevents common test/default values
- **Environment Isolation**: Separate configs for dev/staging/prod

## Port Management

The system provides deterministic port allocation for distributed components:

```python
# Consistent port allocation based on component and system names
port = settings.get_hash_based_port("api-service", "customer-analytics")
# Returns same port for same component/system combination
```

## Configuration Hierarchy

1. Environment variables (highest priority)
2. `.env` file in current directory
3. Default values (lowest priority)

All configuration is validated on startup to catch issues early.
"""

# Autocoder core package 