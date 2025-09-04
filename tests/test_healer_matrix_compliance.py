import pytest
from autocoder_cc.healing.blueprint_healer import BlueprintHealer

def test_healer_respects_matrix():
    """Healer should never propose invalid connections"""
    healer = BlueprintHealer()
    
    # Test that Controller can't connect to Source (not allowed by matrix)
    result = healer._is_connection_allowed("Controller", "Source")
    assert result is False, "Controller→Source should be disallowed"
    
    # Test that Source can connect to Transformer (allowed by matrix)
    result = healer._is_connection_allowed("Source", "Transformer")
    assert result is True, "Source→Transformer should be allowed"
    
    # Test that Router can connect to Sink (after our fix)
    result = healer._is_connection_allowed("Router", "Sink")
    assert result is True, "Router→Sink should be allowed after fix"
    
    # Test that Source can connect to APIEndpoint (after our fix)
    result = healer._is_connection_allowed("Source", "APIEndpoint")
    assert result is True, "Source→APIEndpoint should be allowed after fix"

def test_healer_prevents_duplicates():
    """Healer shouldn't generate duplicate bindings"""
    healer = BlueprintHealer()
    
    # First check - should be allowed
    result1 = healer._should_create_binding("comp1", "Source", "comp2", "Transformer")
    assert result1 is True, "First binding should be allowed"
    
    # Second check - should be rejected as duplicate
    result2 = healer._should_create_binding("comp1", "Source", "comp2", "Transformer")
    assert result2 is False, "Duplicate binding should be rejected"
    
    # Check that the binding is in generated set
    assert ("comp1", "comp2") in healer.generated_bindings

def test_healer_rejects_invalid_connections():
    """Healer should reject connections not allowed by matrix"""
    healer = BlueprintHealer()
    
    # Controller → Source is not allowed
    result = healer._should_create_binding("ctrl1", "Controller", "src1", "Source")
    assert result is False, "Controller→Source should be rejected"
    
    # Check that it's in rejected set
    assert ("ctrl1", "src1") in healer.rejected_bindings
    
    # Try again - should still be rejected (from cache)
    result = healer._should_create_binding("ctrl1", "Controller", "src1", "Source")
    assert result is False, "Previously rejected binding should stay rejected"

def test_healer_stagnation_detection():
    """Healer should detect when it's making no progress"""
    healer = BlueprintHealer()
    
    # Simulate no operations for multiple attempts
    operations1 = []
    assert healer._is_stagnating(operations1) is False, "First empty attempt shouldn't stagnate"
    
    operations2 = []
    assert healer._is_stagnating(operations2) is True, "Second empty attempt should detect stagnation"
    
    # Reset and test operation loops
    healer2 = BlueprintHealer()
    ops = ["Fixed schema_version", "Added policy"]
    
    assert healer2._is_stagnating(ops) is False, "First operation set shouldn't stagnate"
    # Second identical operation increments stagnation count but doesn't trigger yet
    assert healer2._is_stagnating(ops.copy()) is False, "Second identical operations - first repeat"
    # Third identical operation should trigger stagnation
    assert healer2._is_stagnating(ops.copy()) is True, "Third identical operations should detect stagnation"

def test_healer_generates_valid_bindings():
    """Healer should only generate matrix-compliant bindings"""
    healer = BlueprintHealer()
    
    # Create a blueprint with components but no bindings
    blueprint = {
        "schema_version": "1.0.0",
        "system": {
            "name": "test_system",
            "components": [
                {"name": "source1", "type": "Source"},
                {"name": "transformer1", "type": "Transformer"},
                {"name": "sink1", "type": "Sink"}
            ],
            "bindings": []
        }
    }
    
    # Generate missing bindings
    components = blueprint["system"]["components"]
    existing_bindings = blueprint["system"]["bindings"]
    
    new_bindings = healer._generate_missing_bindings(components, existing_bindings)
    
    # Check that generated bindings are valid
    assert len(new_bindings) > 0, "Should generate some bindings"
    
    # Verify each binding respects the matrix
    for binding in new_bindings:
        from_comp = binding.get("from_component")
        to_comps = binding.get("to_components", [])
        
        # Find component types
        from_type = None
        to_type = None
        
        for comp in components:
            if comp["name"] == from_comp:
                from_type = comp["type"]
            if to_comps and comp["name"] == to_comps[0]:
                to_type = comp["type"]
        
        if from_type and to_type:
            # This binding should be allowed by the matrix
            is_allowed = healer._is_connection_allowed(from_type, to_type)
            assert is_allowed, f"Generated binding {from_type}→{to_type} violates matrix"

def test_healer_respects_max_attempts():
    """Healer should stop after reaching max stagnation count"""
    healer = BlueprintHealer()
    
    # Create a problematic blueprint that would cause stagnation
    blueprint = {
        "schema_version": "1.0.0",
        "system": {
            "name": "test_system",
            "components": [
                {"name": "ctrl1", "type": "Controller"},
                {"name": "src1", "type": "Source"}
            ],
            "bindings": []
        }
    }
    
    # Run healing multiple times
    for i in range(4):
        result = healer.heal_blueprint(blueprint.copy())
        # Check that stagnation counter increases appropriately
        if i >= 2:
            assert healer.stagnation_count >= 2, f"Stagnation should be detected by attempt {i+1}"
    
    # After max attempts, stagnation should be at max
    assert healer.stagnation_count >= 2, "Should reach stagnation limit"