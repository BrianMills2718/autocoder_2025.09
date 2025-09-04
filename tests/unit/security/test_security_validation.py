#!/usr/bin/env python3

# Test the security validation
from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator

# Create test component code with transform_key
test_code = '''
class DataTransformer:
    def __init__(self, config):
        self.transform_key = self.config.get("transform_key", "data_value")
        self.api_key = self.config.get("api_key", "default")  # This should fail
        self.data_key = self.config.get("data_key", "value")
'''

# Initialize the generator with a temporary directory
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as temp_dir:
    generator = ComponentLogicGenerator(Path(temp_dir))

    # Test security validation
    violations = generator._validate_generated_security(test_code)

    print("Security validation test results:")
    print("-" * 50)
    for violation in violations:
        print(f"❌ {violation}")

    if not any("transform_key" in v for v in violations):
        print("✅ transform_key is NOT flagged as a security violation (GOOD!)")
    else:
        print("❌ transform_key is STILL flagged as a security violation (BAD!)")

    if any("api_key" in v for v in violations):
        print("✅ api_key is correctly flagged as a security violation (GOOD!)")
    else:
        print("❌ api_key is NOT flagged as a security violation (BAD!)")