#!/usr/bin/env python3
"""
Router Component - Phase 2 Advanced Component Implementation
Routes messages based on configurable conditions and rules
"""

import anyio
import logging
import re
from typing import Dict, Any, List, Optional, Callable
from .composed_base import ComposedComponent
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Router(ComposedComponent):
    """
    Router component that routes messages based on configurable conditions.
    
    Configuration:
    - routing_rules: List of routing rules with condition and destination
    - default_route: Default destination if no rules match
    - condition_type: Type of condition evaluation (expression, regex, function)
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # Extract routing configuration
        self.routing_rules = config.get("routing_rules", [])
        self.default_route = config.get("default_route", None)
        self.condition_type = config.get("condition_type", "expression")
        
        # Validate configuration
        if not self.routing_rules and not self.default_route:
            raise ValueError("Router must have either routing_rules or default_route configured")
        
        # Validate routing rules structure
        for i, rule in enumerate(self.routing_rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Routing rule {i} must be a dictionary")
            
            if "condition" not in rule:
                raise ValueError(f"Routing rule {i} missing 'condition' field")
            
            if "destination" not in rule:
                raise ValueError(f"Routing rule {i} missing 'destination' field")
            
            # Validate condition syntax based on type
            self._validate_condition_syntax(rule["condition"], i)
        
        # Initialize routing statistics
        self.routing_stats = {
            "total_messages": 0,
            "rules_matched": {},
            "default_route_used": 0,
            "routing_errors": 0
        }
        
        # Initialize rule match counters
        for i, rule in enumerate(self.routing_rules):
            self.routing_stats["rules_matched"][i] = 0
        
        self.structured_logger.info(
            f"Router initialized with {len(self.routing_rules)} rules",
            operation="router_init",
            tags={"rules_count": len(self.routing_rules), "default_route": self.default_route}
        )

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Router component"""
        return [
            ConfigRequirement(
                name="routing_rules",
                type="list",
                description="List of routing rules",
                required=True,
                semantic_type=ConfigType.LIST,
                example=r'[{"condition": "type == \"A\"", "route": "route_a"}]'
            ),
            ConfigRequirement(
                name="default_route",
                type="str",
                description="Default route when no rules match",
                required=False,
                default="default",
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="route_evaluation_mode",
                type="str",
                description="How to evaluate routing rules",
                required=False,
                default="first_match",
                options=["first_match", "all_matches"],
                semantic_type=ConfigType.STRING
            )
        ]

    
    def _validate_condition_syntax(self, condition: str, rule_index: int) -> None:
        """Validate condition syntax based on condition type"""
        if self.condition_type == "expression":
            # Basic validation for expression conditions
            if not condition.strip():
                raise ValueError(f"Empty condition in rule {rule_index}")
            
            # Check for basic expression patterns
            valid_patterns = [
                r"message\.",  # message.field access
                r"item\.",     # item.field access
                r"==", "!=", "<", ">", "<=", ">=",  # comparison operators
                r"and", r"or", r"not",  # logical operators
                r"in", r"contains"  # membership operators
            ]
            
            if not any(re.search(pattern, condition) for pattern in valid_patterns):
                raise ValueError(f"Invalid expression condition in rule {rule_index}: {condition}")
        
        elif self.condition_type == "regex":
            # Validate regex pattern
            try:
                re.compile(condition)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern in rule {rule_index}: {e}")
        
        elif self.condition_type == "function":
            # Function conditions should be valid Python function names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', condition):
                raise ValueError(f"Invalid function name in rule {rule_index}: {condition}")
    
    async def evaluate_condition(self, condition: str, message: Any) -> bool:
        """Evaluate routing condition against message"""
        try:
            if self.condition_type == "expression":
                return await self._evaluate_expression_condition(condition, message)
            elif self.condition_type == "regex":
                return await self._evaluate_regex_condition(condition, message)
            elif self.condition_type == "function":
                return await self._evaluate_function_condition(condition, message)
            else:
                raise ValueError(f"Unknown condition type: {self.condition_type}")
        
        except Exception as e:
            self.structured_logger.error(
                f"Condition evaluation failed: {e}",
                operation="condition_evaluation",
                error=e,
                tags={"condition": condition, "condition_type": self.condition_type}
            )
            return False
    
    async def _evaluate_expression_condition(self, condition: str, message: Any) -> bool:
        """Evaluate expression-based condition"""
        # Create safe evaluation context
        context = {
            "message": message,
            "item": message,  # Alias for compatibility
            "hasattr": hasattr,
            "getattr": getattr,
            "isinstance": isinstance,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "len": len,
            "type": type,
            "dict": dict,
            "list": list,
            "tuple": tuple,
            "set": set
        }
        
        # Add message attributes to context for direct access
        if hasattr(message, '__dict__'):
            context.update(message.__dict__)
        elif isinstance(message, dict):
            context.update(message)
        
        try:
            # Evaluate condition safely
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            self.structured_logger.warning(
                f"Expression condition evaluation failed: {e}",
                operation="expression_evaluation",
                tags={"condition": condition, "error": str(e)}
            )
            return False
    
    async def _evaluate_regex_condition(self, condition: str, message: Any) -> bool:
        """Evaluate regex-based condition"""
        try:
            # Convert message to string representation
            message_str = str(message)
            if hasattr(message, '__dict__'):
                message_str = str(message.__dict__)
            elif isinstance(message, dict):
                message_str = str(message)
            
            # Perform regex match
            pattern = re.compile(condition)
            return bool(pattern.search(message_str))
        
        except Exception as e:
            self.structured_logger.warning(
                f"Regex condition evaluation failed: {e}",
                operation="regex_evaluation",
                tags={"condition": condition, "error": str(e)}
            )
            return False
    
    async def _evaluate_function_condition(self, condition: str, message: Any) -> bool:
        """Evaluate function-based condition"""
        try:
            # Look for function in config or use built-in functions
            custom_functions = self.config.get("custom_functions", {})
            
            if condition in custom_functions:
                func = custom_functions[condition]
                if callable(func):
                    result = func(message)
                    return bool(result)
                else:
                    raise ValueError(f"Custom function '{condition}' is not callable")
            
            # Built-in function conditions
            if condition == "is_dict":
                return isinstance(message, dict)
            elif condition == "is_string":
                return isinstance(message, str)
            elif condition == "is_empty":
                return not bool(message)
            elif condition == "has_data":
                return bool(message)
            else:
                raise ValueError(f"Unknown function condition: {condition}")
        
        except Exception as e:
            self.structured_logger.warning(
                f"Function condition evaluation failed: {e}",
                operation="function_evaluation",
                tags={"condition": condition, "error": str(e)}
            )
            return False
    
    async def route_message(self, message: Any) -> str:
        """Determine destination for message based on routing rules"""
        try:
            # Check each routing rule in order
            for i, rule in enumerate(self.routing_rules):
                condition = rule["condition"]
                destination = rule["destination"]
                
                if await self.evaluate_condition(condition, message):
                    self.routing_stats["rules_matched"][i] += 1
                    
                    self.structured_logger.debug(
                        f"Message routed to {destination} via rule {i}",
                        operation="message_routing",
                        tags={
                            "destination": destination,
                            "rule_index": i,
                            "condition": condition
                        }
                    )
                    
                    return destination
            
            # No rules matched, use default route
            if self.default_route:
                self.routing_stats["default_route_used"] += 1
                
                self.structured_logger.debug(
                    f"Message routed to default destination: {self.default_route}",
                    operation="message_routing",
                    tags={"destination": self.default_route, "route_type": "default"}
                )
                
                return self.default_route
            
            # No default route configured
            raise ValueError("No routing rule matched and no default route configured")
        
        except Exception as e:
            self.routing_stats["routing_errors"] += 1
            self.structured_logger.error(
                f"Message routing failed: {e}",
                operation="message_routing",
                error=e,
                tags={"message": str(message)}
            )
            raise
    
    async def process_item(self, item: Any) -> Any:
        """Process item through router"""
        try:
            self.routing_stats["total_messages"] += 1
            
            # Validate input
            if item is None:
                raise ValueError("Cannot route None item")
            
            # Route the message
            destination = await self.route_message(item)
            
            # Create routed message with metadata
            routed_message = {
                "original_message": item,
                "destination": destination,
                "router_name": self.name,
                "routing_timestamp": anyio.get_cancelled_exc_class().time()
            }
            
            # Record successful routing
            self.metrics_collector.record_items_processed()
            
            self.structured_logger.debug(
                f"Item successfully routed to {destination}",
                operation="item_routing",
                tags={
                    "destination": destination,
                    "item_type": type(item).__name__
                }
            )
            
            return routed_message
        
        except Exception as e:
            self.routing_stats["routing_errors"] += 1
            self.metrics_collector.record_error(e.__class__.__name__)
            
            self.structured_logger.error(
                f"Item routing failed: {e}",
                operation="item_routing",
                error=e,
                tags={"item": str(item)}
            )
            
            # Re-raise to allow error handling upstream
            raise
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            **self.routing_stats,
            "routing_rules_count": len(self.routing_rules),
            "default_route": self.default_route,
            "condition_type": self.condition_type
        }
    
    def reset_routing_stats(self) -> None:
        """Reset routing statistics"""
        self.routing_stats = {
            "total_messages": 0,
            "rules_matched": {},
            "default_route_used": 0,
            "routing_errors": 0
        }
        
        # Reset rule match counters
        for i in range(len(self.routing_rules)):
            self.routing_stats["rules_matched"][i] = 0
        
        self.structured_logger.info(
            "Router statistics reset",
            operation="stats_reset"
        )
    
    @classmethod
    def get_required_config_fields(cls) -> List[str]:
        """Get list of required configuration fields"""
        return []  # routing_rules or default_route required, but not both
    
    @classmethod
    def get_required_dependencies(cls) -> List[str]:
        """Get list of required dependencies"""
        return []  # No external dependencies required
    
    async def is_ready(self) -> bool:
        """Check if router is ready to process messages"""
        # Router is ready if it has valid routing configuration
        return bool(self.routing_rules or self.default_route)
    
    async def health_check(self) -> Dict[str, Any]:
        """Router health check"""
        return {
            "status": "healthy",
            "component": "Router",
            "name": self.name,
            "routing_rules": len(self.routing_rules),
            "default_route": self.default_route,
            "condition_type": self.condition_type,
            "statistics": self.get_routing_stats()
        }