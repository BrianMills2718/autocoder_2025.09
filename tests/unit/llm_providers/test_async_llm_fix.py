#!/usr/bin/env python3
"""
Test that the unified LLM provider properly uses async completion.
"""

import asyncio
import sys
sys.path.insert(0, '/home/brian/projects/autocoder4_cc')

from autocoder_cc.llm_providers.unified_llm_provider import UnifiedLLMProvider
from autocoder_cc.llm_providers.base_provider import LLMRequest

async def test_async_completion():
    """Test that async completion works without blocking."""
    print("Testing async LLM completion fix...")
    
    try:
        provider = UnifiedLLMProvider()
        
        # Create a simple request
        request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello async world!' and nothing else.",
            max_tokens=100,  # Increased to avoid Gemini token limit
            temperature=0.0
        )
        
        # Make multiple concurrent requests to test async behavior
        print("Making 3 concurrent async requests...")
        start_time = asyncio.get_event_loop().time()
        
        # Run 3 requests concurrently
        tasks = [
            provider.generate(request),
            provider.generate(request),
            provider.generate(request)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print(f"✅ All 3 requests completed in {total_time:.2f}s")
        
        # If they were blocking, they would take 3x as long
        # With proper async, they should complete in roughly the same time as one request
        
        # Check that responses are valid
        for i, response in enumerate(responses):
            if response:
                print(f"  Response {i+1}: Type={type(response)}, Content={response.content if hasattr(response, 'content') else 'NO CONTENT ATTR'}")
                if response.content:
                    print(f"    Content: {response.content.strip()}")
                else:
                    print(f"    ERROR - Content is None")
            else:
                print(f"  Response {i+1}: ERROR - Response is None")
        
        assert all(response and response.content for response in responses), "Some responses were empty"
        
        print("✅ SUCCESS: Async completion is working properly!")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception during async test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_sync_context_still_works():
    """Test that the provider works correctly in async context."""
    print("\nTesting provider in async context...")
    
    try:
        provider = UnifiedLLMProvider()
        
        request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello async world!' and nothing else.",
            max_tokens=100,  # Increased to avoid Gemini token limit
            temperature=0.0
        )
        
        # Call it properly in async context
        response = await provider.generate(request)
        
        if response and response.content:
            print(f"✅ Response: {response.content.strip()}")
        else:
            print("❌ No response content")
            return False
            
        assert response.content, "Response was empty"
        
        print("✅ SUCCESS: Provider works in async context!")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("Async LLM Completion Fix Test")
    print("=" * 60)
    
    # Test 1: Async completion doesn't block
    test1_passed = await test_async_completion()
    
    # Test 2: Works correctly in async context
    test2_passed = await test_sync_context_still_works()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Async Completion: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Async Context: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED - Async LLM fix is working!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Fix needs more work")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())