#!/usr/bin/env python3
"""
BlueprintExtractor - Extract business requirements from blueprint components

This module converts blueprint component definitions into BusinessLogicSpec objects,
preserving all business context while filtering out infrastructure concerns.
"""

import re
from typing import Dict, Any, List, Optional
from .business_logic_spec import BusinessLogicSpec


class BlueprintExtractor:
    """
    Extracts business logic requirements from blueprint component definitions.
    
    Preserves all business-relevant information while discarding infrastructure
    and boilerplate concerns that should be handled programmatically.
    """
    
    def extract_business_requirements(self, component) -> BusinessLogicSpec:
        """
        Extract business requirements from a blueprint component.
        
        Args:
            component: Blueprint component object with name, type, description, 
                      config, inputs, and outputs attributes
                      
        Returns:
            BusinessLogicSpec containing focused business requirements
        """
        # Extract core identification
        component_name = component.name
        component_type = component.type
        business_purpose = self._extract_business_purpose(component.description, component.type)
        
        # Extract transformation description
        transformation_description = self._extract_transformation_logic(
            component.description, 
            component.config
        )
        
        # Extract input/output schemas
        input_schema = self._extract_input_schema(component.inputs)
        output_schema = self._extract_output_schema(component.outputs)
        
        # Extract edge cases
        edge_cases = self._extract_edge_cases(component.description, component.config)
        
        # Extract quality requirements
        quality_requirements = self._extract_quality_requirements(component.config)
        
        # Extract validation rules
        validation_rules = self._extract_validation_rules(component.config, component.description)
        
        return BusinessLogicSpec(
            component_name=component_name,
            component_type=component_type,
            business_purpose=business_purpose,
            input_schema=input_schema,
            output_schema=output_schema,
            transformation_description=transformation_description,
            edge_cases=edge_cases,
            quality_requirements=quality_requirements,
            validation_rules=validation_rules
        )
    
    def _extract_business_purpose(self, description: str, component_type: str) -> str:
        """Extract clear business purpose from component description"""
        if not description:
            return f"Process data using {component_type} pattern"
            
        # Clean up description and focus on business value
        purpose = description.strip()
        
        # Add component type context if not already present
        type_keywords = {
            'Source': ['generate', 'create', 'produce', 'emit'],
            'Transformer': ['transform', 'process', 'convert', 'modify'],
            'Sink': ['store', 'save', 'persist', 'output'],
            'Store': ['store', 'persist', 'cache', 'database'],
            'APIEndpoint': ['handle', 'serve', 'api', 'endpoint'],
            'Router': ['route', 'dispatch', 'forward', 'direct']
        }
        
        type_words = type_keywords.get(component_type, [])
        if not any(word in purpose.lower() for word in type_words):
            purpose = f"{purpose} using {component_type.lower()} pattern"
            
        return purpose
    
    def _extract_transformation_logic(self, description: str, config: Dict[str, Any]) -> str:
        """Extract specific transformation logic from description and config"""
        transformation_parts = []
        
        # Extract from description
        if description:
            # Look for specific transformation patterns and extract key operations
            transformation_patterns = [
                (r'doubl\w*', 'double'),
                (r'tripl\w*', 'triple'),
                (r'filter\w*', 'filter'),
                (r'sort\w*', 'sort'),
                (r'group\w*', 'group'),
                (r'aggregate\w*', 'aggregate'),
                (r'sum\w*', 'sum'),
                (r'count\w*', 'count'),
                (r'average\w*', 'average'),
                (r'convert\w*', 'convert'),
                (r'transform\w*', 'transform'),
                (r'modify\w*', 'modify'),
                (r'multipl\w*', 'multiply'),
                (r'divid\w*', 'divide'),
                (r'add\w*', 'add'),
                (r'subtract\w*', 'subtract')
            ]
            
            found_operations = []
            for pattern, operation in transformation_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    found_operations.append(operation)
            
            if found_operations:
                # Extract more context around operations
                for operation in found_operations:
                    # Look for patterns like "by doubling" or "multiply by 2"
                    context_patterns = [
                        rf'by {operation}[^.]*',
                        rf'{operation}[^.]*by[^.]*',
                        rf'{operation}[^.]*'
                    ]
                    
                    for ctx_pattern in context_patterns:
                        matches = re.findall(ctx_pattern, description, re.IGNORECASE)
                        if matches:
                            transformation_parts.extend(matches)
                            break
                    else:
                        # Fallback: just add the operation
                        transformation_parts.append(operation)
        
        # Extract from config
        if config:
            # Look for transformation-specific config
            transformation_config = {}
            for key, value in config.items():
                if any(keyword in key.lower() for keyword in [
                    'rule', 'transform', 'filter', 'format', 'algorithm',
                    'method', 'operation', 'action', 'process', 'multiplier'
                ]):
                    transformation_config[key] = value
            
            if transformation_config:
                config_desc = []
                for key, value in transformation_config.items():
                    if isinstance(value, list):
                        config_desc.append(f"apply {key}: {', '.join(map(str, value))}")
                    else:
                        config_desc.append(f"{key} = {value}")
                transformation_parts.extend(config_desc)
        
        if transformation_parts:
            return "; ".join(transformation_parts)
        else:
            # Fallback: use description or generic transformation
            return description if description else "Process input data and generate output"
    
    def _extract_input_schema(self, inputs: List) -> Dict[str, Any]:
        """Extract input schema from component input ports"""
        schema = {}
        
        for input_port in inputs:
            port_name = getattr(input_port, 'name', str(input_port))
            port_info = {
                "type": getattr(input_port, 'schema_type', 'object'),
                "description": getattr(input_port, 'description', ''),
                "required": getattr(input_port, 'required', True)
            }
            schema[port_name] = port_info
            
        return schema
    
    def _extract_output_schema(self, outputs: List) -> Dict[str, Any]:
        """Extract output schema from component output ports"""
        schema = {}
        
        for output_port in outputs:
            port_name = getattr(output_port, 'name', str(output_port))
            port_info = {
                "type": getattr(output_port, 'schema_type', 'object'),
                "description": getattr(output_port, 'description', '')
            }
            schema[port_name] = port_info
            
        return schema
    
    def _extract_edge_cases(self, description: str, config: Dict[str, Any]) -> List[str]:
        """Extract edge cases from description and configuration"""
        edge_cases = []
        
        # Extract from description
        if description:
            edge_case_indicators = [
                'empty', 'null', 'invalid', 'malformed', 'missing', 'error',
                'timeout', 'fail', 'exception', 'boundary', 'limit', 'overflow',
                'negative', 'zero', 'duplicate', 'concurrent'
            ]
            
            for indicator in edge_case_indicators:
                if indicator in description.lower():
                    # Extract sentence containing the indicator
                    sentences = re.split(r'[.!?]+', description)
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            edge_cases.append(f"Handle {indicator} input")
        
        # Extract from config
        if config:
            # Look for validation and constraint configs
            for key, value in config.items():
                if 'allow_empty' in key.lower() and not value:
                    edge_cases.append("Handle empty input")
                if 'max_length' in key.lower() or 'length' in key.lower():
                    edge_cases.append(f"Handle input exceeding length limits")
                if 'required_fields' in key.lower() and isinstance(value, list):
                    edge_cases.append(f"Handle missing required fields")
                if 'validation' in key.lower():
                    edge_cases.append("Handle validation failures")
                if 'timeout' in key.lower():
                    edge_cases.append("Handle timeout scenarios")
                if 'retry' in key.lower():
                    edge_cases.append("Handle retry failures")
        
        return list(set(edge_cases))  # Remove duplicates
    
    def _extract_quality_requirements(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quality/performance requirements from config"""
        quality_req = {}
        
        if not config:
            return quality_req
            
        # Performance requirements
        performance_keys = [
            'max_latency_ms', 'latency', 'timeout_ms', 'timeout_seconds',
            'throughput_rps', 'throughput', 'rate_limit_rps', 'rate_limit',
            'memory_limit_mb', 'memory_limit', 'cpu_limit', 'max_memory',
            'batch_size', 'buffer_size', 'connection_pool_size',
            'max_connections', 'retry_attempts', 'retry_count',
            'error_tolerance', 'accuracy_required', 'interval_seconds',
            'interval', 'frequency', 'auth_required'
        ]
        
        for key, value in config.items():
            if any(perf_key in key.lower() for perf_key in performance_keys):
                quality_req[key] = value
            
            # Handle nested performance config
            if isinstance(value, dict) and any(word in key.lower() for word in ['performance', 'quality', 'sla']):
                quality_req.update(value)
                
        return quality_req
    
    def _extract_validation_rules(self, config: Dict[str, Any], description: str) -> List[str]:
        """Extract validation rules from config and description"""
        rules = []
        
        # Extract from config
        if config:
            for key, value in config.items():
                if 'validation' in key.lower():
                    if isinstance(value, list):
                        rules.extend([f"Must satisfy {rule}" for rule in value])
                    elif isinstance(value, dict):
                        for rule_key, rule_value in value.items():
                            rules.append(f"Must have {rule_key}: {rule_value}")
                    else:
                        rules.append(f"Must pass {key} validation")
                        
                if 'rule' in key.lower():
                    if isinstance(value, list):
                        rules.extend([f"Must follow rule: {rule}" for rule in value])
                    else:
                        rules.append(f"Must follow rule: {value}")
        
        # Extract from description
        if description:
            # Look for requirement keywords
            requirement_patterns = [
                r'must \w+[^.]*',
                r'should \w+[^.]*', 
                r'required to \w+[^.]*',
                r'needs to \w+[^.]*'
            ]
            
            for pattern in requirement_patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                rules.extend(matches)
        
        return rules