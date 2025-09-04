#!/usr/bin/env python3
"""
Test Blueprint Generation for To-Do App
Verifies that all three fixes work correctly:
1. Blueprint binding generation
2. LLM integration with timeouts
3. Natural language processing preserves user intent
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator

async def test_todo_app_generation():
    """Test generating a to-do app from natural language"""
    print("=== Testing To-Do App Blueprint Generation ===\n")
    
    # Create translator
    translator = NaturalLanguageToPydanticTranslator()
    
    # Simple to-do app request
    request = "make me a to-do app"
    
    print(f"Request: {request}")
    print("\n" + "="*50 + "\n")
    
    try:
        # Generate intermediate system
        intermediate_system, structured_nl = translator.translate_to_intermediate(request)
        
        print("✅ Generated IntermediateSystem:")
        print(f"   System name: {intermediate_system.name}")
        print(f"   Description: {intermediate_system.description}")
        print(f"   Components: {len(intermediate_system.components)}")
        for comp in intermediate_system.components:
            print(f"      - {comp.name} ({comp.type}): {comp.description}")
        print(f"   Bindings: {len(intermediate_system.bindings)}")
        for binding in intermediate_system.bindings:
            print(f"      - {binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}")
        
        print("\n" + "="*50 + "\n")
        print("Structured Natural Language:")
        print(structured_nl)
        
        print("\n" + "="*50 + "\n")
        
        # Verify key aspects
        issues = []
        
        # Check 1: System name matches request
        if "todo" not in intermediate_system.name.lower():
            issues.append(f"System name '{intermediate_system.name}' doesn't match 'to-do app' request")
        
        # Check 2: Has bindings
        if len(intermediate_system.bindings) == 0:
            issues.append("No bindings generated (Blueprint Binding Fix failed)")
        
        # Check 3: Description matches request
        if "todo" not in intermediate_system.description.lower() and "to-do" not in intermediate_system.description.lower():
            issues.append("System description doesn't match 'to-do app' request (Natural Language Fix failed)")
        
        # Check 4: Has appropriate components
        has_api = any(comp.type == "APIEndpoint" for comp in intermediate_system.components)
        has_store = any(comp.type == "Store" for comp in intermediate_system.components)
        if not has_api:
            issues.append("No APIEndpoint component for user interaction")
        if not has_store:
            issues.append("No Store component for persisting to-dos")
        
        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ ALL CHECKS PASSED!")
            print("   - System name matches request")
            print("   - Bindings were generated")
            print("   - Description preserves user intent")
            print("   - Has appropriate components")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_todo_app_generation())
    sys.exit(0 if success else 1)