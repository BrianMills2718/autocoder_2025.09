import ast
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

class ComponentAnalyzer:
    """Analyzes generated components to understand their patterns"""
    
    def __init__(self):
        self.logger = None  # Will be set if needed
    
    def analyze_api_endpoint(self, file_path: Path) -> Dict[str, Any]:
        """Analyze an API endpoint component to extract its patterns"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Detect response format (status vs status_code)
        response_field = "status_code" if "status_code" in content else "status"
        
        # Detect API paths more comprehensively
        paths = set()
        # Pattern 1: path == "/something"
        for match in re.finditer(r'path\s*==\s*["\']([^"\']+)["\']', content):
            paths.add(match.group(1))
        # Pattern 2: path.startswith("/something")
        for match in re.finditer(r'path\.startswith\(["\']([^"\']+)["\']', content):
            paths.add(match.group(1))
        # Pattern 3: if "/something" in path
        for match in re.finditer(r'["\']/(todos?|tasks?)[/"]', content):
            paths.add(f"/{match.group(1).rstrip('s')}")
        
        # Detect HTTP method handling
        methods = set()
        for match in re.finditer(r'method\s*==\s*["\'](\w+)["\']', content):
            methods.add(match.group(1))
        for match in re.finditer(r'request_method\s*==\s*["\'](\w+)["\']', content):
            methods.add(match.group(1))
        
        # Detect the actual class name
        class_name = None
        for match in re.finditer(r'class\s+(\w+)\s*\(', content):
            if 'APIEndpoint' in match.group(1):
                class_name = match.group(1)
                break
        
        return {
            "response_field": response_field,
            "paths": list(paths),
            "methods": list(methods),
            "base_path": self._detect_base_path(list(paths)),
            "class_name": class_name
        }
    
    def analyze_store(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Store component to extract its patterns"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Detect supported actions
        actions = set()
        for match in re.finditer(r'action\s*==\s*["\']([^"\']+)["\']', content):
            actions.add(match.group(1))
        
        # Detect class name
        class_name = None
        for match in re.finditer(r'class\s+(\w+)\s*\(', content):
            if 'Store' in match.group(1):
                class_name = match.group(1)
                break
        
        return {
            "actions": list(actions),
            "class_name": class_name
        }
    
    def analyze_controller(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Controller component to extract its patterns"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Detect supported actions
        actions = set()
        for match in re.finditer(r'action\s*==\s*["\']([^"\']+)["\']', content):
            actions.add(match.group(1))
        
        # Check if it uses nested payload
        uses_payload = 'payload' in content
        
        # Detect class name
        class_name = None
        for match in re.finditer(r'class\s+(\w+)\s*\(', content):
            if 'Controller' in match.group(1):
                class_name = match.group(1)
                break
        
        return {
            "actions": list(actions),
            "uses_payload": uses_payload,
            "class_name": class_name
        }
    
    def _detect_base_path(self, paths: List[str]) -> str:
        """Detect the base path from a list of paths"""
        # Look for the most common base path
        for path in paths:
            if path in ["/todos", "/tasks"]:
                return path
        # Check for path patterns
        if any("/todo" in p for p in paths):
            return "/todos"
        if any("/task" in p for p in paths):
            return "/tasks"
        # Default based on component generation patterns
        return "/todos"
    
    def detect_component_class(self, file_path: Path) -> Optional[str]:
        """Detect the actual class name from a component file"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find class definition
        for match in re.finditer(r'class\s+(\w+)\s*\([^)]+\):', content):
            class_name = match.group(1)
            if any(keyword in class_name for keyword in ['Store', 'Controller', 'APIEndpoint', 'Endpoint']):
                return class_name
        
        return None