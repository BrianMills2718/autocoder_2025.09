#!/usr/bin/env python3
"""
Valid blueprint fixtures that match the ACTUAL production structure.
All tests should use these fixtures to ensure consistency.
"""

from typing import Dict, Any


def get_nested_blueprint() -> Dict[str, Any]:
    """
    Standard nested blueprint structure as produced by IntermediateToBlueprintTranslator.
    This is the PRODUCTION format.
    """
    return {
        "system": {
            "name": "test_system",
            "description": "Test system for validation",
            "version": "1.0.0",
            "components": [
                {
                    "name": "source",
                    "type": "Source",
                    "description": "Data source",
                    "configuration": {
                        "data_source": "csv",
                        "file_path": "/data/input.csv"
                    },
                    "inputs": [],
                    "outputs": [{"name": "output", "schema": {}}]
                },
                {
                    "name": "transformer",
                    "type": "Transformer",
                    "description": "Data transformer",
                    "configuration": {
                        "transform_type": "filter"
                    },
                    "inputs": [{"name": "input", "schema": {}}],
                    "outputs": [{"name": "output", "schema": {}}]
                },
                {
                    "name": "sink",
                    "type": "Sink",
                    "description": "Data sink",
                    "configuration": {
                        "sink_type": "database"
                    },
                    "inputs": [{"name": "input", "schema": {}}],
                    "outputs": []
                }
            ],
            "connections": [
                {"from": "source.output", "to": "transformer.input"},
                {"from": "transformer.output", "to": "sink.input"}
            ],
            "bindings": [  # Alternative to connections
                {
                    "from": {"component": "source", "port": "output"},
                    "to": {"component": "transformer", "port": "input"}
                },
                {
                    "from": {"component": "transformer", "port": "output"},
                    "to": {"component": "sink", "port": "input"}
                }
            ]
        },
        "schemas": {},
        "metadata": {
            "version": "1.0.0",
            "author": "Test Suite",
            "autocoder_version": "4.3.0"
        },
        "policy": {
            "security": {
                "encryption_at_rest": True,
                "encryption_in_transit": True
            }
        }
    }


def get_minimal_nested_blueprint() -> Dict[str, Any]:
    """Minimal valid nested blueprint"""
    return {
        "system": {
            "name": "minimal_system",
            "components": [
                {
                    "name": "component1",
                    "type": "Source",
                    "configuration": {}
                }
            ]
        }
    }


def get_csv_to_s3_blueprint() -> Dict[str, Any]:
    """Blueprint for CSV to S3 pipeline - common use case"""
    return {
        "system": {
            "name": "csv_to_s3_pipeline",
            "description": "Process CSV files and upload to S3",
            "components": [
                {
                    "name": "csv_file_source",  # The exact name that caused the bug
                    "type": "Source",
                    "configuration": {
                        "data_source": "csv",
                        "directory": "/data/input",
                        "pattern": "*.csv"
                    }
                },
                {
                    "name": "data_filter",
                    "type": "Transformer",
                    "configuration": {
                        "filter_field": "status",
                        "filter_value": "active"
                    }
                },
                {
                    "name": "data_enricher",
                    "type": "Transformer",
                    "configuration": {
                        "enrichment_source": "postgresql",
                        "join_key": "user_id"
                    }
                },
                {
                    "name": "s3_sink",
                    "type": "Sink",
                    "configuration": {
                        "sink_type": "s3",
                        "bucket": "processed-data",
                        "prefix": "enriched/"
                    }
                }
            ],
            "connections": [
                {"from": "csv_file_source.output", "to": "data_filter.input"},
                {"from": "data_filter.output", "to": "data_enricher.input"},
                {"from": "data_enricher.output", "to": "s3_sink.input"}
            ]
        },
        "schemas": {},
        "metadata": {},
        "policy": {}
    }


def get_api_endpoint_blueprint() -> Dict[str, Any]:
    """Blueprint with API endpoint component"""
    return {
        "system": {
            "name": "api_system",
            "components": [
                {
                    "name": "api",
                    "type": "APIEndpoint",
                    "configuration": {
                        "port": 8080,
                        "endpoints": ["/health", "/data"]
                    }
                }
            ]
        },
        "metadata": {},
        "policy": {}
    }


# DEPRECATED - Only for backward compatibility testing
def get_flat_blueprint_legacy() -> Dict[str, Any]:
    """
    LEGACY flat structure - should only be used for backward compatibility tests.
    DO NOT use for new tests.
    """
    return {
        "name": "legacy_system",
        "components": [
            {
                "name": "component1",
                "type": "Source",
                "config": {}
            }
        ],
        "connections": []
    }


# Validation helper
def validate_blueprint_structure(blueprint: Dict[str, Any]) -> bool:
    """Validate that a blueprint has the correct structure"""
    if "system" not in blueprint:
        return False
    
    system = blueprint["system"]
    if "components" not in system:
        return False
    
    if not isinstance(system["components"], list):
        return False
    
    return True


# Test data generators
def create_blueprint_with_n_components(n: int) -> Dict[str, Any]:
    """Create a blueprint with N components for stress testing"""
    components = []
    connections = []
    
    for i in range(n):
        components.append({
            "name": f"component_{i}",
            "type": "Source" if i == 0 else "Transformer" if i < n-1 else "Sink",
            "configuration": {}
        })
        
        if i > 0:
            connections.append({
                "from": f"component_{i-1}.output",
                "to": f"component_{i}.input"
            })
    
    return {
        "system": {
            "name": f"system_with_{n}_components",
            "components": components,
            "connections": connections
        },
        "metadata": {},
        "policy": {}
    }