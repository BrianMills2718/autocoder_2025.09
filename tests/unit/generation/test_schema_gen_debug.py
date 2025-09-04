#!/usr/bin/env python3
"""Debug script to test schema generation directly"""

import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from autocoder_cc.generation.llm_schema_generator import LLMSchemaGenerator

async def test_schema_generation():
    generator = LLMSchemaGenerator()
    
    # Simple test prompt
    prompt = """
Generate a Pydantic schema for a Todo item with these fields:
- id: string (UUID)
- title: string (required)
- description: string (optional)
- completed: boolean (default False)
- created_at: datetime
"""
    
    try:
        result = generator.generate_schema(
            component_name="todo_store",
            component_type="Store",
            description="A todo storage component",
            configuration={"storage_type": "postgresql"},
            schema_type="request"
        )
        print("SUCCESS! Generated schema:")
        print(result)
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schema_generation())