#!/usr/bin/env python3
"""
Test just the validation method to isolate the AST parsing issue
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from autocoder_cc.blueprint_language.llm_component_generator import LLMComponentGenerator

def test_validation_only():
    """Test just the validation method with known good code"""
    
    # Sample valid Python code
    test_code = """import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, FastAPI, HTTPException
from autocoder_cc.components.composed_base import ComposedComponent

class GeneratedAPIEndpoint_test_api(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.router = APIRouter()
        self.app = FastAPI()
        self.port = config.get("port", 8000)
        self.endpoints = config.get("endpoints", [])

    async def process_item(self, item: Any) -> Any:
        return {"message": "test"}
"""

    try:
        generator = LLMComponentGenerator()
        print("🧪 Testing validation method directly...")
        
        result = generator.validate_no_placeholders(test_code)
        print(f"✅ Validation passed: {result}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation_only()