"""
Schema Utilities - Shared schema compatibility logic
"""


def are_schemas_compatible(from_schema: str, to_schema: str) -> bool:
    """
    Check if two schemas are compatible for binding connections.
    
    Extracted from SystemGenerator._are_schemas_compatible method.
    Shared utility to prevent duplication across modules.
    Updated to support "any" type and schema healing compatibility.
    """
    # Exact match is always compatible
    if from_schema == to_schema:
        return True
    
    # "any" type accepts anything - universal compatibility
    if to_schema == "any":
        return True
    
    # Compatible conversions based on AutoCoder architecture
    compatible_pairs = [
        ('common_string_schema', 'common_object_schema'),  # string can be wrapped in object
        ('string', 'object'),  # string can be wrapped in object  
        ('array', 'object'),   # array can be wrapped in object
        ('object', 'array'),   # object can be placed in array
        ('number', 'object'),  # number can be wrapped in object
        ('integer', 'number'), # integer is a number
        ('boolean', 'object'), # boolean can be wrapped in object
        ('common_number_schema', 'common_object_schema'),  # number to object
        ('common_boolean_schema', 'common_object_schema'), # boolean to object
        ('common_array_schema', 'common_object_schema'),   # array to object
        # Support for any type compatibility (for healing)
        ('common_object_schema', 'any'),
        ('common_integer_schema', 'any'),
        ('common_string_schema', 'any'),
        ('common_boolean_schema', 'any'),
        ('common_array_schema', 'any'),
        ('common_number_schema', 'any'),
        ('object', 'any'),
        ('integer', 'any'),
        ('string', 'any'),
        ('boolean', 'any'),
        ('array', 'any'),
        ('number', 'any'),
    ]
    
    return (from_schema, to_schema) in compatible_pairs