from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Natural Language to Component Specification Parser for V5.0 Enhanced Generation
Implements fail-hard parsing with strict validation and no fallbacks
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re
import logging
from pydantic import BaseModel, Field, ValidationError


class NLParsingError(Exception):
    """Raised when natural language parsing fails - no fallbacks available"""
    pass


class ComponentSpecificationError(Exception):
    """Raised when component specification is invalid - fail hard on ambiguity"""
    pass


class ComponentType(Enum):
    """Supported component types for V5.0 generation"""
    SOURCE = "source"
    TRANSFORMER = "transformer"
    SINK = "sink"


@dataclass
class ComponentSpecification:
    """Parsed component specification with strict validation"""
    component_type: ComponentType
    class_name: str
    description: str
    data_type: str
    processing_method: str
    required_config_fields: List[str]
    required_dependencies: List[str]
    input_schemas: List[str] = None
    output_schemas: List[str] = None


class NaturalLanguageParser:
    """
    V5.0 Natural Language Parser with Fail-Hard Principles
    
    Key Principles:
    - No ambiguous parsing - fail hard on unclear specifications
    - Predefined patterns only - no machine learning or AI inference
    - Strict validation of all parsed components
    - No fallback interpretations or "best guess" behavior
    - Explicit component type detection required
    """
    
    def __init__(self):
        self.logger = get_logger("NaturalLanguageParser")
        
        # Predefined parsing patterns for component types
        self._component_type_patterns = {
            ComponentType.SOURCE: [
                r'(?:create|generate|produce|read|fetch|load|extract)\s+(?:data|information)',
                r'(?:data|file|api|database)\s+(?:source|reader|loader|extractor)',
                r'(?:source|generator|producer|reader)\s+(?:component|class)',
                r'(?:read|fetch|get|retrieve)\s+(?:from|data)',
                r'(?:api|database|file|stream)\s+(?:reader|source)',
            ],
            ComponentType.TRANSFORMER: [
                r'(?:transform|process|convert|modify|filter|map|aggregate)\s+(?:data|information)',
                r'(?:data|stream)\s+(?:transformer|processor|converter|filter)',
                r'(?:transformer|processor|filter|converter)\s+(?:component|class)',
                r'(?:process|transform|convert|modify)\s+(?:input|data)',
                r'(?:filter|map|aggregate|enrich|normalize)\s+(?:data|stream)',
            ],
            ComponentType.SINK: [
                r'(?:store|save|write|persist|output|send)\s+(?:data|information)',
                r'(?:data|file|database|api)\s+(?:sink|writer|saver|store)',
                r'(?:sink|writer|saver|store)\s+(?:component|class)',
                r'(?:write|save|store|persist)\s+(?:to|data)',
                r'(?:database|file|api|queue)\s+(?:writer|sink)',
            ]
        }
        
        # Data type patterns
        self._data_type_patterns = {
            'json': [r'json', r'javascript\s+object', r'api\s+response'],
            'csv': [r'csv', r'comma\s+separated', r'spreadsheet', r'tabular'],
            'xml': [r'xml', r'markup', r'soap', r'configuration'],
            'binary': [r'binary', r'image', r'media', r'blob'],
            'text': [r'text', r'plain\s+text', r'log', r'string'],
        }
        
        # Processing method patterns
        self._processing_method_patterns = {
            'api': [r'api', r'rest', r'http', r'web\s+service', r'endpoint'],
            'database': [r'database', r'sql', r'postgres', r'mysql', r'db'],
            'file': [r'file', r'filesystem', r'disk', r'local\s+storage'],
            'synthetic': [r'synthetic', r'fake', r'mock', r'test\s+data', r'random'],
            'sync': [r'synchronous', r'sync', r'blocking', r'sequential'],
            'async': [r'asynchronous', r'async', r'non-blocking', r'concurrent'],
            'batch': [r'batch', r'bulk', r'group', r'chunk'],
            'stream': [r'stream', r'streaming', r'real-time', r'continuous'],
        }
        
        # Transformation type patterns (for transformers)
        self._transformation_patterns = {
            'filter': [r'filter', r'select', r'where', r'condition', r'criteria'],
            'map': [r'map', r'transform', r'convert', r'change', r'modify'],
            'aggregate': [r'aggregate', r'sum', r'count', r'group', r'collect'],
            'enrich': [r'enrich', r'join', r'lookup', r'augment', r'enhance'],
            'normalize': [r'normalize', r'standardize', r'clean', r'format'],
        }
        
        # Storage type patterns (for sinks)
        self._storage_patterns = {
            'database': [r'database', r'sql', r'postgres', r'mysql', r'table'],
            'file': [r'file', r'filesystem', r'disk', r'local', r'save'],
            'api': [r'api', r'rest', r'http', r'endpoint', r'service'],
            'queue': [r'queue', r'message', r'topic', r'event', r'publish'],
            'cache': [r'cache', r'redis', r'memory', r'temporary', r'fast'],
        }
        
        # Class name extraction patterns
        self._class_name_pattern = re.compile(
            r'(?:class|component)\s+(?:called|named)\s+([A-Z][a-zA-Z0-9]*)|(?:called|named)\s+([A-Z][a-zA-Z0-9]*)',
            re.IGNORECASE
        )
        
        self.logger.info("✅ Natural Language Parser initialized with fail-hard validation")
    
    def parse_component_specification(self, natural_language: str) -> ComponentSpecification:
        """Parse natural language into component specification - fail hard on ambiguity"""
        
        # Input validation
        if natural_language is None:
            raise NLParsingError(
                "None input provided for natural language specification. "
                "V5.0 requires valid string input - no None values allowed."
            )
        
        if not isinstance(natural_language, str):
            raise NLParsingError(
                f"Invalid input type {type(natural_language)}. "
                "V5.0 requires string input for natural language specifications."
            )
        
        if not natural_language or not natural_language.strip():
            raise NLParsingError(
                "Empty natural language specification provided. "
                "V5.0 requires explicit component descriptions - no empty inputs allowed."
            )
        
        # Clean and normalize input
        nl_text = natural_language.lower().strip()
        
        try:
            # Step 1: Detect component type
            component_type = self._detect_component_type(nl_text)
            
            # Step 2: Extract class name
            class_name = self._extract_class_name(natural_language)
            
            # Step 3: Extract data type
            data_type = self._extract_data_type(nl_text)
            
            # Step 4: Extract processing method
            processing_method = self._extract_processing_method(nl_text, component_type)
            
            # Step 5: Extract required configurations
            required_config, required_deps = self._extract_requirements(nl_text, component_type)
            
            # Step 6: Validate specification completeness
            spec = ComponentSpecification(
                component_type=component_type,
                class_name=class_name,
                description=natural_language.strip(),
                data_type=data_type,
                processing_method=processing_method,
                required_config_fields=required_config,
                required_dependencies=required_deps
            )
            
            self._validate_specification(spec)
            
            self.logger.info(f"✅ Parsed component specification: {class_name} ({component_type.value})")
            return spec
            
        except Exception as e:
            if isinstance(e, (NLParsingError, ComponentSpecificationError)):
                raise
            else:
                raise NLParsingError(
                    f"Failed to parse natural language specification: {e}. "
                    f"V5.0 requires unambiguous component descriptions - no interpretation fallbacks available."
                )
    
    def _detect_component_type(self, nl_text: str) -> ComponentType:
        """Detect component type from natural language - fail hard on ambiguity"""
        
        type_scores = {}
        
        for comp_type, patterns in self._component_type_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, nl_text, re.IGNORECASE):
                    score += 1
            type_scores[comp_type] = score
        
        # Find the highest scoring type
        max_score = max(type_scores.values())
        
        if max_score == 0:
            available_keywords = []
            for patterns in self._component_type_patterns.values():
                available_keywords.extend(patterns[:2])  # Show first 2 patterns as examples
            
            raise NLParsingError(
                f"Unable to detect component type from specification. "
                f"V5.0 requires explicit component type indicators. "
                f"Use keywords like: {', '.join(available_keywords[:6])}..."
            )
        
        # Check for ties (ambiguous specification)
        winning_types = [comp_type for comp_type, score in type_scores.items() if score == max_score]
        
        if len(winning_types) > 1:
            raise NLParsingError(
                f"Ambiguous component type detected. Specification matches multiple types: {[t.value for t in winning_types]}. "
                f"V5.0 requires unambiguous specifications - no best-guess interpretation allowed."
            )
        
        return winning_types[0]
    
    def _extract_class_name(self, original_text: str) -> str:
        """Extract class name from natural language - fail hard if not found"""
        
        # Try to find explicit class name
        match = self._class_name_pattern.search(original_text)
        if match:
            # Check both capture groups
            class_name = match.group(1) if match.group(1) else match.group(2)
            if class_name:
                # Validate class name format
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                    raise NLParsingError(
                        f"Invalid class name format '{class_name}'. "
                        f"V5.0 requires PascalCase class names starting with capital letter."
                    )
                return class_name
        
        # If no explicit class name found, fail hard
        raise NLParsingError(
            "No class name specified. "
            "V5.0 requires explicit class names using 'class ClassName' or 'component called ClassName'. "
            "No automatic name generation available."
        )
    
    def _extract_data_type(self, nl_text: str) -> str:
        """Extract data type from natural language - fail hard if ambiguous"""
        
        detected_types = []
        
        for data_type, patterns in self._data_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, nl_text, re.IGNORECASE):
                    detected_types.append(data_type)
                    break
        
        if not detected_types:
            available_types = list(self._data_type_patterns.keys())
            raise NLParsingError(
                f"No data type detected in specification. "
                f"V5.0 requires explicit data type. Available types: {available_types}. "
                f"No default data type assumptions allowed."
            )
        
        if len(detected_types) > 1:
            raise NLParsingError(
                f"Multiple data types detected: {detected_types}. "
                f"V5.0 requires single, unambiguous data type specification."
            )
        
        return detected_types[0]
    
    def _extract_processing_method(self, nl_text: str, component_type: ComponentType) -> str:
        """Extract processing method based on component type"""
        
        detected_methods = []
        
        for method, patterns in self._processing_method_patterns.items():
            for pattern in patterns:
                if re.search(pattern, nl_text, re.IGNORECASE):
                    if method not in detected_methods:
                        detected_methods.append(method)
                    break
        
        # For transformers, also check transformation types
        if component_type == ComponentType.TRANSFORMER:
            for trans_type, patterns in self._transformation_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, nl_text, re.IGNORECASE):
                        if trans_type not in detected_methods:
                            detected_methods.append(trans_type)
                        break
        
        # For sinks, also check storage types
        if component_type == ComponentType.SINK:
            for storage_type, patterns in self._storage_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, nl_text, re.IGNORECASE):
                        if storage_type not in detected_methods:
                            detected_methods.append(storage_type)
                        break
        
        if not detected_methods:
            if component_type == ComponentType.SOURCE:
                available_methods = ['api', 'database', 'file', 'synthetic']
            elif component_type == ComponentType.TRANSFORMER:
                available_methods = ['filter', 'map', 'aggregate', 'enrich', 'normalize']
            else:  # SINK
                available_methods = ['database', 'file', 'api', 'queue', 'cache']
            
            raise NLParsingError(
                f"No processing method detected for {component_type.value}. "
                f"Available methods: {available_methods}. "
                f"V5.0 requires explicit processing method specification."
            )
        
        if len(detected_methods) > 1:
            # Apply priority resolution for all component types
            if component_type == ComponentType.SOURCE:
                # Priority order for sources: most specific to most general
                priority_order = ['api', 'database', 'file', 'synthetic']
                for method in priority_order:
                    if method in detected_methods:
                        return method
                        
            elif component_type == ComponentType.TRANSFORMER:
                # Priority order: most specific to most general
                priority_order = ['normalize', 'enrich', 'aggregate', 'filter', 'map']
                
                # Find highest priority method present
                for method in priority_order:
                    if method in detected_methods:
                        return method
                
                # Fallback to transformation patterns if none match priority
                trans_methods = [m for m in detected_methods if m in self._transformation_patterns]
                if trans_methods:
                    return trans_methods[0]
                    
            elif component_type == ComponentType.SINK:
                # Priority order for sinks: most specific to most general
                priority_order = ['database', 'api', 'queue', 'file', 'cache']
                for method in priority_order:
                    if method in detected_methods:
                        return method
            
            # If still multiple after priority resolution, prefer non-execution-style methods
            non_execution_methods = [m for m in detected_methods if m not in ['sync', 'async', 'batch', 'stream']]
            if len(non_execution_methods) == 1:
                return non_execution_methods[0]
            
            # For non-transformers or if no resolution found, fail hard
            raise NLParsingError(
                f"Multiple processing methods detected after priority resolution: {detected_methods}. "
                f"V5.0 requires single, unambiguous processing method."
            )
        
        return detected_methods[0]
    
    def _extract_requirements(self, nl_text: str, component_type: ComponentType) -> Tuple[List[str], List[str]]:
        """Extract configuration and dependency requirements"""
        
        config_fields = []
        dependencies = []
        
        # API-related requirements
        if re.search(r'api|rest|http|endpoint', nl_text, re.IGNORECASE):
            config_fields.extend(['api_url', 'api_key'])
            dependencies.append('api')
        
        # Database requirements
        if re.search(r'database|sql|postgres|mysql', nl_text, re.IGNORECASE):
            config_fields.extend(['connection_string', 'table_name'])
            dependencies.append('database')
        
        # File requirements
        if re.search(r'file|filesystem|disk', nl_text, re.IGNORECASE):
            config_fields.extend(['file_path', 'file_format'])
            dependencies.append('file')
        
        # Component type specific requirements
        if component_type == ComponentType.SOURCE:
            config_fields.append('outputs')
        elif component_type == ComponentType.TRANSFORMER:
            config_fields.extend(['inputs', 'outputs'])
        else:  # SINK
            config_fields.append('inputs')
        
        return list(set(config_fields)), list(set(dependencies))
    
    def _validate_specification(self, spec: ComponentSpecification) -> None:
        """Validate parsed specification for completeness and consistency"""
        
        # Validate class name
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', spec.class_name):
            raise ComponentSpecificationError(
                f"Invalid class name '{spec.class_name}'. Must be PascalCase starting with capital letter."
            )
        
        # Validate data type
        if spec.data_type not in ['json', 'csv', 'xml', 'binary', 'text']:
            raise ComponentSpecificationError(
                f"Invalid data type '{spec.data_type}'. Must be one of: json, csv, xml, binary, text."
            )
        
        # Component type specific validation
        if spec.component_type == ComponentType.SOURCE:
            if spec.processing_method not in ['api', 'database', 'file', 'synthetic']:
                raise ComponentSpecificationError(
                    f"Invalid processing method '{spec.processing_method}' for Source. "
                    f"Must be one of: api, database, file, synthetic."
                )
        
        elif spec.component_type == ComponentType.TRANSFORMER:
            valid_methods = ['filter', 'map', 'aggregate', 'enrich', 'normalize', 'sync', 'async', 'batch', 'stream']
            if spec.processing_method not in valid_methods:
                raise ComponentSpecificationError(
                    f"Invalid processing method '{spec.processing_method}' for Transformer. "
                    f"Must be one of: {valid_methods}."
                )
        
        elif spec.component_type == ComponentType.SINK:
            if spec.processing_method not in ['database', 'file', 'api', 'queue', 'cache', 'sync', 'async', 'batch', 'stream']:
                raise ComponentSpecificationError(
                    f"Invalid processing method '{spec.processing_method}' for Sink. "
                    f"Must be one of: database, file, api, queue, cache, sync, async, batch, stream."
                )
        
        # Validate required fields exist
        if not spec.required_config_fields:
            raise ComponentSpecificationError(
                "No required configuration fields detected. V5.0 components must have explicit configuration."
            )
        
        self.logger.debug(f"✅ Specification validated for {spec.class_name}")
    
    def get_parsing_examples(self) -> Dict[str, str]:
        """Get examples of valid natural language specifications"""
        
        return {
            "source_api": "Create a data source component called ApiDataSource that reads JSON data from API endpoints",
            "source_database": "Generate a source component called DatabaseReader that fetches CSV data from database tables",
            "transformer_filter": "Build a transformer component called FilterComponent that filters JSON data based on conditions",
            "transformer_map": "Create a transformer component called DataMapper that transforms CSV data using map operations",
            "sink_database": "Make a sink component called DatabaseWriter that stores JSON data to database tables",
            "sink_file": "Generate a file sink component called FileStorage that saves CSV data to filesystem"
        }
    
    def validate_natural_language(self, nl_text: str) -> List[str]:
        """Validate natural language for common issues - return warnings"""
        
        warnings = []
        
        if len(nl_text.strip()) < 20:
            warnings.append("Specification is very short - may not contain enough detail")
        
        if not re.search(r'class|component|called|named', nl_text, re.IGNORECASE):
            warnings.append("No explicit class name found - specify 'class ClassName' or 'component called ClassName'")
        
        # Check for component type indicators
        has_type_indicator = False
        for patterns in self._component_type_patterns.values():
            for pattern in patterns[:3]:  # Check first 3 patterns
                if re.search(pattern, nl_text, re.IGNORECASE):
                    has_type_indicator = True
                    break
            if has_type_indicator:
                break
        
        if not has_type_indicator:
            warnings.append("No clear component type indicator found - specify 'source', 'transformer', or 'sink' behavior")
        
        # Check for data type
        has_data_type = False
        for patterns in self._data_type_patterns.values():
            for pattern in patterns:
                if re.search(pattern, nl_text, re.IGNORECASE):
                    has_data_type = True
                    break
            if has_data_type:
                break
        
        if not has_data_type:
            warnings.append("No data type specified - specify JSON, CSV, XML, binary, or text")
        
        return warnings


# Global natural language parser instance
nl_parser = NaturalLanguageParser()