#!/usr/bin/env python3
import re

# Test the current pattern
pattern = r'config\.get\s*\(\s*["\']([^"\']*(?:password|secret|token|api_key|credential|private_key|auth_key)[^"\']*)["\'],\s*["\'][^"\']+["\']\s*\)'

# Test cases
test_cases = [
    'self.transform_key = self.config.get("transform_key", "data_value")',
    'self.api_key = self.config.get("api_key", "default")',
    'self.data_key = self.config.get("data_key", "value")',
    'self.password = self.config.get("password", "default")',
    'self.private_key = self.config.get("private_key", "default")',
    'self.my_key = self.config.get("my_key", "value")'
]

print("Testing current pattern:")
print(f"Pattern: {pattern}")
print()

for test in test_cases:
    matches = re.findall(pattern, test, re.IGNORECASE)
    print(f'Test: {test}')
    print(f'Matches: {matches}')
    print()

# Now let's see if "key" is matching anywhere
print("\nChecking if 'key' alone matches:")
simple_key_pattern = r'config\.get\s*\(\s*["\']([^"\']*key[^"\']*)["\'],\s*["\'][^"\']+["\']\s*\)'
for test in test_cases:
    matches = re.findall(simple_key_pattern, test, re.IGNORECASE)
    if matches:
        print(f'Test: {test}')
        print(f'Matches with simple key: {matches}')