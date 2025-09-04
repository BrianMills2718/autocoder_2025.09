#!/usr/bin/env python3
"""
Setup script for Autocoder V5.2
"""
from setuptools import setup, find_packages

setup(
    name="autocoder",
    version="5.2.0",
    description="Autocoder V5.2 - Hybrid Architecture Generation Engine",
    packages=find_packages(),
    install_requires=[
        # Core structured concurrency and communication
        "anyio>=4.0.0",
        
        # Component generation and validation
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.21.0",
        
        # HTTP frameworks for API components
        "fastapi>=0.111.0",
        "uvicorn>=0.24.0",
        "httpx>=0.25.0",
        
        # Database connections for Store components
        "databases[postgresql]>=0.8.0",
        "asyncpg>=0.29.0",
        
        # Redis connections for Accumulator components
        "redis[hiredis]>=5.0.0",
        
        # Testing infrastructure
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        
        # Schema validation
        "jsonschema>=4.20.0",
        
        # Development utilities
        "black>=23.0.0",
        "ruff>=0.1.0",
        
        # LLM integrations
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        
        # CLI dependencies
        "click>=8.0.0",
        "colorama>=0.4.0",
        "watchdog>=3.0.0",
        
        # Observability stack
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-jaeger>=1.20.0",
        "opentelemetry-exporter-otlp>=1.20.0"
    ],
    python_requires=">=3.9",
    entry_points={
        'console_scripts': [
            'autocoder=autocoder.cli.main:cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers", 
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)