#!/usr/bin/env python3
"""
Test with the actual LLM output that was failing
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/brian/autocoder4_cc/autocoder_cc')

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_actual_llm_output():
    """Test with actual LLM-generated code that was failing"""
    
    # This is similar to what we saw in the generated code preview
    actual_llm_code = """import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, FastAPI, HTTPException
from autocoder_cc.components.composed_base import ComposedComponent
from anyio import create_task_group

class GeneratedAPIEndpoint_test_api(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.port = config.get("port", 8000)
        self.endpoints = config.get("endpoints", [])
        self.router = APIRouter()
        self.app = FastAPI()
        self.app.include_router(self.router, prefix="")
        
        for endpoint in self.endpoints:
            if endpoint["method"] == "GET":
                self.router.get(endpoint["path"])(self.get_users)

    async def get_users(self):
        try:
            users = [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Doe", "email": "jane@example.com"}
            ]
            return {"users": users, "status": "success"}
        except Exception as e:
            logging.error(f"Failed to get users: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get users")

    async def process_item(self, item: Any) -> Any:
        try:
            async with create_task_group() as tg:
                await tg.start_task(self.start_server)
        except Exception as e:
            logging.error(f"Failed to start server: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to start server")
    
    async def start_server(self):
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
"""

    try:
        generator = LLMComponentGenerator()
        print("🧪 Testing with actual LLM-like output...")
        print(f"Code length: {len(actual_llm_code)}")
        
        result = generator.validate_no_placeholders(actual_llm_code)
        print(f"✅ Validation passed: {result}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_llm_output()