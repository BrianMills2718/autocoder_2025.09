#!/usr/bin/env python3
"""
Test script for Gemini structured output with component generation
"""
import asyncio
import json
from autocoder_cc.llm_providers.unified_llm_provider import UnifiedLLMProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest
from autocoder_cc.llm_providers.structured_outputs import GeneratedComponent, ComponentType
from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator


async def test_direct_structured_output():
    """Test Gemini structured output directly"""
    print("=== Testing Direct Gemini Structured Output ===\n")
    
    # Initialize provider
    provider = UnifiedLLMProvider({})
    
    # Create structured request
    system_prompt = """You are an expert Python developer. Generate ONLY a JSON response that matches the provided schema.
    Do not include any explanations, code blocks, or markdown. Return only valid JSON."""
    
    user_prompt = """Generate a JSON object for a Transformer component with these properties:
    - component_type: "TRANSFORMER"
    - class_name: "KeywordFilterTransformer"
    - base_class: "StandaloneComponentBase"
    - docstring: "Filters messages based on configured keywords"
    - init_attributes: {"keywords": [], "case_sensitive": false, "action": "pass_through"}
    - setup_body: "self.logger.info(f'KeywordFilter {self.name} setup complete')"
    - process_body: Implementation that checks if item contains keywords and filters accordingly
    - helper_methods: A filter_message method that checks if a message contains keywords
    
    The JSON must match the GeneratedComponent schema exactly."""
    
    request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=4096,
        temperature=0.3,
        response_schema=GeneratedComponent  # Use structured output
    )
    
    try:
        response = await provider.generate(request)
        print("✅ Structured output generation succeeded!")
        print(f"Provider: {response.provider}, Model: {response.model}")
        print("\nRaw Response Content:")
        print(repr(response.content))
        print("\nStructured Response:")
        
        # Parse and pretty print the JSON
        try:
            content = response.content
            # Check if wrapped in markdown code block
            if content.startswith("```json") and content.endswith("```"):
                # Extract JSON from markdown
                json_start = content.find("```json") + 7
                json_end = content.rfind("```")
                content = content[json_start:json_end].strip()
                print("📝 Extracted JSON from markdown code block")
            
            data = json.loads(content)
            print(json.dumps(data, indent=2))
            
            # Try to instantiate the Pydantic model
            component = GeneratedComponent(**data)
            print(f"\n✅ Successfully parsed as GeneratedComponent model")
            print(f"Component type: {component.component_type}")
            print(f"Class name: {component.class_name}")
            print(f"Setup body: {component.setup_body}")
            print(f"Helper methods: {len(component.helper_methods) if component.helper_methods else 0}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Content type: {type(response.content)}")
            print(f"Content length: {len(response.content) if response.content else 0}")
            print(f"First 100 chars: {response.content[:100] if response.content else 'N/A'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_component_generator_structured():
    """Test component generation with structured output"""
    print("\n\n=== Testing Component Generator with Structured Output ===\n")
    
    generator = LLMComponentGenerator()
    
    try:
        code = await generator.generate_component_structured(
            component_type="Transformer",
            component_name="KeywordFilter",
            component_description="Filters messages based on configured keywords",
            component_config={
                "keywords": ["error", "warning", "critical"],
                "case_sensitive": False,
                "action": "pass_through"  # or "block"
            },
            class_name="GeneratedTransformer_KeywordFilter",
            inputs=[{"name": "message_in", "type": "str"}],
            outputs=[{"name": "message_out", "type": "str"}],
            system_context="This is part of a logging pipeline that needs to filter messages"
        )
        
        print("✅ Component generation with structured output succeeded!")
        print("\nGenerated Code:")
        print("=" * 80)
        print(code)
        print("=" * 80)
        
        # Try to compile the code
        compile(code, "generated_component.py", "exec")
        print("\n✅ Generated code compiles successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_fallback_behavior():
    """Test that fallback to regular generation works"""
    print("\n\n=== Testing Fallback Behavior ===\n")
    
    generator = LLMComponentGenerator()
    
    # Force an error by using an invalid component type that won't match enum
    try:
        code = await generator.generate_component_structured(
            component_type="InvalidComponentType",  # This should trigger fallback
            component_name="TestComponent",
            component_description="Test component to trigger fallback",
            component_config={},
            class_name="GeneratedComponent_Test"
        )
        
        print("✅ Fallback to regular generation succeeded!")
        print(f"\nGenerated code length: {len(code)} characters")
        
    except Exception as e:
        print(f"Error during fallback test: {e}")


async def main():
    """Run all tests"""
    print("Starting Gemini Structured Output Tests...\n")
    
    # Test 1: Direct structured output
    await test_direct_structured_output()
    
    # Test 2: Component generator with structured output
    await test_component_generator_structured()
    
    # Test 3: Fallback behavior
    await test_fallback_behavior()
    
    print("\n\n=== All Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())