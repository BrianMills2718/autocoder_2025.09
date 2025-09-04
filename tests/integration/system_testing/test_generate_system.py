#!/usr/bin/env python3
"""Test script to run generate_deployed_system and examine output."""
import os
import sys
import logging
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autocoder_cc.blueprint_language.natural_language_to_blueprint import generate_system_from_description

# Configure logging to capture all logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('system_generation.log')
    ]
)

def test_system_generation():
    """Test generating a simple todo system."""
    print("=" * 80)
    print("TESTING SYSTEM GENERATION")
    print("=" * 80)
    
    # Simple todo app description
    description = """
    Create a simple todo application with the following features:
    - RESTful API endpoint to create, read, update, and delete todos
    - Store component to persist todos in a database
    - Each todo should have: id, title, description, completed status, and timestamps
    - The API should validate input and return appropriate HTTP status codes
    """
    
    output_dir = "./test_generated_todo_system"
    
    # Clean up any existing output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    try:
        print(f"\n📋 System Description:\n{description}")
        print(f"\n📁 Output Directory: {output_dir}")
        print("\n🚀 Starting system generation...\n")
        
        # Run the generation
        result = generate_system_from_description(description, output_dir)
        
        print(f"\n✅ Generation completed!")
        print(f"📍 Result: {result}")
        
        # List generated files
        print("\n📂 Generated Files:")
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
                
        # Read and display key files
        print("\n📄 Key Generated Files Content:")
        
        # Check for blueprint.yaml
        blueprint_path = Path(output_dir) / "blueprint.yaml"
        if blueprint_path.exists():
            print(f"\n--- blueprint.yaml ---")
            with open(blueprint_path, 'r') as f:
                content = f.read()
                print(content[:1000] + "..." if len(content) > 1000 else content)
        
        # Check for main component files
        components_dir = Path(output_dir) / "components"
        if components_dir.exists():
            for comp_file in components_dir.glob("*.py"):
                print(f"\n--- {comp_file.name} ---")
                with open(comp_file, 'r') as f:
                    content = f.read()
                    print(content[:500] + "..." if len(content) > 500 else content)
                    
        # Check logs
        print("\n📋 Generation Logs:")
        if os.path.exists('system_generation.log'):
            with open('system_generation.log', 'r') as f:
                logs = f.read()
                print(logs[-2000:] if len(logs) > 2000 else logs)
                
    except Exception as e:
        print(f"\n❌ ERROR during generation: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Check logs for more details
        print("\n📋 Error Logs:")
        if os.path.exists('system_generation.log'):
            with open('system_generation.log', 'r') as f:
                logs = f.read()
                print(logs[-3000:] if len(logs) > 3000 else logs)

if __name__ == "__main__":
    test_system_generation()