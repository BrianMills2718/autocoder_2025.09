"""
Resource Registry - Tracks and manages all system resources
Following Autocoder 3.3: Prevent resource conflicts through central registry
"""

from typing import Dict, Set, Optional

class ResourceRegistry:
    """Tracks and manages all system resources"""
    
    def __init__(self):
        self.allocated_resources: Dict[str, Set[str]] = {
            'ports': set(),
            'databases': set(),
            'files': set(),
            'threads': set()
        }
    
    def allocate(self, resource_type: str, identifier: str) -> bool:
        """Allocate a resource if available"""
        if resource_type not in self.allocated_resources:
            return False
            
        if identifier in self.allocated_resources[resource_type]:
            return False  # Already allocated
            
        self.allocated_resources[resource_type].add(identifier)
        return True
    
    def release(self, resource_type: str, identifier: str) -> bool:
        """Release an allocated resource"""
        if resource_type not in self.allocated_resources:
            return False
            
        if identifier not in self.allocated_resources[resource_type]:
            return False  # Not allocated
            
        self.allocated_resources[resource_type].remove(identifier)
        return True
    
    def is_allocated(self, resource_type: str, identifier: str) -> bool:
        """Check if a resource is allocated"""
        if resource_type not in self.allocated_resources:
            return False
            
        return identifier in self.allocated_resources[resource_type]