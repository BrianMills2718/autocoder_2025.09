import pytest
from autocoder_cc.blueprint_language.architectural_validator import ArchitecturalValidator

def test_connectivity_matrix_symmetry():
    """Ensure can_connect_to and can_receive_from are symmetric"""
    validator = ArchitecturalValidator()
    matrix = validator.CONNECTIVITY_MATRIX
    
    errors = []
    for from_type, from_rules in matrix.items():
        for to_type in from_rules.get('can_connect_to', []):
            to_rules = matrix.get(to_type, {})
            can_receive = to_rules.get('can_receive_from', [])
            if from_type not in can_receive:
                errors.append(f"{from_type} → {to_type} valid from {from_type} but {to_type} doesn't accept from {from_type}")
    
    assert not errors, f"Matrix contradictions found:\n" + "\n".join(errors)

def test_sources_have_no_inputs():
    """Sources shouldn't receive from anything"""
    validator = ArchitecturalValidator()
    
    # Check all source types
    source_types = ['Source', 'EventSource']
    for source_type in source_types:
        source_rules = validator.CONNECTIVITY_MATRIX.get(source_type, {})
        assert len(source_rules.get('can_receive_from', [])) == 0, f"{source_type} should not receive inputs"

def test_sinks_are_terminal():
    """Sinks shouldn't connect to anything"""
    validator = ArchitecturalValidator()
    sink_rules = validator.CONNECTIVITY_MATRIX.get('Sink', {})
    assert len(sink_rules.get('can_connect_to', [])) == 0, "Sinks should be terminal"

def test_no_self_connections_for_sources():
    """Sources shouldn't connect to themselves"""
    validator = ArchitecturalValidator()
    source_rules = validator.CONNECTIVITY_MATRIX.get('Source', {})
    assert 'Source' not in source_rules.get('can_connect_to', []), "Sources shouldn't connect to other sources"

def test_matrix_completeness():
    """Ensure all referenced component types exist in the matrix"""
    validator = ArchitecturalValidator()
    matrix = validator.CONNECTIVITY_MATRIX
    
    all_referenced_types = set()
    
    # Collect all referenced types
    for from_type, from_rules in matrix.items():
        all_referenced_types.add(from_type)
        all_referenced_types.update(from_rules.get('can_connect_to', []))
        all_referenced_types.update(from_rules.get('can_receive_from', []))
    
    # Check all referenced types have entries
    missing_types = []
    for comp_type in all_referenced_types:
        if comp_type not in matrix:
            missing_types.append(comp_type)
    
    assert not missing_types, f"Referenced types missing from matrix: {missing_types}"

def test_bidirectional_consistency():
    """Check that bidirectional connections are consistent"""
    validator = ArchitecturalValidator()
    matrix = validator.CONNECTIVITY_MATRIX
    
    errors = []
    
    # For components that can both send and receive from each other,
    # ensure consistency (e.g., if A can send to B and B can send to A)
    for from_type, from_rules in matrix.items():
        for to_type in from_rules.get('can_connect_to', []):
            # Check if there's a reverse connection
            to_rules = matrix.get(to_type, {})
            if from_type in to_rules.get('can_connect_to', []):
                # There's a bidirectional possibility, check both are allowed
                if to_type not in from_rules.get('can_receive_from', []):
                    errors.append(f"{from_type} can send to {to_type} and {to_type} can send to {from_type}, but {from_type} doesn't receive from {to_type}")
                if from_type not in to_rules.get('can_receive_from', []):
                    errors.append(f"{to_type} can send to {from_type} and {from_type} can send to {to_type}, but {to_type} doesn't receive from {from_type}")
    
    assert not errors, f"Bidirectional inconsistencies found:\n" + "\n".join(errors)