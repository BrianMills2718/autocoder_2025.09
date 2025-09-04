#!/usr/bin/env python3
"""
Filter Component - Phase 2 Advanced Component Implementation
Filters and transforms messages based on configurable conditions and actions
"""

import anyio
import logging
import re
from typing import Dict, Any, List, Optional, Callable, Union
from .composed_base import ComposedComponent
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Filter(ComposedComponent):
    """
    Filter component that filters and transforms messages based on configurable conditions.
    
    Configuration:
    - filter_conditions: List of filter conditions to evaluate
    - filter_action: Action to take (pass, block, transform, route)
    - transformation_rules: Rules for transforming messages
    - default_action: Default action if no conditions match
    - condition_type: Type of condition evaluation (expression, regex, function)
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        
        # Extract filter configuration
        self.filter_conditions = config.get("filter_conditions", [])
        self.filter_action = config.get("filter_action", "pass")
        self.transformation_rules = config.get("transformation_rules", [])
        self.default_action = config.get("default_action", "pass")
        self.condition_type = config.get("condition_type", "expression")
        
        # Validate configuration
        if not self.filter_conditions:
            raise ValueError("Filter must have filter_conditions configured")
        
        if self.filter_action not in ["pass", "block", "transform", "route"]:
            raise ValueError(f"Invalid filter_action: {self.filter_action}")
        
        if self.default_action not in ["pass", "block", "transform", "route"]:
            raise ValueError(f"Invalid default_action: {self.default_action}")
        
        # Validate filter conditions structure
        for i, condition in enumerate(self.filter_conditions):
            if not isinstance(condition, dict):
                raise ValueError(f"Filter condition {i} must be a dictionary")
            
            if "condition" not in condition:
                raise ValueError(f"Filter condition {i} missing 'condition' field")
            
            # Validate condition syntax
            self._validate_condition_syntax(condition["condition"], i)
            
            # Validate action if specified
            action = condition.get("action", self.filter_action)
            if action not in ["pass", "block", "transform", "route"]:
                raise ValueError(f"Invalid action in filter condition {i}: {action}")
        
        # Validate transformation rules if filter action is transform
        if self.filter_action == "transform" or any(
            cond.get("action") == "transform" for cond in self.filter_conditions
        ):
            if not self.transformation_rules:
                raise ValueError("transformation_rules required when filter_action is 'transform'")
            
            for i, rule in enumerate(self.transformation_rules):
                if not isinstance(rule, dict):
                    raise ValueError(f"Transformation rule {i} must be a dictionary")
                
                if "field" not in rule or "operation" not in rule:
                    raise ValueError(f"Transformation rule {i} missing 'field' or 'operation'")
        
        # Initialize filter statistics
        self.filter_stats = {
            "total_messages": 0,
            "messages_passed": 0,
            "messages_blocked": 0,
            "messages_transformed": 0,
            "messages_routed": 0,
            "conditions_matched": {},
            "filter_errors": 0
        }
        
        # Initialize condition match counters
        for i, condition in enumerate(self.filter_conditions):
            self.filter_stats["conditions_matched"][i] = 0
        
        self.structured_logger.info(
            f"Filter initialized with {len(self.filter_conditions)} conditions",
            operation="filter_init",
            tags={
                "conditions_count": len(self.filter_conditions),
                "filter_action": self.filter_action,
                "condition_type": self.condition_type
            }
        )

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Filter component"""
        return [
            ConfigRequirement(
                name="filter_conditions",
                type="list",
                description="List of filter conditions to apply",
                required=True,
                semantic_type=ConfigType.LIST,
                example='[{"field": "age", "operator": ">", "value": 18}]'
            ),
            ConfigRequirement(
                name="filter_mode",
                type="str",
                description="How to combine multiple conditions",
                required=False,
                default="all",
                options=["all", "any"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="transformation_rules",
                type="list",
                description="Optional transformations to apply after filtering",
                required=False,
                default=[],
                semantic_type=ConfigType.LIST
            )
        ]

    
    def _validate_condition_syntax(self, condition: str, condition_index: int) -> None:
        """Validate condition syntax based on condition type"""
        if self.condition_type == "expression":
            # Basic validation for expression conditions
            if not condition.strip():
                raise ValueError(f"Empty condition in filter condition {condition_index}")
            
            # Check for basic expression patterns
            valid_patterns = [
                r"message\.",  # message.field access
                r"item\.",     # item.field access
                r"==", "!=", "<", ">", "<=", ">=",  # comparison operators
                r"and", r"or", r"not",  # logical operators
                r"in", r"contains"  # membership operators
            ]
            
            if not any(re.search(pattern, condition) for pattern in valid_patterns):
                raise ValueError(f"Invalid expression condition in filter condition {condition_index}: {condition}")
        
        elif self.condition_type == "regex":
            # Validate regex pattern
            try:
                re.compile(condition)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern in filter condition {condition_index}: {e}")
        
        elif self.condition_type == "function":
            # Function conditions should be valid Python function names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', condition):
                raise ValueError(f"Invalid function name in filter condition {condition_index}: {condition}")
    
    async def evaluate_filter(self, condition: str, message: Any) -> bool:
        """Evaluate filter condition against message"""
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
                f"Filter condition evaluation failed: {e}",
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
            elif condition == "is_numeric":
                return isinstance(message, (int, float))
            elif condition == "is_list":
                return isinstance(message, list)
            else:
                raise ValueError(f"Unknown function condition: {condition}")
        
        except Exception as e:
            self.structured_logger.warning(
                f"Function condition evaluation failed: {e}",
                operation="function_evaluation",
                tags={"condition": condition, "error": str(e)}
            )
            return False
    
    async def should_pass(self, message: Any) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check if message should pass through filter.
        
        Returns:
            tuple: (should_pass, action, condition_data)
        """
        try:
            # Check each filter condition in order
            for i, condition_config in enumerate(self.filter_conditions):
                condition = condition_config["condition"]
                action = condition_config.get("action", self.filter_action)
                
                if await self.evaluate_filter(condition, message):
                    self.filter_stats["conditions_matched"][i] += 1
                    
                    self.structured_logger.debug(
                        f"Filter condition {i} matched, action: {action}",
                        operation="filter_evaluation",
                        tags={
                            "condition_index": i,
                            "action": action,
                            "condition": condition
                        }
                    )
                    
                    # Return action and condition data
                    return action == "pass", action, condition_config
            
            # No conditions matched, use default action
            self.structured_logger.debug(
                f"No filter conditions matched, using default action: {self.default_action}",
                operation="filter_evaluation",
                tags={"action": self.default_action}
            )
            
            return self.default_action == "pass", self.default_action, None
        
        except Exception as e:
            self.filter_stats["filter_errors"] += 1
            self.structured_logger.error(
                f"Filter evaluation failed: {e}",
                operation="filter_evaluation",
                error=e,
                tags={"message": str(message)}
            )
            # Default to pass on error
            return True, "pass", None
    
    async def transform_message(self, message: Any, transformation_rules: List[Dict[str, Any]] = None) -> Any:
        """Transform message based on transformation rules"""
        try:
            rules = transformation_rules or self.transformation_rules
            
            # Work with a copy of the message to avoid modifying the original
            if isinstance(message, dict):
                transformed = message.copy()
            elif hasattr(message, '__dict__'):
                # CRITICAL FIX: Create new dict from object attributes
                transformed = message.__dict__.copy()
                # Copy any additional attributes that might not be in __dict__
                for attr_name in dir(message):
                    if not attr_name.startswith('_') and not callable(getattr(message, attr_name)):
                        attr_value = getattr(message, attr_name)
                        if attr_name not in transformed:
                            transformed[attr_name] = attr_value
            else:
                # For non-dict, non-object messages, wrap in a dict
                transformed = {"value": message}
            
            for rule in rules:
                field = rule["field"]
                operation = rule["operation"]
                
                if operation == "set":
                    value = rule.get("value", "")
                    transformed[field] = value  # Always set on dictionary
                
                elif operation == "append":
                    value = rule.get("value", "")
                    current = transformed.get(field, "")
                    transformed[field] = str(current) + str(value)
                
                elif operation == "prepend":
                    value = rule.get("value", "")
                    current = transformed.get(field, "")
                    transformed[field] = str(value) + str(current)
                
                elif operation == "remove":
                    transformed.pop(field, None)
                
                elif operation == "replace":
                    old_value = rule.get("old_value", "")
                    new_value = rule.get("new_value", "")
                    current = str(transformed.get(field, ""))
                    transformed[field] = current.replace(old_value, new_value)
                
                elif operation == "regex_replace":
                    pattern = rule.get("pattern", "")
                    replacement = rule.get("replacement", "")
                    current = str(transformed.get(field, ""))
                    transformed[field] = re.sub(pattern, replacement, current)
                
                else:
                    raise ValueError(f"Unknown transformation operation: {operation}")
            
            return transformed
        
        except Exception as e:
            self.structured_logger.error(
                f"Message transformation failed: {e}",
                operation="message_transformation",
                error=e,
                tags={"message": str(message)}
            )
            # Return original message on transformation error
            return message
    
    async def process_item(self, item: Any) -> Any:
        """Process item through filter"""
        try:
            # Update statistics
            self.filter_stats["total_messages"] += 1
            
            # Validate input
            if item is None:
                self.structured_logger.warning(
                    "Received None item, blocking",
                    operation="item_processing"
                )
                self.filter_stats["messages_blocked"] += 1
                return None
            
            # Evaluate filter conditions
            should_pass, action, condition_data = await self.should_pass(item)
            
            if action == "block":
                self.filter_stats["messages_blocked"] += 1
                
                self.structured_logger.debug(
                    f"Item blocked by filter",
                    operation="item_processing",
                    tags={"action": action, "item_type": type(item).__name__}
                )
                
                return None
            
            elif action == "pass":
                self.filter_stats["messages_passed"] += 1
                
                self.structured_logger.debug(
                    f"Item passed through filter",
                    operation="item_processing",
                    tags={"action": action, "item_type": type(item).__name__}
                )
                
                # Record successful processing
                self.metrics_collector.record_items_processed()
                return item
            
            elif action == "transform":
                self.filter_stats["messages_transformed"] += 1
                
                # Apply transformation
                transformation_rules = None
                if condition_data and "transformation_rules" in condition_data:
                    transformation_rules = condition_data["transformation_rules"]
                
                transformed_item = await self.transform_message(item, transformation_rules)
                
                self.structured_logger.debug(
                    f"Item transformed by filter",
                    operation="item_processing",
                    tags={"action": action, "item_type": type(item).__name__}
                )
                
                # Record successful processing
                self.metrics_collector.record_items_processed()
                return transformed_item
            
            elif action == "route":
                self.filter_stats["messages_routed"] += 1
                
                # Create routed message with metadata
                destination = condition_data.get("destination", "default") if condition_data else "default"
                routed_message = {
                    "original_message": item,
                    "destination": destination,
                    "filter_name": self.name,
                    "routing_timestamp": anyio.get_cancelled_exc_class().time()
                }
                
                self.structured_logger.debug(
                    f"Item routed by filter to {destination}",
                    operation="item_processing",
                    tags={"action": action, "destination": destination}
                )
                
                # Record successful processing
                self.metrics_collector.record_items_processed()
                return routed_message
            
            else:
                raise ValueError(f"Unknown filter action: {action}")
        
        except Exception as e:
            self.filter_stats["filter_errors"] += 1
            self.metrics_collector.record_error(e.__class__.__name__)
            
            self.structured_logger.error(
                f"Item processing failed: {e}",
                operation="item_processing",
                error=e,
                tags={"item": str(item)}
            )
            
            # Re-raise to allow error handling upstream
            raise
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filter statistics"""
        return {
            **self.filter_stats,
            "filter_conditions_count": len(self.filter_conditions),
            "filter_action": self.filter_action,
            "default_action": self.default_action,
            "condition_type": self.condition_type
        }
    
    def reset_filter_stats(self) -> None:
        """Reset filter statistics"""
        self.filter_stats = {
            "total_messages": 0,
            "messages_passed": 0,
            "messages_blocked": 0,
            "messages_transformed": 0,
            "messages_routed": 0,
            "conditions_matched": {},
            "filter_errors": 0
        }
        
        # Reset condition match counters
        for i in range(len(self.filter_conditions)):
            self.filter_stats["conditions_matched"][i] = 0
        
        self.structured_logger.info(
            "Filter statistics reset",
            operation="stats_reset"
        )
    
    @classmethod
    def get_required_config_fields(cls) -> List[ConfigRequirement]:
        """Get list of required configuration fields with full specifications"""
        return [
            ConfigRequirement(
                name="filter_conditions",
                type="list",
                description="List of filter conditions to evaluate messages",
                required=True,
                example=[{"condition": "data.type == 'user'", "action": "pass"}],
                validator=lambda x: isinstance(x, list) and len(x) > 0
            ),
            ConfigRequirement(
                name="filter_action",
                type="str",
                description="Default action to take when conditions match",
                required=False,
                default="pass",
                options=["pass", "block", "transform", "route"]
            ),
            ConfigRequirement(
                name="transformation_rules",
                type="list",
                description="Rules for transforming messages",
                required=False,
                default=[],
                depends_on={"filter_action": "transform"},
                example=[{"field": "data.value", "operation": "multiply", "factor": 2}]
            ),
            ConfigRequirement(
                name="default_action",
                type="str",
                description="Action when no conditions match",
                required=False,
                default="pass",
                options=["pass", "block", "transform", "route"]
            ),
            ConfigRequirement(
                name="condition_type",
                type="str",
                description="Type of condition evaluation",
                required=False,
                default="expression",
                options=["expression", "regex", "function", "custom"]
            ),
            ConfigRequirement(
                name="custom_functions",
                type="dict",
                description="Custom evaluation functions",
                required=False,
                depends_on={"condition_type": ["function", "custom"]},
                example={"validate_user": "lambda x: x.get('age', 0) >= 18"}
            )
        ]
    
    @classmethod
    def get_required_dependencies(cls) -> List[str]:
        """Get list of required dependencies"""
        return []  # No external dependencies required
    
    async def is_ready(self) -> bool:
        """Check if filter is ready to process messages"""
        # Filter is ready if it has valid filter conditions
        return bool(self.filter_conditions)
    
    async def health_check(self) -> Dict[str, Any]:
        """Filter health check"""
        return {
            "status": "healthy",
            "component": "Filter",
            "name": self.name,
            "filter_conditions": len(self.filter_conditions),
            "filter_action": self.filter_action,
            "default_action": self.default_action,
            "condition_type": self.condition_type,
            "transformation_rules": len(self.transformation_rules),
            "statistics": self.get_filter_stats()
        }