#!/usr/bin/env python3
"""
Runtime defaults for the port-based architecture.
This is the single source of truth for runtime configuration.

Referenced by: docs/implementation_roadmap/.../06_DECISIONS/STATUS_SOT.md
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# =============================================================================
# CHECKPOINT CONFIGURATION
# =============================================================================

CHECKPOINT_CONFIG = {
    "type": "sqlite",  # v1: SQLite, v2: consider PostgreSQL
    "base_path": os.environ.get(
        "AUTOCODER4_CC_DATA_DIR", 
        "/var/lib/autocoder4_cc/checkpoints"
    ),
    "file_pattern": "{system_id}.db",
    "snapshot_interval_seconds": 60,
    "max_snapshots": 10,
    "wal_mode": True,  # Write-ahead logging for better concurrency
}

# Triggers for PostgreSQL migration (if ANY are met)
POSTGRES_MIGRATION_TRIGGERS = {
    "multi_process_access": False,  # Need to read/write from multiple processes
    "steady_state_writes_per_sec": 1.0,  # More than 1 write/second sustained
    "database_size_gb": 1.0,  # Database file exceeds 1 GB
    "recovery_time_objective_sec": 10,  # RTO < 10 seconds required
}

# =============================================================================
# PII MASKING CONFIGURATION
# =============================================================================

# Default PII fields to mask (v1: top-level keys only)
PII_DENYLIST = [
    "email",
    "password", 
    "ssn",
    "phone",
    "token",
    "api_key",
    "secret",
    "credit_card",
]

PII_MASKING_CONFIG = {
    "enabled": True,  # Default: enabled for safety
    "mask_value": "***",  # Replacement value
    "recursive": False,  # v1: top-level only, v2: recursive
    "denylist": PII_DENYLIST,
}

# =============================================================================
# METRICS CONFIGURATION
# =============================================================================

# Authoritative metric names for walking skeleton acceptance
METRICS_CONFIG = {
    "namespace": "runner",  # All metrics prefixed with "runner_"
    "acceptance_metrics": {
        "errors_total": "runner_errors_total",  # Must be 0
        "latency_p95": "runner_msg_latency_ms_p95",  # Must be < 50ms
    },
    "sampling_window": {
        "message_count": 1000,  # Test with 1000 messages
        "exclude_warmup": 100,  # Exclude first 100 messages from p95 calc
    },
}

# =============================================================================
# PORT CONFIGURATION
# =============================================================================

PORT_DEFAULTS = {
    "buffer_size": 1024,  # Default buffer size for ports
    "ingress_buffer": 128,  # Smaller for ingress ports
    "internal_buffer": 256,  # Internal port buffers
    "timeout_ms": 5000,  # Default timeout for port operations
}

# =============================================================================
# MERGER FAIRNESS (v1)
# =============================================================================

MERGER_CONFIG = {
    "strategy": "round_robin",  # v1: simple round-robin
    "burst_cap": 32,  # Read up to 32 messages before switching inputs
    "age_nudge_ms": 50,  # Check oldest message age threshold
    "age_check_interval": 512,  # Check age every N messages
}

# =============================================================================
# VALIDATION GATE CONFIGURATION
# =============================================================================

VALIDATION_CONFIG = {
    "gate_file": "integration_validation_gate.py",  # Single gate file
    "component_pass_ratio": 0.667,  # Component passes if ≥2/3 tests pass
    "system_pass_ratio": 0.95,  # System passes if ≥95% components pass
}

# =============================================================================
# GENERATOR CONFIGURATION
# =============================================================================

GENERATOR_CONFIG = {
    "output_validation": [
        "py_compile",  # First: syntax check
        "ruff",  # Second: linting
        "mypy",  # Third: type checking
    ],
    "manifest_file": "generated_manifest.json",
    "template_engine": "string",  # v1: string templates, v2: consider Jinja2
}

# =============================================================================
# ENVIRONMENT PATHS
# =============================================================================

def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(os.environ.get("AUTOCODER4_CC_DATA_DIR", "/var/lib/autocoder4_cc"))

def get_checkpoint_path(system_id: str) -> Path:
    """Get the checkpoint database path for a system."""
    base = get_data_dir() / "checkpoints"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{system_id}.db"

def get_logs_dir() -> Path:
    """Get the logs directory path."""
    logs = get_data_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs

# =============================================================================
# VERSION INFORMATION
# =============================================================================

VERSION_INFO = {
    "schema": "2.0.0",  # Blueprint schema version
    "runtime": "1.0.0",  # Runtime version
    "api": "v1",  # API version
}

# Export key configurations
__all__ = [
    "CHECKPOINT_CONFIG",
    "POSTGRES_MIGRATION_TRIGGERS",
    "PII_DENYLIST",
    "PII_MASKING_CONFIG",
    "METRICS_CONFIG",
    "PORT_DEFAULTS",
    "MERGER_CONFIG",
    "VALIDATION_CONFIG",
    "GENERATOR_CONFIG",
    "VERSION_INFO",
    "get_data_dir",
    "get_checkpoint_path",
    "get_logs_dir",
]