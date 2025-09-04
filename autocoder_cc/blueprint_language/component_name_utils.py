#!/usr/bin/env python3
"""
Component Name Transformation Utilities

Provides robust conversion between different naming conventions used
in component discovery, validation, and healing processes.
"""

import re
from typing import List, Set


def snake_case_to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase
    
    Examples:
        fraud_detector -> FraudDetector
        api_gateway -> ApiGateway  
        user_store -> UserStore
    """
    if not snake_str:
        return snake_str
        
    # Split on underscores and capitalize each part
    components = snake_str.split('_')
    return ''.join(word.capitalize() for word in components if word)


def pascal_case_to_snake_case(pascal_str: str) -> str:
    """Convert PascalCase to snake_case
    
    Examples:
        FraudDetector -> fraud_detector
        APIGateway -> api_gateway
        UserStore -> user_store
    """
    if not pascal_str:
        return pascal_str
    
    # Insert underscore before uppercase letters (except the first one)
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', pascal_str)
    snake_str = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str)
    return snake_str.lower()


def generate_class_name_variants(component_name: str) -> List[str]:
    """Generate all possible class name variants for a component name
    
    This handles various naming patterns that might be used:
    - Direct name (fraud_detector)
    - PascalCase (FraudDetector) 
    - With component suffix (FraudDetectorComponent)
    - Capitalized snake_case (Fraud_Detector)
    
    Args:
        component_name: The component name from blueprint (usually snake_case)
        
    Returns:
        List of possible class names to search for
    """
    variants = set()
    
    # Add the original name
    variants.add(component_name)
    
    # Convert to PascalCase
    pascal_name = snake_case_to_pascal_case(component_name)
    variants.add(pascal_name)
    
    # Add component suffix variants
    variants.add(f"{pascal_name}Component")
    variants.add(f"{component_name}_component")
    variants.add(f"{component_name}Component")
    
    # Add capitalized first letter variant
    if component_name:
        variants.add(component_name.capitalize())
    
    # Handle special cases for common patterns
    if '_' in component_name:
        # Try replacing underscores with nothing (compact form)
        compact = component_name.replace('_', '')
        variants.add(compact)
        variants.add(compact.capitalize())
        
        # Try capitalizing each word but keeping underscores
        words = component_name.split('_')
        capitalized_words = '_'.join(word.capitalize() for word in words)
        variants.add(capitalized_words)
    
    # Remove empty strings and return as sorted list for consistency
    return sorted([v for v in variants if v])


def find_best_class_name_match(available_classes: Set[str], component_name: str) -> str:
    """Find the best class name match from available classes
    
    Args:
        available_classes: Set of class names found in the file
        component_name: The component name we're looking for
        
    Returns:
        The best matching class name, or the original component_name if no match
    """
    if not available_classes:
        return component_name
    
    # Generate all possible variants
    variants = generate_class_name_variants(component_name)
    
    # Try exact matches first (in order of preference)
    for variant in variants:
        if variant in available_classes:
            return variant
    
    # Try case-insensitive matches
    component_lower = component_name.lower()
    for class_name in available_classes:
        if class_name.lower() == component_lower:
            return class_name
    
    # Try partial matches (class name contains component name or vice versa)
    for class_name in available_classes:
        class_lower = class_name.lower()
        if (component_lower in class_lower or 
            class_lower in component_lower or
            # Check if removing common suffixes matches
            class_lower.replace('component', '') == component_lower or
            component_lower.replace('component', '') == class_lower):
            return class_name
    
    # If no match found, return the most likely PascalCase variant
    return snake_case_to_pascal_case(component_name)


def normalize_component_name_for_file(component_name: str) -> str:
    """Normalize component name for file naming
    
    Args:
        component_name: Component name from blueprint
        
    Returns:
        Normalized name suitable for Python file naming (snake_case)
    """
    # Convert to snake_case if it's not already
    if '_' not in component_name and any(c.isupper() for c in component_name):
        # Looks like PascalCase, convert to snake_case
        return pascal_case_to_snake_case(component_name)
    
    # Ensure lowercase
    return component_name.lower()


# Test cases for validation
if __name__ == "__main__":
    # Test snake_case to PascalCase conversion
    test_cases = [
        ("fraud_detector", "FraudDetector"),
        ("api_gateway", "ApiGateway"),
        ("user_store", "UserStore"),
        ("simple_transformer", "SimpleTransformer"),
        ("http_api_endpoint", "HttpApiEndpoint"),
    ]
    
    print("Testing snake_case to PascalCase conversion:")
    for input_name, expected in test_cases:
        result = snake_case_to_pascal_case(input_name)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_name} -> {result} (expected: {expected})")
    
    print("\nTesting class name variant generation:")
    test_component = "fraud_detector"
    variants = generate_class_name_variants(test_component)
    print(f"  {test_component} variants: {variants}")
    
    print("\nTesting best match finding:")
    available = {"FraudDetector", "UserStore", "ApiGateway"}
    for component in ["fraud_detector", "user_store", "api_gateway"]:
        match = find_best_class_name_match(available, component)
        print(f"  {component} -> {match}")