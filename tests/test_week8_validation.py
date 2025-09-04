def test_can_generate_without_bypass():
    """Test generation without --bypass-validation flag"""
    import tempfile
    from pathlib import Path
    from autocoder_cc.blueprint_language.natural_language_to_blueprint import generate_system_from_description
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # This is the key test - validation should work
        result = generate_system_from_description(
            "Simple test system",
            output_dir=tmpdir,
            bypass_validation=False,  # NOT bypassing
            skip_deployment=True
        )
        assert result is not None, "Generation failed without bypass"
        assert Path(result).exists(), "Output directory not created"

def test_validation_orchestrator_complete():
    """Test ValidationOrchestrator has all methods"""
    from autocoder_cc.blueprint_language.system_generation.validation_orchestrator import ValidationOrchestrator
    
    vo = ValidationOrchestrator()
    assert hasattr(vo, '_validate_pre_generation'), "Missing _validate_pre_generation"
    assert hasattr(vo, 'validate_component'), "Missing validate_component"
    assert hasattr(vo, 'validate_system'), "Missing validate_system"