#!/usr/bin/env python3
"""
Unit tests for boundary semantics engine
Task 3: Boundary Semantics Engine validation
"""

import pytest
from autocoder_cc.blueprint_language.blueprint_parser import (
    BlueprintParser, ParsedPort, ParsedComponent, ParsedBlueprint
)
from autocoder_cc.blueprint_validation.vr1_validator import VR1Validator
from autocoder_cc.blueprint_validation.boundary_semantics import (
    BoundarySemantics, CommitmentType, CommitmentPredicate
)


def create_test_blueprint(blueprint_data):
    """Helper to create test blueprints"""
    parser = BlueprintParser()
    return parser.parse_dict(blueprint_data)


class TestBoundarySemantics:
    """Test basic boundary semantics functionality"""

    def test_boundary_semantics_initialization(self):
        """Test boundary semantics initializes correctly"""
        blueprint_data = {
            "component": {
                "name": "test_component",
                "type": "APIEndpoint",
                "processing_mode": "stream",
                "inputs": [{"name": "request", "schema": "RequestSchema"}],
                "outputs": [{"name": "response", "schema": "ResponseSchema"}]
            },
            "schemas": {
                "RequestSchema": {"type": "object"},
                "ResponseSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        assert semantics.vr1_validator == vr1_validator
        assert semantics.blueprint == blueprint


class TestCommitmentPredicates:
    """Test commitment predicate building"""

    def test_simple_predicate_building(self):
        """Test building simple commitment predicates"""
        blueprint_data = {
            "component": {
                "name": "api",
                "type": "APIEndpoint",
                "processing_mode": "stream",
                "inputs": [{"name": "request", "schema": "RequestSchema", 
                           "boundary_ingress": True, "reply_required": True}],
                "outputs": [{"name": "response", "schema": "ResponseSchema"}]
            },
            "schemas": {
                "RequestSchema": {"type": "object"},
                "ResponseSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        ingress_port = component.inputs[0]
        
        predicate = semantics._build_commitment_predicate(component, ingress_port)
        
        assert predicate.commitment_type == CommitmentType.SIMPLE_REPLY
        assert len(predicate.required_paths) == 1
        assert predicate.required_paths[0]["termination_type"] == "reply_satisfaction"

    def test_monitored_bus_ok_predicate(self):
        """Test monitored_bus_ok allows observability-only termination"""
        blueprint_data = {
            "component": {
                "name": "monitor",
                "type": "Transformer",
                "processing_mode": "stream",
                "monitored_bus_ok": True,
                "inputs": [{"name": "data_in", "schema": "DataSchema", "boundary_ingress": True}],
                "outputs": [{"name": "metrics_out", "schema": "MetricsSchema", "observability_export": True}]
            },
            "schemas": {
                "DataSchema": {"type": "object"},
                "MetricsSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        ingress_port = component.inputs[0]
        
        predicate = semantics._build_commitment_predicate(component, ingress_port)
        
        assert predicate.commitment_type == CommitmentType.CONDITIONAL_OBSERVABILITY
        assert predicate.conditions["monitored_bus_ok"] is True


class TestWebSocketSemantics:
    """Test WebSocket handshake and messaging semantics"""

    def test_websocket_handshake_validation(self):
        """Test WebSocket connection handshake commitment predicate"""
        blueprint_data = {
            "component": {
                "name": "ws",
                "type": "WebSocket",
                "processing_mode": "stream",
                "inputs": [
                    {"name": "connection_request", "schema": "ConnectionRequest", 
                     "boundary_ingress": True, "reply_required": True},
                    {"name": "message_in", "schema": "Message", "boundary_ingress": True}
                ],
                "outputs": [
                    {"name": "connection_status", "schema": "ConnectionStatus", "satisfies_reply": True},
                    {"name": "message_out", "schema": "Message", "observability_export": True}
                ],
                "monitored_bus_ok": True
            },
            "schemas": {
                "ConnectionRequest": {"type": "object"},
                "ConnectionStatus": {"type": "object"},
                "Message": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        results = semantics.validate_advanced_commitments()
        
        # Should have results for both ingress points
        assert len(results) == 2
        
        # Find connection handshake result
        connection_result = next(r for r in results if "connection_request" in r.ingress_point)
        assert connection_result.termination_found is True
        assert connection_result.termination_details["commitment_type"] == "compound_handshake"
        
        # Find message handling result
        message_result = next(r for r in results if "message_in" in r.ingress_point)
        assert message_result.termination_found is True
        assert message_result.termination_details["commitment_type"] == "conditional_observability"

    def test_websocket_predicate_building(self):
        """Test WebSocket commitment predicate building"""
        blueprint_data = {
            "component": {
                "name": "ws",
                "type": "WebSocket",
                "processing_mode": "stream",
                "inputs": [
                    {"name": "connection_request", "schema": "ConnectionRequest"},
                    {"name": "message_in", "schema": "Message"}
                ],
                "outputs": [
                    {"name": "connection_status", "schema": "ConnectionStatus"},
                    {"name": "message_out", "schema": "Message"}
                ]
            },
            "schemas": {
                "ConnectionRequest": {"type": "object"},
                "ConnectionStatus": {"type": "object"},
                "Message": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        
        # Test connection request predicate
        connection_port = component.inputs[0]
        connection_predicate = semantics._build_websocket_predicate(component, connection_port)
        
        assert connection_predicate.commitment_type == CommitmentType.COMPOUND_HANDSHAKE
        assert connection_predicate.conditions["websocket_handshake"] is True
        
        # Test message handling predicate
        message_port = component.inputs[1]
        message_predicate = semantics._build_websocket_predicate(component, message_port)
        
        assert message_predicate.commitment_type == CommitmentType.CONDITIONAL_OBSERVABILITY
        assert message_predicate.conditions["websocket_messaging"] is True


class TestGRPCSemantics:
    """Test gRPC unary and streaming patterns"""

    def test_grpc_unary_patterns(self):
        """Test gRPC unary request/response validation"""
        blueprint_data = {
            "component": {
                "name": "grpc",
                "type": "gRPCEndpoint",
                "processing_mode": "stream",
                "inputs": [{"name": "unary_request", "schema": "UnaryRequest", 
                           "boundary_ingress": True, "reply_required": True}],
                "outputs": [{"name": "unary_response", "schema": "UnaryResponse", 
                            "satisfies_reply": True}]
            },
            "schemas": {
                "UnaryRequest": {"type": "object"},
                "UnaryResponse": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        unary_port = component.inputs[0]
        
        predicate = semantics._build_grpc_predicate(component, unary_port)
        
        assert predicate.commitment_type == CommitmentType.SIMPLE_REPLY
        assert predicate.required_paths[0]["termination_type"] == "reply_satisfaction"

    def test_grpc_streaming_patterns(self):
        """Test gRPC streaming validation with multiple termination options"""
        blueprint_data = {
            "component": {
                "name": "grpc",
                "type": "gRPCEndpoint",
                "processing_mode": "stream",
                "inputs": [{"name": "stream_request", "schema": "StreamRequest", 
                           "boundary_ingress": True}],
                "outputs": [
                    {"name": "stream_response", "schema": "StreamResponse", "satisfies_reply": True},
                    {"name": "stream_status", "schema": "StreamStatus", "observability_export": True}
                ]
            },
            "schemas": {
                "StreamRequest": {"type": "object"},
                "StreamResponse": {"type": "object"},
                "StreamStatus": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        stream_port = component.inputs[0]
        
        predicate = semantics._build_grpc_predicate(component, stream_port)
        
        assert predicate.commitment_type == CommitmentType.COMPOUND_STREAMING
        assert predicate.conditions["grpc_streaming"] is True


class TestObservabilityOnlyTermination:
    """Test observability-only termination patterns"""

    def test_monitored_bus_ok_observability(self):
        """Test monitored_bus_ok allows observability-only termination"""
        blueprint_data = {
            "component": {
                "name": "monitor",
                "type": "Transformer", 
                "processing_mode": "stream",
                "monitored_bus_ok": True,
                "inputs": [{"name": "data_in", "schema": "DataSchema", "boundary_ingress": True}],
                "outputs": [{"name": "metrics_out", "schema": "MetricsSchema", "observability_export": True}]
            },
            "schemas": {
                "DataSchema": {"type": "object"},
                "MetricsSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        results = semantics.validate_advanced_commitments()
        result = results[0]
        
        assert result.termination_found is True
        assert result.termination_details["commitment_type"] == "conditional_observability"
        assert result.termination_details["conditions"]["monitored_bus_ok"] is True

    def test_observability_predicate_building(self):
        """Test observability predicate building"""
        blueprint_data = {
            "component": {
                "name": "monitor",
                "type": "Transformer",
                "processing_mode": "stream",
                "monitored_bus_ok": True,
                "inputs": [{"name": "data", "schema": "DataSchema"}],
                "outputs": [{"name": "metrics", "schema": "MetricsSchema"}]
            },
            "schemas": {
                "DataSchema": {"type": "object"},
                "MetricsSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        component = blueprint.component
        data_port = component.inputs[0]
        
        predicate = semantics._build_observability_predicate(component, data_port)
        
        assert predicate.commitment_type == CommitmentType.CONDITIONAL_OBSERVABILITY
        assert predicate.conditions["monitored_bus_ok"] is True
        assert predicate.required_paths[0]["allow_observability_only"] is True


class TestAdvancedValidationLogic:
    """Test complex validation logic for compound predicates"""

    def test_reply_satisfaction_or_observability_validation(self):
        """Test either reply satisfaction or observability termination"""
        blueprint_data = {
            "component": {
                "name": "flexible",
                "type": "Transformer",
                "processing_mode": "stream",
                "monitored_bus_ok": True,
                "inputs": [{"name": "input", "schema": "InputSchema", "boundary_ingress": True}],
                "outputs": [
                    {"name": "output", "schema": "OutputSchema", "satisfies_reply": False},
                    {"name": "metrics", "schema": "MetricsSchema", "observability_export": True}
                ]
            },
            "schemas": {
                "InputSchema": {"type": "object"},
                "OutputSchema": {"type": "object"},
                "MetricsSchema": {"type": "object"}
            }
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        # Test the path validation logic
        path_spec = {
            "from_port": "input",
            "termination_type": "reply_satisfaction_or_observability",
            "alternatives": ["output", "observability_export"]
        }
        conditions = {"monitored_bus_ok": True}
        
        path_satisfied, path_details = semantics._validate_required_path(
            "flexible", "input", path_spec, conditions
        )
        
        # Should succeed due to observability export even though reply satisfaction fails
        assert path_satisfied is True
        assert "observability" in path_details.get("termination_type", "")

    def test_monitoring_allowance_check(self):
        """Test monitoring allowance detection"""
        # Component with monitored_bus_ok=True
        component_with_monitoring = ParsedComponent(
            name="monitor", 
            type="Transformer",
            monitored_bus_ok=True
        )
        
        # Component with monitored_bus_ok=False
        component_without_monitoring = ParsedComponent(
            name="normal",
            type="Transformer",
            monitored_bus_ok=False
        )
        
        blueprint_data = {
            "component": {
                "name": "dummy",
                "type": "Transformer",
                "processing_mode": "batch",
                "inputs": [{"name": "input", "schema": "Schema"}],
                "outputs": [{"name": "output", "schema": "Schema"}]
            },
            "schemas": {"Schema": {"type": "object"}}
        }
        
        blueprint = create_test_blueprint(blueprint_data)
        vr1_validator = VR1Validator(blueprint)
        semantics = BoundarySemantics(vr1_validator)
        
        assert semantics._has_monitored_bus_allowance(component_with_monitoring) is True
        assert semantics._has_monitored_bus_allowance(component_without_monitoring) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])