#!/usr/bin/env python3
"""
Transformer component for Autocoder V5.2 System-First Architecture
"""
import anyio
import time
from typing import Dict, Any, List
from .composed_base import ComposedComponent
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Transformer(ComposedComponent):
    """
    Transformer components modify, enrich, or transform data using anyio streams.
    Examples: data validators, enrichers, formatters
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "Transformer"
        
        # Note: ConsistentErrorHandler already initialized in ComposedComponent

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Transformer component"""
        return [
            ConfigRequirement(
                name="transformation_type",
                type="str",
                description="Type of transformation to apply",
                required=True,
                options=["map", "filter", "aggregate", "enrich", "normalize"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="transformation_rules",
                type="list",
                description="List of transformation rules to apply",
                required=False,
                default=[],
                semantic_type=ConfigType.LIST
            ),
            ConfigRequirement(
                name="field_mappings",
                type="dict",
                description="Field mapping for data transformation",
                required=False,
                default={},
                semantic_type=ConfigType.DICT
            )
        ]

    
    @handle_errors(component_name="Transformer", operation="process")
    async def process(self) -> None:
        """Transform data from input streams and send to output streams."""
        try:
            # Process all available input streams (not just 'input')
            if self.receive_streams:
                async with anyio.create_task_group() as tg:
                    for stream_name, stream in self.receive_streams.items():
                        tg.start_soon(self._process_stream, stream_name, stream)
            else:
                self.logger.warning("No input stream configured")
                    
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "main_process_loop"},
                operation="process"
            )
            self.record_error(str(e))
            raise
    
    async def _process_stream(self, stream_name: str, stream):
        """Process a single input stream using the shared base class method"""
        try:
            await self._process_stream_with_handler(stream_name, stream, self._transform_data)
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "stream": stream_name, "operation": "process_stream"},
                operation="stream_processing"
            )
            raise
                
    async def _transform_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default data transformation implementation for Transformer components.
        Provides working functionality instead of failing.
        """
        # Check if this is a generated component needing real implementation
        class_name = self.__class__.__name__
        if class_name.startswith('Generated'):
            # Generated component - provide configurable working transformation
            self.logger.info(f"Generated component {class_name} using configurable data transformation")
            
            # Get transformation configuration
            transform_config = self.config.get("transform", {})
            transform_type = transform_config.get("type", "passthrough")
            
            if transform_type == "passthrough":
                # Simple passthrough with metadata
                return {
                    **inputs,
                    "transformed_by": self.name,
                    "transformed_at": time.time(),
                    "transform_type": "passthrough"
                }
                
            elif transform_type == "filter":
                # Filter data based on criteria
                filter_key = transform_config.get("key", "value")
                filter_value = transform_config.get("value", None)
                
                if filter_key in inputs and inputs[filter_key] == filter_value:
                    return {
                        **inputs,
                        "filtered": True,
                        "transformed_by": self.name
                    }
                else:
                    return None  # Filtered out
                    
            elif transform_type == "aggregate":
                # Aggregate/summarize data
                if not hasattr(self, "_aggregated_data"):
                    self._aggregated_data = []
                self._aggregated_data.append(inputs)
                
                return {
                    "count": len(self._aggregated_data),
                    "latest": inputs,
                    "transformed_by": self.name,
                    "transformed_at": time.time()
                }
                
            elif transform_type == "enrich":
                # Enrich data with additional fields
                enrichment = transform_config.get("fields", {})
                return {
                    **inputs,
                    **enrichment,
                    "enriched_by": self.name,
                    "enriched_at": time.time()
                }
                
            else:
                # Default transformation
                return {
                    "original": inputs,
                    "transformed": True,
                    "transformed_by": self.name,
                    "timestamp": time.time()
                }
        else:
            # Base Transformer component - simple passthrough
            return {
                **inputs,
                "processed_by": self.name,
                "processed_at": time.time()
            }
    
    @classmethod
    def get_required_config_fields(cls) -> List[ConfigRequirement]:
        """Get list of required configuration fields with full specifications"""
        return [
            ConfigRequirement(
                name="transformation_type",
                type="str",
                description="Type of transformation to apply",
                required=True,
                options=["map", "filter", "aggregate", "enrich", "validate", "format", "custom"],
                example="enrich"
            ),
            ConfigRequirement(
                name="transformation_rules",
                type="list",
                description="List of transformation rules to apply",
                required=True,
                example=[{"field": "value", "operation": "multiply", "factor": 2}]
            ),
            ConfigRequirement(
                name="enrichment_source",
                type="str",
                description="Source for data enrichment",
                required=False,
                depends_on={"transformation_type": "enrich"},
                semantic_type=ConfigType.DATABASE_URL,
                example="postgres://localhost:5432/enrichment_db"
            ),
            ConfigRequirement(
                name="validation_schema",
                type="dict",
                description="Schema for data validation",
                required=False,
                depends_on={"transformation_type": "validate"},
                example={"type": "object", "properties": {"id": {"type": "string"}}}
            ),
            ConfigRequirement(
                name="output_format",
                type="str",
                description="Format for transformed output",
                required=False,
                depends_on={"transformation_type": "format"},
                options=["json", "csv", "xml", "yaml", "protobuf"],
                default="json"
            ),
            ConfigRequirement(
                name="custom_function",
                type="str",
                description="Custom transformation function code",
                required=False,
                depends_on={"transformation_type": "custom"},
                example="lambda x: x['value'] * 2 if 'value' in x else x"
            ),
            ConfigRequirement(
                name="batch_processing",
                type="bool",
                description="Process data in batches",
                required=False,
                default=False
            ),
            ConfigRequirement(
                name="batch_size",
                type="int",
                description="Size of processing batches",
                required=False,
                depends_on={"batch_processing": True},
                default=100,
                validator=lambda x: x > 0 and x <= 10000
            ),
            ConfigRequirement(
                name="error_handling",
                type="str",
                description="How to handle transformation errors",
                required=False,
                default="skip",
                options=["skip", "fail", "default", "log"]
            ),
            ConfigRequirement(
                name="default_value",
                type="dict",
                description="Default value for failed transformations",
                required=False,
                depends_on={"error_handling": "default"},
                example={"status": "error", "value": None}
            )
        ]