"""
Dockerfile generator plugin for the scaffold generation system.
Follows Enterprise Roadmap v2 plugin architecture.
"""
from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Template
from autocoder_cc.core.config import settings


class DockerfileGenerator:
    """Generates Dockerfile for autocoder systems."""
    
    def generate(self, blueprint: Dict[str, Any]) -> str:
        """Generate Dockerfile content based on system blueprint using Jinja2."""
        system_name = blueprint.get('system', {}).get('name', 'autocoder-app')
        components = blueprint.get('system', {}).get('components', [])
        
        # Determine if we need database support
        has_database = any(comp.get('type') == 'Store' for comp in components)
        has_redis = any(comp.get('type') == 'Accumulator' for comp in components)
        has_rabbitmq = any(comp.get('type') == 'MessageBus' for comp in components)
        
        # Prepare template variables
        template_vars = {
            'system_name': system_name,
            'has_database': has_database,
            'has_redis': has_redis,
            'has_rabbitmq': has_rabbitmq,
            'port_range_start': settings.PORT_RANGE_START,
            'port_range_end': settings.PORT_RANGE_END,
            'environment': settings.ENVIRONMENT,
            'log_level': settings.LOG_LEVEL,
            'default_postgres_url': settings.DEFAULT_POSTGRES_URL,
            'default_redis_url': settings.DEFAULT_REDIS_URL,
            'default_rabbitmq_url': settings.DEFAULT_RABBITMQ_URL
        }
        
        dockerfile_template = Template('''# Generated Dockerfile for {{ system_name }}
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables from central config
{% if has_database -%}
ENV DATABASE_URL=${DATABASE_URL:-{{ default_postgres_url }}}
{% endif -%}
{% if has_redis -%}
ENV REDIS_URL=${REDIS_URL:-{{ default_redis_url }}}
{% endif -%}
{% if has_rabbitmq -%}
ENV RABBITMQ_URL=${RABBITMQ_URL:-{{ default_rabbitmq_url }}}
{% endif -%}
ENV PORT_RANGE_START={{ port_range_start }}
ENV PORT_RANGE_END={{ port_range_end }}
ENV ENVIRONMENT={{ environment }}
ENV LOG_LEVEL={{ log_level }}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://127.0.0.1:${DEFAULT_API_PORT:-8000}/health || exit 1

# Default command
CMD ["python", "main.py"]''')
        
        return dockerfile_template.render(**template_vars)