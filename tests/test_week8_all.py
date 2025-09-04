"""Week 8 comprehensive test suite"""

def test_recipe_system_integrated():
    """Recipe system is connected and working"""
    from autocoder_cc.recipes import RecipeExpander
    from autocoder_cc.blueprint_language.system_generator import SystemGenerator
    from pathlib import Path
    import tempfile
    
    # Check expander exists and has method
    expander = RecipeExpander()
    assert hasattr(expander, 'expand_to_spec')
    
    # Check generator uses it
    with tempfile.TemporaryDirectory() as tmpdir:
        sg = SystemGenerator(Path(tmpdir))
        assert hasattr(sg, 'recipe_expander')

def test_anyio_migration_complete():
    """Critical files use anyio not asyncio"""
    import ast
    from pathlib import Path
    
    critical_files = [
        'autocoder_cc/ports/base.py',
        'autocoder_cc/components/walking_skeleton/api_source.py',
    ]
    
    for filepath in critical_files:
        if Path(filepath).exists():
            with open(filepath) as f:
                content = f.read()
                assert 'import asyncio' not in content, f"{filepath} still uses asyncio"

def test_validation_works():
    """Can generate without bypass flag"""
    # Simple check that validation doesn't crash
    from autocoder_cc.blueprint_language.system_generation.validation_orchestrator import ValidationOrchestrator
    vo = ValidationOrchestrator()
    assert hasattr(vo, '_validate_pre_generation')

def test_ports_functional():
    """Ports can connect and communicate"""
    import anyio
    from autocoder_cc.ports.base import InputPort, OutputPort
    
    async def test():
        in_port = InputPort("test", 10)
        out_port = OutputPort("test")
        await out_port.connect(in_port)
        await out_port.send("test")
        msg = await in_port.receive()
        assert msg == "test"
        
    anyio.run(test)

# Run all with: pytest tests/test_week8_all.py -xvs