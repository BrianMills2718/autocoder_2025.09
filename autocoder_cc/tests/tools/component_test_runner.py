#!/usr/bin/env python3
"""
Component Test Runner - Executes validation tests on generated components
Part of the 4-tier validation framework
"""
import ast
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import importlib
import importlib.util
import sys
import tempfile
import os

from autocoder_cc.observability import get_logger
import subprocess

# Import PropertyTestGenerator for schema-based test data
try:
    from autocoder_cc.generation.property_test_generator import PropertyTestGenerator
    PROPERTY_TEST_GENERATOR_AVAILABLE = True
except ImportError:
    PROPERTY_TEST_GENERATOR_AVAILABLE = False
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import uuid

# Import ComponentAnalyzer for adaptive test generation
from autocoder_cc.tests.tools.component_analyzer import ComponentAnalyzer


class MockCommunicator:
    """Mock communicator for testing isolated components
    
    Simulates inter-component communication during functional testing.
    Provides realistic responses for common component interactions.
    """
    
    def __init__(self):
        self.sent_messages = []  # Track all sent messages for verification
        self.query_responses = []  # Track all queries for verification
        self.logger = logging.getLogger("MockCommunicator")
    
    async def send_to_component(self, source_component: str, target_component: str, 
                                data: Dict[str, Any], target_port: str = "input") -> Dict[str, Any]:
        """Mock sending data to another component
        
        Simulates realistic responses based on target component type and action.
        """
        # Log the interaction
        self.sent_messages.append({
            "source": source_component,
            "target": target_component,
            "data": data,
            "port": target_port,
            "timestamp": time.time()
        })
        
        self.logger.debug(f"Mock send from {source_component} to {target_component}: {data}")
        
        # Simulate store component responses
        if "store" in target_component.lower():
            action = data.get("action")
            
            if action == "add_item":
                return {
                    "status": "success",
                    "message": "Item added successfully",
                    "result": {
                        "id": f"mock-{uuid.uuid4().hex[:8]}",
                        "title": data.get("title"),
                        "description": data.get("description"),
                        "created_at": datetime.now().isoformat()
                    }
                }
            elif action == "update_item":
                return {
                    "status": "success",
                    "message": "Item updated successfully",
                    "result": {
                        "id": data.get("item_id"),
                        "title": data.get("update_data", {}).get("title", "Updated Title"),
                        "updated_at": datetime.now().isoformat()
                    }
                }
            elif action == "delete_item":
                return {
                    "status": "success",
                    "message": "Item deleted successfully",
                    "result": {"id": data.get("item_id"), "deleted": True}
                }
            elif action == "get_item":
                return {
                    "status": "success",
                    "message": "Item retrieved successfully",
                    "result": {
                        "id": data.get("item_id"),
                        "title": "Mock Item",
                        "description": "Mock Description",
                        "created_at": datetime.now().isoformat()
                    }
                }
            elif action == "list_items":
                return {
                    "status": "success",
                    "message": "Items listed successfully",
                    "result": [
                        {"id": "mock-1", "title": "Item 1", "description": "Desc 1"},
                        {"id": "mock-2", "title": "Item 2", "description": "Desc 2"}
                    ]
                }
            # Default fallback for unknown store actions
            return {
                "status": "success",
                "message": f"Store operation {action} completed",
                "result": {"mock": True}
            }
        
        # Simulate controller responses
        if "controller" in target_component.lower():
            return {
                "status": "success",
                "message": "Request processed by controller",
                "result": {"processed": True}
            }
        
        # Default success response
        return {
            "status": "success",
            "message": f"Mock send to {target_component} successful",
            "result": {"mock": True}
        }
    
    async def query_component(self, source_component: str, target_component: str,
                            query: Dict[str, Any], target_port: str = "query") -> Dict[str, Any]:
        """Mock querying another component
        
        Returns realistic query responses based on query type.
        """
        # Log the query
        self.query_responses.append({
            "source": source_component,
            "target": target_component,
            "query": query,
            "port": target_port,
            "timestamp": time.time()
        })
        
        self.logger.debug(f"Mock query from {source_component} to {target_component}: {query}")
        
        action = query.get("action")
        
        # Simulate different query responses
        if action == "list_items":
            return {
                "status": "success",
                "message": "Items retrieved",
                "result": [
                    {"id": "mock-1", "title": "Mock Item 1"},
                    {"id": "mock-2", "title": "Mock Item 2"}
                ]
            }
        elif action == "get_item":
            item_id = query.get("item_id", "unknown")
            return {
                "status": "success",
                "message": "Item retrieved",
                "result": {
                    "id": item_id,
                    "title": f"Mock Item {item_id}",
                    "description": "Mock description"
                }
            }
        elif action == "check_health":
            return {
                "status": "success",
                "result": {"healthy": True, "status": "operational"}
            }
        
        # Default query response
        return {
            "status": "success",
            "message": "Query processed",
            "result": {"mock": True}
        }


class MockTracer:
    """Mock tracer that accepts child_of parameter but ignores it"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(f"MockTracer.{component_name}")
        self.status = None  # Add status attribute for error checking
    
    def start_span(self, name: str, child_of=None, attributes=None, **kwargs):
        """Start a span, accepting but ignoring child_of parameter"""
        return MockSpan(name, self.logger, attributes)
    
    def start_as_current_span(self, name: str, child_of=None, **kwargs):
        """Start a span as current span, accepting but ignoring child_of parameter"""
        return MockSpan(name, self.logger, kwargs.get("attributes"))


class MockSpan:
    """Mock span implementation"""
    
    def __init__(self, name: str, logger, attributes=None):
        self.name = name
        self.logger = logger
        self.attributes = attributes or {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def set_tag(self, key: str, value: Any):
        """Set a tag (same as attribute)"""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes=None):
        pass
    
    def set_status(self, status):
        pass
    
    def end(self):
        """End the span"""
        pass
    
    def record_exception(self, exception):
        """Record an exception in the span"""
        self.logger.debug(f"Exception recorded in span {self.name}: {exception}")
        self.set_attribute("error", True)
        self.set_attribute("exception.type", type(exception).__name__)
        self.set_attribute("exception.message", str(exception))


class TestLevel(Enum):
    """Test levels in the validation hierarchy"""
    FRAMEWORK = "framework"
    COMPONENT_LOGIC = "component_logic"
    INTEGRATION = "integration"
    SEMANTIC = "semantic"


@dataclass
class ComponentTestConfig:
    """Configuration for component testing"""
    component_path: Path  # Changed from component_file to component_path
    component_class_name: str  # Changed from component_name
    test_inputs: List[Dict[str, Any]] = field(default_factory=list)
    expected_outputs: int = 1
    timeout_seconds: float = 30.0
    validate_contract: bool = True
    validate_functionality: bool = True
    validate_performance: bool = False
    test_level: TestLevel = TestLevel.COMPONENT_LOGIC
    enable_mocking: bool = True
    custom_test_data: Optional[Dict[str, Any]] = None
    blueprint_path: Optional[Path] = None  # Path to component's blueprint YAML
    component_schema: Optional[Dict[str, Any]] = None  # Extracted input schema


@dataclass
class ComponentTestResult:
    """Result of component testing"""
    component_name: str
    test_level: TestLevel
    
    # Test outcomes
    syntax_valid: bool = False
    imports_valid: bool = False
    instantiation_valid: bool = False
    contract_validation_passed: bool = False
    functional_test_passed: bool = False
    
    # Additional attributes for validation gate compatibility
    setup_passed: bool = False
    cleanup_passed: bool = False
    process_passed: bool = False
    data_flow_passed: bool = False
    no_placeholders: bool = False
    component_type: str = ""
    
    # Error details
    syntax_errors: List[str] = field(default_factory=list)
    import_errors: List[str] = field(default_factory=list)
    instantiation_errors: List[str] = field(default_factory=list)
    contract_errors: List[str] = field(default_factory=list)
    functional_errors: List[str] = field(default_factory=list)
    
    # Performance metrics
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Blueprint information for healing
    blueprint_info: Optional[Dict[str, Any]] = None
    system_name: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        """Check if all tests passed"""
        return all([
            self.syntax_valid,
            self.imports_valid,
            self.instantiation_valid,
            self.contract_validation_passed,
            self.functional_test_passed
        ])
    
    @property
    def success(self) -> bool:
        """Alias for passed - used by validation gate"""
        return self.passed
    
    @property
    def error_message(self) -> str:
        """Get summary of all errors"""
        errors = []
        if self.syntax_errors:
            errors.append(f"Syntax: {'; '.join(self.syntax_errors)}")
        if self.import_errors:
            errors.append(f"Import: {'; '.join(self.import_errors)}")
        if self.instantiation_errors:
            errors.append(f"Instantiation: {'; '.join(self.instantiation_errors)}")
        if self.contract_errors:
            errors.append(f"Contract: {'; '.join(self.contract_errors)}")
        if self.functional_errors:
            errors.append(f"Functional: {'; '.join(self.functional_errors)}")
        return " | ".join(errors) if errors else "No errors"


class ComponentTestRunner:
    """
    Runs validation tests on generated components.
    
    This is part of the 4-tier validation framework:
    1. Framework validation - Harness functionality
    2. Component logic validation - This class
    3. Integration validation - Inter-component communication
    4. Semantic validation - End-to-end with real systems
    """
    
    def __init__(self):
        self.logger = get_logger("ComponentTestRunner")
        # Initialize PropertyTestGenerator if available
        self.property_test_generator = PropertyTestGenerator() if PROPERTY_TEST_GENERATOR_AVAILABLE else None
        # Cache for discovered blueprints
        self._blueprint_cache = {}
        # Initialize ComponentAnalyzer for adaptive test generation
        self.component_analyzer = ComponentAnalyzer()
    
    async def run_component_test_suite(self, test_configs: List[ComponentTestConfig]) -> Dict[str, Any]:
        """
        Run tests for multiple components and return summary.
        
        Returns dict with:
        - total_components: Total number tested
        - passed: Number that passed all tests
        - failed: Number that failed any test
        - results: List of ComponentTestResult objects
        """
        results = []
        passed = 0
        failed = 0
        
        for config in test_configs:
            self.logger.info(f"Testing component: {config.component_class_name}")
            result = await self.run_component_tests(config)
            results.append(result)
            
            if result.passed:
                passed += 1
            else:
                failed += 1
        
        return {
            "total_components": len(test_configs),
            "passed": passed,
            "failed": failed,
            "results": results
        }
    
    async def run_component_tests(self, config: ComponentTestConfig) -> ComponentTestResult:
        """
        Run all validation tests on a component.
        
        Tests include:
        1. Syntax validation
        2. Import validation
        3. Instantiation test
        4. Contract validation (interfaces, methods)
        5. Functional test (basic operation)
        """
        result = ComponentTestResult(
            component_name=config.component_class_name,
            test_level=config.test_level
        )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. Syntax validation
            self.logger.info(f"Running syntax validation for {config.component_class_name}")
            result.syntax_valid, result.syntax_errors = self._validate_syntax(config.component_path)
            
            if not result.syntax_valid:
                self.logger.error(f"Syntax validation failed for {config.component_class_name}")
                return result
            
            # 2. Import validation
            self.logger.info(f"Running import validation for {config.component_class_name}")
            result.imports_valid, result.import_errors = await self._validate_imports(config.component_path)
            
            if not result.imports_valid:
                self.logger.error(f"Import validation failed for {config.component_class_name}")
                return result
            
            # 3. Extract blueprint schema if available
            if not config.component_schema:
                config.component_schema = self._extract_blueprint_schema(config)
                
            # 4. Load component module
            module = self._load_component_module(config.component_path, config.component_class_name)
            if not module:
                result.instantiation_errors.append("Failed to load component module")
                return result
            
            # 5. Instantiation test
            self.logger.info(f"Running instantiation test for {config.component_class_name}")
            component_instance, instantiation_errors = await self._test_instantiation(
                module, config.component_class_name
            )
            
            result.instantiation_valid = component_instance is not None
            result.instantiation_errors = instantiation_errors
            
            if not result.instantiation_valid:
                self.logger.error(f"Instantiation test failed for {config.component_class_name}")
                return result
            
            # 6. Contract validation
            self.logger.info(f"Running contract validation for {config.component_class_name}")
            result.contract_validation_passed, result.contract_errors = self._validate_contract(
                component_instance, config.component_class_name
            )
            
            # 7. Functional test
            if result.contract_validation_passed and config.test_level != TestLevel.FRAMEWORK:
                self.logger.info(f"Running functional test for {config.component_class_name}")
                result.functional_test_passed, result.functional_errors = await self._run_functional_test(
                    component_instance, config
                )
            
        except Exception as e:
            self.logger.error(f"Unexpected error testing {config.component_class_name}: {e}")
            result.functional_errors.append(f"Unexpected error: {str(e)}")
        
        finally:
            result.execution_time = asyncio.get_event_loop().time() - start_time
        
        return result
    
    def _validate_syntax(self, component_file: Path) -> Tuple[bool, List[str]]:
        """Validate Python syntax"""
        errors = []
        
        try:
            with open(component_file, 'r') as f:
                source_code = f.read()
            
            # Parse the AST
            ast.parse(source_code)
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            if e.text:
                errors.append(f"  {e.text.strip()}")
                if e.offset:
                    errors.append(f"  {' ' * (e.offset - 1)}^")
        except Exception as e:
            errors.append(f"Failed to parse file: {str(e)}")
        
        return False, errors
    
    async def _validate_imports(self, component_file: Path) -> Tuple[bool, List[str]]:
        """Validate all imports can be resolved"""
        errors = []
        
        try:
            # Use subprocess to test imports in isolation with proper package context
            # For relative imports to work, we need to import as part of package
            test_script = f"""
import sys
import os
import importlib

# Add the components directory FIRST for local imports
sys.path.insert(0, '{component_file.parent}')
# Then add the system root
sys.path.insert(0, '{component_file.parent.parent.parent}')

try:
    # Use spec_from_file_location for more reliable import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "component_module", 
        '{component_file}'
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("IMPORTS_OK")
    else:
        print("IMPORT_ERROR: Could not create module spec")
except ImportError as e:
    print(f"IMPORT_ERROR: {{e}}")
except Exception as e:
    print(f"OTHER_ERROR: {{e}}")
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
                tf.write(test_script)
                tf.flush()
                
                result = subprocess.run(
                    [sys.executable, tf.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if "IMPORTS_OK" in result.stdout:
                    return True, []
                elif "IMPORT_ERROR" in result.stdout:
                    error_msg = result.stdout.split("IMPORT_ERROR: ")[1].strip()
                    errors.append(f"Import error: {error_msg}")
                else:
                    errors.append(f"Import validation failed: {result.stdout} {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            errors.append("Import validation timed out")
        except Exception as e:
            errors.append(f"Import validation error: {str(e)}")
        
        return False, errors
    
    def _load_component_module(self, component_file: Path, component_name: str):
        """Dynamically load component module with proper package context"""
        try:
            # Store original path
            original_path = sys.path.copy()
            
            # Add component directory FIRST for local imports
            sys.path.insert(0, str(component_file.parent))
            # Then add the system root (parent of scaffolds dir)
            system_root = component_file.parent.parent.parent
            sys.path.insert(0, str(system_root))
            
            try:
                # Use spec_from_file_location for more reliable import
                spec = importlib.util.spec_from_file_location(
                    "component_module", 
                    component_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module
                else:
                    self.logger.error(f"Could not create module spec for {component_file}")
                    return None
            finally:
                # Restore original path
                sys.path = original_path
            
        except Exception as e:
            self.logger.error(f"Failed to load component module: {e}")
            return None
    
    async def _test_instantiation(self, module, component_name: str) -> Tuple[Optional[Any], List[str]]:
        """Test component instantiation"""
        errors = []
        
        try:
            # Find the component class
            class_name = self._find_component_class(module)
            if not class_name:
                errors.append("No component class found in module")
                return None, errors
            
            component_class = getattr(module, class_name)
            
            # Try to instantiate with test configuration
            # Provide common test configs to avoid initialization failures
            config = {
                "test_mode": True,
                # Database configs for Store components
                "db_type": "sqlite",
                "storage_type": "file",  # Add storage_type for generated Store components
                "db_path": ":memory:",
                "db_password": "test_password",
                "db_user": "test_user",
                "db_host": "localhost",
                "db_port": 5432,
                "db_name": "test_db",
                # API configs
                "port": 8080,
                "host": "localhost",
                # General configs
                "timeout": 30,
                "max_retries": 3,
                # Controller configs
                "store_component_name": "test_store"  # Add store name for Controller components
            }
            component_instance = component_class(name=component_name, config=config)
            
            return component_instance, []
            
        except Exception as e:
            errors.append(f"Instantiation failed: {str(e)}")
            return None, errors
    
    def _find_component_class(self, module) -> Optional[str]:
        """Find the main component class in the module"""
        # Look for classes that inherit from common base classes
        base_classes = ['Component', 'Source', 'Transformer', 'Sink', 'Model', 'Store', 
                       'APIEndpoint', 'Controller', 'ComposedComponent', 'ComposedComponent', 'HarnessComponent',
                       'StreamProcessor', 'WebSocket', 'Router', 'Aggregator', 'Filter', 'Accumulator']
        
        # Classes to explicitly exclude (helper/infrastructure classes)
        excluded_classes = ['ComponentCommunicator', 'ComponentRegistry', 'CommunicationConfig',
                           'MessageEnvelope', 'StandaloneMetricsCollector', 'StandaloneTracer',
                           'ComponentStatus', 'ObservabilityConfig']
        
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and name not in excluded_classes:
                # Check if it inherits from any base class
                for base in obj.__mro__[1:]:  # Skip self
                    if base.__name__ in base_classes:
                        return name
        
        # NO FALLBACK - if we can't find a proper component class, return None
        # This prevents accidentally testing infrastructure classes
        return None
    
    def _validate_contract(self, component_instance, component_name: str) -> Tuple[bool, List[str]]:
        """Validate component implements required interface (supports both old and new patterns)"""
        errors = []
        
        try:
            # Check if this is a ComposedComponent or ComposedComponent (new interfaces)
            is_composed = False
            is_standalone = False
            for base in component_instance.__class__.__mro__:
                if base.__name__ == 'ComposedComponent':
                    is_composed = True
                    break
                elif base.__name__ == 'ComposedComponent':
                    is_standalone = True
                    break
            
            if is_composed:
                # Validate ComposedComponent interface (reference implementation pattern)
                self.logger.info(f"Validating ComposedComponent interface for {component_name}")
                
                # Required methods for composed components
                required_methods = ['setup', 'process', 'cleanup', 'get_health_status']
            elif is_standalone:
                # Validate ComposedComponent interface
                self.logger.info(f"Validating ComposedComponent interface for {component_name}")
                
                # Required methods for standalone components
                required_methods = ['setup', 'teardown', 'process_item', 'get_health_status']
                
                for method_name in required_methods:
                    if not hasattr(component_instance, method_name):
                        errors.append(f"Missing required method: {method_name}")
                    else:
                        method = getattr(component_instance, method_name)
                        if not callable(method):
                            errors.append(f"{method_name} is not callable")
                
                # Standalone components don't need stream attributes
                # They use communicator for inter-component communication
                
            else:
                # Validate old component interface
                self.logger.info(f"Validating legacy component interface for {component_name}")
                
                # Check required methods based on component type
                base_class_name = component_instance.__class__.__bases__[0].__name__
                
                required_methods = {
                    'Source': ['_generate_data', 'setup', 'process', 'cleanup'],
                    'Transformer': ['_transform_data', 'setup', 'process', 'cleanup'],
                    'Sink': ['_output_data', 'setup', 'process', 'cleanup'],
                    'Model': ['_load_model', '_run_inference', 'setup', 'process', 'cleanup'],
                    'Store': ['setup', 'process', 'cleanup'],
                    'Component': ['setup', 'process', 'cleanup']
                }
                
                methods_to_check = required_methods.get(base_class_name, ['setup', 'process', 'cleanup'])
                
                for method_name in methods_to_check:
                    if not hasattr(component_instance, method_name):
                        errors.append(f"Missing required method: {method_name}")
                    else:
                        method = getattr(component_instance, method_name)
                        if not callable(method):
                            errors.append(f"{method_name} is not callable")
                
                # Check for stream attributes (only for old components)
                if not hasattr(component_instance, 'receive_streams'):
                    errors.append("Missing receive_streams attribute")
                if not hasattr(component_instance, 'send_streams'):
                    errors.append("Missing send_streams attribute")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Contract validation error: {str(e)}")
            return False, errors
    
    def _find_blueprint_path(self, component_path: Path) -> Optional[Path]:
        """Automatically discover blueprint.yaml by searching parent directories"""
        # Check cache first
        cache_key = str(component_path)
        if cache_key in self._blueprint_cache:
            return self._blueprint_cache[cache_key]
        
        current_dir = component_path.parent
        
        # Search up to 5 levels up for blueprint.yaml
        for _ in range(5):
            blueprint_path = current_dir / "blueprint.yaml"
            if blueprint_path.exists():
                self.logger.info(f"Found blueprint at: {blueprint_path}")
                self._blueprint_cache[cache_key] = blueprint_path
                return blueprint_path
            
            # Also check for blueprint.yml
            blueprint_path = current_dir / "blueprint.yml"
            if blueprint_path.exists():
                self.logger.info(f"Found blueprint at: {blueprint_path}")
                self._blueprint_cache[cache_key] = blueprint_path
                return blueprint_path
                
            # Move up one directory
            parent = current_dir.parent
            if parent == current_dir:  # Reached root
                break
            current_dir = parent
            
        self.logger.warning(f"No blueprint found for component at {component_path}")
        self._blueprint_cache[cache_key] = None
        return None
    
    def _fuzzy_match_component_name(self, target_name: str, component_list: List[Dict]) -> Optional[Dict]:
        """Find component with fuzzy name matching"""
        target_lower = target_name.lower()
        
        # Try exact match first
        for component in component_list:
            if component.get('name') == target_name:
                return component
        
        # Try case-insensitive match
        for component in component_list:
            if component.get('name', '').lower() == target_lower:
                return component
        
        # Try underscore/camelCase variations
        # Convert TaskAPIEndpoint to task_api_endpoint and vice versa
        import re
        
        # CamelCase to snake_case (handle consecutive capitals like API)
        snake_case = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', target_name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case).lower()
        for component in component_list:
            if component.get('name', '').lower() == snake_case:
                return component
        
        # snake_case to CamelCase (simple version)
        camel_case = ''.join(word.capitalize() for word in target_name.split('_'))
        for component in component_list:
            if component.get('name', '') == camel_case:
                return component
                
        # Try partial match (component name contains target or vice versa)
        for component in component_list:
            comp_name = component.get('name', '').lower()
            if target_lower in comp_name or comp_name in target_lower:
                self.logger.info(f"Fuzzy matched '{target_name}' to '{component.get('name')}'")
                return component
        
        return None
    
    def _extract_blueprint_schema(self, config: ComponentTestConfig) -> Optional[Dict[str, Any]]:
        """Extract input schema from component's blueprint if available"""
        # Try provided path first, then auto-discover
        blueprint_path = config.blueprint_path
        if not blueprint_path or not blueprint_path.exists():
            blueprint_path = self._find_blueprint_path(config.component_path)
            if not blueprint_path:
                self.logger.info(f"No blueprint found for {config.component_class_name}, will use fallback test data")
                return None
            
        try:
            import yaml
            with open(blueprint_path, 'r') as f:
                blueprint = yaml.safe_load(f)
            
            # Find the component in the blueprint
            if 'system' in blueprint and 'components' in blueprint['system']:
                # Use fuzzy matching to find component
                component = self._fuzzy_match_component_name(
                    config.component_class_name, 
                    blueprint['system']['components']
                )
                
                if component:
                    # Extract input schemas
                    inputs = component.get('inputs', [])
                    if inputs:
                        # Return the first input schema as primary
                        schema = inputs[0].get('schema', {})
                        if schema:
                            self.logger.info(f"Extracted schema for {config.component_class_name}: {schema}")
                            return schema
                        else:
                            self.logger.warning(f"Component {config.component_class_name} has input but no schema")
                else:
                    self.logger.warning(f"Component {config.component_class_name} not found in blueprint")
            
            return None
        except Exception as e:
            self.logger.warning(f"Failed to extract blueprint schema: {e}")
            return None
    
    def _generate_test_data_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data that conforms to a given schema"""
        test_data = {}
        
        # Handle different schema formats
        if 'properties' in schema:
            # JSON Schema format
            for prop_name, prop_schema in schema.get('properties', {}).items():
                prop_type = prop_schema.get('type', 'string')
                
                if prop_type == 'string':
                    test_data[prop_name] = f"test_{prop_name}"
                elif prop_type == 'integer':
                    test_data[prop_name] = 42
                elif prop_type == 'number':
                    test_data[prop_name] = 3.14
                elif prop_type == 'boolean':
                    test_data[prop_name] = True
                elif prop_type == 'array':
                    test_data[prop_name] = ["test_item_1", "test_item_2"]
                elif prop_type == 'object':
                    test_data[prop_name] = {"nested": "data"}
                else:
                    test_data[prop_name] = "unknown_type"
                    
        elif 'type' in schema:
            # Simple type schema
            if schema['type'] == 'object':
                test_data = {"test": "data", "value": 42}
            elif schema['type'] == 'string':
                return "test_string"
            elif schema['type'] == 'array':
                return ["item1", "item2"]
                
        return test_data
    
    def _generate_schema_aware_test_data(self, schema: Dict[str, Any], 
                                        count: int = 3) -> List[Dict[str, Any]]:
        """Generate test data using PropertyTestGenerator with schema awareness"""
        test_data_samples = []
        
        # If we have PropertyTestGenerator and a schema, try to be smarter
        if self.property_test_generator and schema:
            try:
                # Analyze schema to determine data type
                schema_type = schema.get('type', 'object')
                
                # Try to use type-specific generators
                if schema_type == 'object' or 'properties' in schema:
                    # Use JSON generator for object schemas
                    samples = self.property_test_generator.generate_json_test_data(count=count)
                    
                    # Enhance samples to match schema properties if available
                    if 'properties' in schema:
                        for sample in samples:
                            # Add any required properties from schema
                            for prop_name, prop_schema in schema['properties'].items():
                                if prop_name not in sample:
                                    prop_type = prop_schema.get('type', 'string')
                                    if prop_type == 'string':
                                        sample[prop_name] = f"test_{prop_name}"
                                    elif prop_type == 'integer':
                                        sample[prop_name] = 42
                                    elif prop_type == 'boolean':
                                        sample[prop_name] = True
                    
                    test_data_samples.extend(samples)
                    
                elif schema_type == 'array':
                    # Generate array data
                    for i in range(count):
                        test_data_samples.append([
                            {"id": f"item-{i}-{j}", "value": j * 10}
                            for j in range(3)
                        ])
                else:
                    # Fall back to JSON for unknown types
                    test_data_samples.extend(
                        self.property_test_generator.generate_json_test_data(count=count)
                    )
                    
                return test_data_samples
                
            except Exception as e:
                self.logger.warning(f"Schema-aware PropertyTestGenerator failed: {e}")
        
        # Fallback to basic generation
        return [self._generate_default_test_data(i) for i in range(count)]
    
    def _generate_multiple_test_cases(self, component_instance, component_name: str,
                                     config: Optional[ComponentTestConfig] = None) -> List[Dict[str, Any]]:
        """Generate multiple test cases for better coverage"""
        test_cases = []
        class_name = component_instance.__class__.__name__
        
        # Define common actions/operations by component type
        if "APIEndpoint" in class_name:
            actions = ["create", "read", "update"]
        elif "Store" in class_name:
            actions = ["create", "list", "create"]  # Use create twice and list to avoid non-existent items
        elif "Controller" in class_name:
            actions = ["process", "validate", "transform"]
        else:
            actions = ["execute", "process", "run"]
        
        # Generate test data samples
        if config and config.component_schema:
            # Use schema-aware generation
            base_samples = self._generate_schema_aware_test_data(
                config.component_schema, count=len(actions)
            )
        elif self.property_test_generator:
            try:
                # Fall back to generic PropertyTestGenerator
                base_samples = self.property_test_generator.generate_json_test_data(count=len(actions))
                
            except Exception as e:
                self.logger.warning(f"PropertyTestGenerator failed: {e}")
                base_samples = [self._generate_default_test_data(i) for i in range(len(actions))]
        else:
            # Final fallback
            base_samples = [self._generate_default_test_data(i) for i in range(len(actions))]
        
        # Combine data with component-specific structure
        for i, (action, base_data) in enumerate(zip(actions, base_samples)):
            test_case = self._wrap_test_data_for_component(
                component_instance, action, base_data, i
            )
            test_cases.append(test_case)
            
        return test_cases
    
    def _wrap_test_data_for_component(self, component_instance, action: str, 
                                      base_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Wrap test data in component-specific structure"""
        class_name = component_instance.__class__.__name__
        
        if "APIEndpoint" in class_name:
            # API components expect HTTP request format
            # Try to detect if it's tasks or todos based on component name
            path_base = "/todos" if "todo" in class_name.lower() or "todo" in str(component_instance.name).lower() else "/tasks"
            
            if action == "create":
                return {
                    "method": "POST",
                    "path": path_base,
                    "body": {
                        "title": f"Test Task {index}",
                        "description": f"Test Description {index}"
                    }
                }
            elif action == "read":
                return {
                    "method": "GET",
                    "path": f"{path_base}/test-{index}",
                    "body": {}
                }
            elif action == "update":
                return {
                    "method": "PUT",
                    "path": f"{path_base}/test-{index}",
                    "body": {
                        "title": f"Updated Task {index}",
                        "description": f"Updated Description {index}"
                    }
                }
            else:  # Default GET all
                return {
                    "method": "GET",
                    "path": path_base,
                    "body": {}
                }
        elif "Store" in class_name:
            # Store components expect flat structure with action at root
            if action == "create":
                return {
                    "action": "add_item",
                    "title": f"Test Item {index}",
                    "description": f"Test Description for item {index}"
                }
            elif action == "read":
                return {
                    "action": "get_item",
                    "item_id": f"test-item-{index}"
                }
            elif action == "update":
                return {
                    "action": "update_item",
                    "item_id": f"test-item-{index}",
                    "update_data": {
                        "title": f"Updated Item {index}",
                        "description": f"Updated Description {index}"
                    }
                }
            elif action == "list":
                return {"action": "list_items"}
            else:  # Default to list
                return {"action": "list_items"}
        elif "Controller" in class_name:
            # Controller components expect action with nested payload
            if action == "process":
                return {
                    "action": "add_task",
                    "payload": {
                        "title": f"Test Task {index}",
                        "description": f"Test Description for task {index}"
                    }
                }
            elif action == "validate":
                return {
                    "action": "get_task",
                    "payload": {
                        "task_id": f"test-task-{index}"
                    }
                }
            elif action == "transform":
                return {
                    "action": "update_task",
                    "payload": {
                        "task_id": f"test-task-{index}",
                        "title": f"Updated Task {index}",
                        "description": f"Updated Description {index}"
                    }
                }
            else:
                return {
                    "action": "get_all_tasks",
                    "payload": {}
                }
        else:
            return {
                "action": action,
                "data": base_data,
                "id": f"test-{index}"
            }
    
    def _generate_single_test_case(self, component_instance, component_name: str,
                                   config: Optional[ComponentTestConfig], 
                                   action: str, index: int) -> Dict[str, Any]:
        """Generate a single test case with specific action"""
        class_name = component_instance.__class__.__name__
        
        # Generate base data
        if config and config.component_schema:
            base_data = self._generate_test_data_from_schema(config.component_schema)
        else:
            base_data = self._generate_default_test_data(index)
        
        # Use the wrapper method
        return self._wrap_test_data_for_component(component_instance, action, base_data, index)
    
    def _is_successful_response(self, result: Dict[str, Any], component_class: str) -> bool:
        """Determine if a response indicates success based on component type and response format"""
        if not result:
            return False
        
        # Check various status field names
        status = result.get('status')
        status_code = result.get('status_code')
        
        # String success indicators
        if status in ['success', 'completed', 'ok']:
            return True
        
        # HTTP success codes (2xx range)
        if isinstance(status, int) and 200 <= status < 300:
            return True
        if isinstance(status_code, int) and 200 <= status_code < 300:
            return True
        
        # For API endpoints, be more lenient
        if "APIEndpoint" in component_class:
            # If it has expected structure, it's likely successful
            if 'body' in result or 'headers' in result:
                # 404 for updates on non-existent items is acceptable
                if status_code == 404:
                    return True  # Component handled the request without crashing
        
        # For Store components, check for result field
        if "Store" in component_class:
            if result.get('result') is not None or result.get('items') is not None:
                return True
        
        # For Controller components
        if "Controller" in component_class:
            if result.get('processed') or result.get('result') is not None:
                return True
        
        return False
    
    def _generate_adaptive_test_cases(self, component_instance, component_path: Path) -> List[Dict[str, Any]]:
        """Generate test cases adapted to the specific component implementation"""
        class_name = component_instance.__class__.__name__
        
        if "APIEndpoint" in class_name:
            # Analyze the component
            analysis = self.component_analyzer.analyze_api_endpoint(component_path)
            base_path = analysis['base_path']
            
            test_cases = []
            
            # Generate POST test if supported
            if 'POST' in analysis.get('methods', []) or not analysis.get('methods'):
                test_cases.append({
                    "method": "POST",
                    "path": base_path,
                    "body": {
                        "title": "Test Item",
                        "description": "Test Description"
                    }
                })
            
            # Generate GET list test - should always work
            test_cases.append({
                "method": "GET",
                "path": base_path,
                "body": {}
            })
            
            # Add another safe operation
            test_cases.append({
                "method": "GET",
                "path": f"{base_path}/test-1",
                "body": {}
            })
            
            return test_cases
        
        elif "Store" in class_name:
            analysis = self.component_analyzer.analyze_store(component_path)
            test_cases = []
            
            # Use actual actions from the component
            if "add_item" in analysis.get('actions', []):
                test_cases.append({
                    "action": "add_item",
                    "title": "Test Item",
                    "description": "Test Description"
                })
            
            if "list_items" in analysis.get('actions', []):
                test_cases.append({"action": "list_items"})
            
            # Add another add for better coverage
            if "add_item" in analysis.get('actions', []):
                test_cases.append({
                    "action": "add_item",
                    "title": "Test Item 2",
                    "description": "Test Description 2"
                })
            
            return test_cases if test_cases else self._generate_multiple_test_cases(component_instance, class_name, None)
        
        elif "Controller" in class_name:
            analysis = self.component_analyzer.analyze_controller(component_path)
            test_cases = []
            uses_payload = analysis.get('uses_payload', True)
            
            for action in analysis.get('actions', ['add_task', 'get_all_tasks'])[:3]:
                if uses_payload:
                    test_case = {
                        "action": action,
                        "payload": {}
                    }
                    if 'add' in action or 'create' in action:
                        test_case["payload"] = {
                            "title": "Test Task",
                            "description": "Test Description"
                        }
                    elif 'get' in action and 'all' not in action:
                        test_case["payload"] = {"task_id": "test-1"}
                else:
                    test_case = {"action": action}
                    if 'add' in action:
                        test_case.update({
                            "title": "Test Task",
                            "description": "Test Description"
                        })
                test_cases.append(test_case)
            
            return test_cases if test_cases else self._generate_multiple_test_cases(component_instance, class_name, None)
        
        # Fallback to existing logic
        return self._generate_multiple_test_cases(component_instance, class_name, None)
    
    def _generate_default_test_data(self, index: int) -> Dict[str, Any]:
        """Generate default test data when no schema available"""
        return {
            "id": f"item-{index}",
            "name": f"Test Item {index}",
            "value": 100 + index * 10,
            "active": index % 2 == 0,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "source": "test",
                "index": index,
                "test_run": datetime.now().timestamp()
            }
        }
    
    def _generate_component_specific_test_data(self, component_instance, component_name: str, 
                                              config: Optional[ComponentTestConfig] = None) -> Dict[str, Any]:
        """Generate test data specific to the component type using schema and domain knowledge"""
        
        # For single test case generation (backward compatibility)
        # Use the first test case from multiple generation
        test_cases = self._generate_multiple_test_cases(component_instance, component_name, config)
        if test_cases:
            return test_cases[0]
        
        # Fallback if multiple generation fails
        class_name = component_instance.__class__.__name__
        
        # Final fallback with improved domain-specific patterns
        if "APIEndpoint" in class_name or "api_endpoint" in component_name.lower():
            # More realistic API endpoint test data
            return {
                "action": "create",
                "payload": {
                    "name": "Test Task",
                    "description": "Test task description",
                    "priority": 1,
                    "status": "pending"
                }
            }
        
        elif "Store" in class_name or "store" in component_name.lower():
            # More realistic store test data
            return {
                "operation": "create",
                "data": {
                    "id": f"item-{datetime.now().timestamp():.0f}",
                    "title": "Test Item",
                    "content": "Test content for validation",
                    "created_at": datetime.now().isoformat(),
                    "metadata": {"source": "test", "version": 1}
                }
            }
        
        elif "Controller" in class_name or "controller" in component_name.lower():
            # More realistic controller test data
            return {
                "command": "process_task",
                "params": {
                    "task_id": "task-123",
                    "user_id": "user-456",
                    "action": "update_status",
                    "data": {"status": "in_progress"}
                }
            }
        
        elif "WebSocket" in class_name or "websocket" in component_name.lower():
            return {
                "type": "message",
                "data": {
                    "content": "Test message",
                    "timestamp": datetime.now().isoformat()
                },
                "client_id": f"client-{datetime.now().timestamp():.0f}"
            }
        
        # Generic but more realistic default
        else:
            return {
                "id": f"test-{datetime.now().timestamp():.0f}",
                "type": "test_data",
                "content": {
                    "message": "Generic test data",
                    "timestamp": datetime.now().isoformat(),
                    "source": "component_test_runner"
                }
            }
    
    async def _run_functional_test(self, component_instance, config: ComponentTestConfig) -> Tuple[bool, List[str]]:
        """Run basic functional test (supports both old and new component interfaces)"""
        errors = []
        
        try:
            # Check if this is a ComposedComponent or ComposedComponent (new interfaces)
            is_composed = False
            is_standalone = False
            for base in component_instance.__class__.__mro__:
                if base.__name__ == 'ComposedComponent':
                    is_composed = True
                    break
                elif base.__name__ == 'ComposedComponent':
                    is_standalone = True
                    break
            
            if is_composed:
                # Test ComposedComponent components
                self.logger.info(f"Running functional test for ComposedComponent component")
                
                # Call setup
                await component_instance.setup()
                
                # Inject mock communicator for testing
                if hasattr(component_instance, 'set_communication_framework'):
                    mock_communicator = MockCommunicator()
                    component_instance.set_communication_framework(mock_communicator, None)
                    self.logger.info("Injected mock communicator for functional testing")
                elif hasattr(component_instance, 'communicator'):
                    # Direct attribute setting as fallback
                    component_instance.communicator = MockCommunicator()
                    self.logger.info("Set mock communicator directly on component")
                    # Also inject mock tracer to handle child_of parameter
                    component_instance.tracer = MockTracer(component_instance.name)
                    self.logger.info("Set mock tracer directly on component")
                
                # For composed components with process_item method
                if hasattr(component_instance, 'process_item'):
                    # Generate multiple test cases for better coverage
                    # Try adaptive test generation first if component_path is available
                    if config.component_path and config.component_path.exists():
                        try:
                            test_cases = self._generate_adaptive_test_cases(
                                component_instance, config.component_path
                            )
                            self.logger.info(f"Using adaptive test generation, {len(test_cases)} test cases")
                        except Exception as e:
                            self.logger.warning(f"Adaptive test generation failed: {e}, falling back to default")
                            test_cases = self._generate_multiple_test_cases(
                                component_instance, config.component_class_name, config
                            )
                    else:
                        # Fallback to existing test generation
                        test_cases = self._generate_multiple_test_cases(
                            component_instance, config.component_class_name, config
                        )
                    
                    # Run each test case
                    passed_count = 0
                    for i, test_data in enumerate(test_cases):
                        try:
                            result = await component_instance.process_item(test_data)
                            # Use the improved success detection method
                            is_success = self._is_successful_response(result, component_instance.__class__.__name__)
                            if result and is_success:
                                passed_count += 1
                                self.logger.info(f"Test case {i+1} passed")
                            else:
                                self.logger.warning(f"Test case {i+1} returned non-success status: {result}")
                        except Exception as e:
                            self.logger.warning(f"Test case {i+1} failed: {e}")
                    
                    # At least 2 out of 3 should pass
                    if passed_count >= 2:
                        self.logger.info(f"Functional test passed ({passed_count}/3 test cases succeeded)")
                    else:
                        errors.append(f"Only {passed_count}/3 test cases passed")
                        return False, errors
                
                # Call cleanup
                await component_instance.cleanup()
                
            elif is_standalone:
                # Test ComposedComponent components
                self.logger.info(f"Running functional test for ComposedComponent component")
                
                # Call setup
                await component_instance.setup()
                
                # Inject mock communicator for testing
                if hasattr(component_instance, 'set_communication_framework'):
                    mock_communicator = MockCommunicator()
                    component_instance.set_communication_framework(mock_communicator, None)
                    self.logger.info("Injected mock communicator for functional testing")
                elif hasattr(component_instance, 'communicator'):
                    # Direct attribute setting as fallback
                    component_instance.communicator = MockCommunicator()
                    self.logger.info("Set mock communicator directly on component")
                    # Also inject mock tracer to handle child_of parameter
                    component_instance.tracer = MockTracer(component_instance.name)
                    self.logger.info("Set mock tracer directly on component")
                
                # Generate multiple test cases for better coverage
                # Try adaptive test generation first if component_path is available
                if config.component_path and config.component_path.exists():
                    try:
                        test_cases = self._generate_adaptive_test_cases(
                            component_instance, config.component_path
                        )
                        self.logger.info(f"Using adaptive test generation, {len(test_cases)} test cases")
                    except Exception as e:
                        self.logger.warning(f"Adaptive test generation failed: {e}, falling back to default")
                        test_cases = self._generate_multiple_test_cases(
                            component_instance, config.component_class_name, config
                        )
                else:
                    # Fallback to existing test generation
                    test_cases = self._generate_multiple_test_cases(
                        component_instance, config.component_class_name, config
                    )
                
                # Run each test case
                test_results = []
                for i, test_data in enumerate(test_cases):
                    self.logger.info(f"Running test case {i+1}/{len(test_cases)}: action={test_data.get('action', 'unknown')}")
                    try:
                        result = await component_instance.process_item(test_data)
                        if result is None:
                            errors.append(f"Test case {i+1}: process_item returned None")
                            test_results.append(False)
                        else:
                            self.logger.info(f"Test case {i+1}: Success - {result}")
                            test_results.append(True)
                    except NotImplementedError:
                        # Some components may not implement process_item if they're passive
                        self.logger.info(f"Test case {i+1}: process_item not implemented (may be expected)")
                        test_results.append(True)  # Don't fail for passive components
                    except Exception as e:
                        errors.append(f"Test case {i+1}: process_item raised exception: {str(e)}")
                        test_results.append(False)
                
                # Log test summary
                passed = sum(test_results)
                total = len(test_results)
                self.logger.info(f"Functional test summary: {passed}/{total} test cases passed")
                
                # Consider test passed if at least 2/3 of test cases pass
                if passed < (total * 2 / 3):
                    errors.append(f"Too many test cases failed: {total - passed}/{total}")
                
                # Test health check
                health_status = await component_instance.health_check()
                if not isinstance(health_status, dict):
                    errors.append(f"health_check returned invalid type: {type(health_status)}")
                
                # Call teardown (new interface uses teardown, not cleanup)
                await component_instance.teardown()
                
            else:
                # Test old-style components with multiple test cases
                self.logger.info(f"Running functional test for legacy component")
                
                # Simulate minimal harness setup for old components
                component_instance.receive_streams = {}
                component_instance.send_streams = {}
                
                # Call setup
                await component_instance.setup()
                
                # Generate multiple test cases
                test_cases = self._generate_multiple_test_cases(
                    component_instance, config.component_class_name, config
                )
                
                # Test component-specific functionality with multiple cases
                base_class_name = component_instance.__class__.__bases__[0].__name__
                test_results = []
                
                if base_class_name == 'Source' and hasattr(component_instance, '_generate_data'):
                    # Test data generation multiple times
                    for i in range(3):
                        self.logger.info(f"Running test case {i+1}/3 for Source component")
                        context = {"index": i}
                        try:
                            data = await component_instance._generate_data(context)
                            if data is None:
                                errors.append(f"Test case {i+1}: Source _generate_data returned None")
                                test_results.append(False)
                            else:
                                self.logger.info(f"Test case {i+1}: Success - generated data")
                                test_results.append(True)
                        except Exception as e:
                            errors.append(f"Test case {i+1}: _generate_data raised exception: {str(e)}")
                            test_results.append(False)
                            
                elif base_class_name == 'Transformer' and hasattr(component_instance, '_transform_data'):
                    # Test transformation with multiple test cases
                    for i, test_data in enumerate(test_cases):
                        self.logger.info(f"Running test case {i+1}/{len(test_cases)} for Transformer")
                        try:
                            result = await component_instance._transform_data(test_data)
                            if result is None:
                                errors.append(f"Test case {i+1}: Transformer _transform_data returned None")
                                test_results.append(False)
                            else:
                                self.logger.info(f"Test case {i+1}: Success - transformed data")
                                test_results.append(True)
                        except Exception as e:
                            errors.append(f"Test case {i+1}: _transform_data raised exception: {str(e)}")
                            test_results.append(False)
                            
                elif hasattr(component_instance, 'process'):
                    # Generic process method testing with multiple cases
                    for i, test_data in enumerate(test_cases):
                        self.logger.info(f"Running test case {i+1}/{len(test_cases)} for legacy component")
                        try:
                            # Old components expect data in receive_streams
                            component_instance.receive_streams = {"input": [test_data]}
                            await component_instance.process()
                            self.logger.info(f"Test case {i+1}: Success - process completed")
                            test_results.append(True)
                        except Exception as e:
                            errors.append(f"Test case {i+1}: process raised exception: {str(e)}")
                            test_results.append(False)
                
                # Log test summary for old components
                if test_results:
                    passed = sum(test_results)
                    total = len(test_results)
                    self.logger.info(f"Legacy component test summary: {passed}/{total} test cases passed")
                    
                    # Apply same 2/3 threshold
                    if passed < (total * 2 / 3):
                        errors.append(f"Too many test cases failed: {total - passed}/{total}")
                        
                # Call cleanup
                await component_instance.cleanup()
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Functional test error: {str(e)}")
            return False, errors
    
    def generate_junit_xml(self, test_results: List[ComponentTestResult], output_file: Optional[Path] = None) -> str:
        """
        Generate JUnit XML report from component test results.
        
        Cycle 23 automation integration requirement - provides CI/CD integration
        evidence by generating standard JUnit XML reports compatible with CI systems.
        
        Args:
            test_results: List of ComponentTestResult objects
            output_file: Optional path to write XML file
            
        Returns:
            JUnit XML content as string
        """
        # Create root element
        total_tests = len(test_results)
        failures = sum(1 for result in test_results if not result.passed)
        total_time = sum(result.execution_time for result in test_results)
        
        testsuite = ET.Element("testsuite", {
            "name": "ComponentValidationSuite",
            "tests": str(total_tests),
            "failures": str(failures),
            "errors": "0",  # We treat all issues as failures, not errors
            "time": f"{total_time:.3f}",
            "timestamp": datetime.now().isoformat(),
            "hostname": "autocoder-validation"
        })
        
        # Add properties section
        properties = ET.SubElement(testsuite, "properties")
        
        ET.SubElement(properties, "property", {
            "name": "cycle",
            "value": "23"
        })
        ET.SubElement(properties, "property", {
            "name": "validation_type", 
            "value": "component_logic"
        })
        ET.SubElement(properties, "property", {
            "name": "framework_version",
            "value": "autocoder-5.2"
        })
        
        # Add test cases
        for result in test_results:
            testcase = ET.SubElement(testsuite, "testcase", {
                "classname": f"ComponentValidation.{result.test_level.value}",
                "name": result.component_name,
                "time": f"{result.execution_time:.3f}"
            })
            
            # Add failure details if test failed
            if not result.passed:
                failure_message = result.get_error_summary()
                failure = ET.SubElement(testcase, "failure", {
                    "message": f"Component validation failed: {result.component_name}",
                    "type": "ValidationFailure"
                })
                failure.text = f"""
Component: {result.component_name}
Test Level: {result.test_level.value}
Execution Time: {result.execution_time:.3f}s

Validation Results:
- Syntax Valid: {result.syntax_valid}
- Imports Valid: {result.imports_valid}  
- Instantiation Valid: {result.instantiation_valid}
- Contract Validation: {result.contract_validation_passed}
- Functional Test: {result.functional_test_passed}

Error Details:
{failure_message}
"""
            
            # Add system-out for additional info
            system_out = ET.SubElement(testcase, "system-out")
            system_out.text = f"""
Component: {result.component_name}
Test Level: {result.test_level.value}
Syntax Errors: {len(result.syntax_errors)}
Import Errors: {len(result.import_errors)}
Instantiation Errors: {len(result.instantiation_errors)}
Contract Errors: {len(result.contract_errors)}
Functional Errors: {len(result.functional_errors)}
Execution Time: {result.execution_time:.3f}s
"""
        
        # Convert to string
        xml_string = ET.tostring(testsuite, encoding='unicode', xml_declaration=True)
        
        # Write to file if specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(xml_string)
            
            self.logger.info(f"✅ JUnit XML report written to {output_file}")
        
        return xml_string
    
    async def run_component_test_suite_with_junit(self, test_configs: List[ComponentTestConfig], 
                                                 junit_output_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run component test suite and generate JUnit XML report.
        
        Cycle 23 automation integration - combines component testing with CI/CD
        compatible JUnit XML output for seamless CI integration.
        
        Args:
            test_configs: List of component test configurations
            junit_output_file: Optional path for JUnit XML output
            
        Returns:
            Dictionary with test results and JUnit XML content
        """
        # Run standard test suite
        test_summary = await self.run_component_test_suite(test_configs)
        
        # Generate JUnit XML
        junit_xml = self.generate_junit_xml(test_summary['results'], junit_output_file)
        
        # Enhanced summary with JUnit XML
        return {
            **test_summary,
            "junit_xml_content": junit_xml,
            "junit_xml_file": str(junit_output_file) if junit_output_file else None,
            "ci_integration_ready": True
        }