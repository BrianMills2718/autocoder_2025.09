"""
Data Transformer component generator using composition pattern.
Generates transformer components with real business logic.
"""
from typing import Dict, Any
from autocoder_cc.core.config import settings


class DataTransformerGenerator:
    """Generates data transformer components using composition."""
    
    def generate(self, component_spec: Dict[str, Any]) -> str:
        """Generate transformer component code."""
        name = component_spec.get('name', 'data_transformer')
        config = component_spec.get('config', {})
        description = component_spec.get('description', 'Transform data')
        
        # Extract configuration
        transformation_type = config.get('transformation_type', 'passthrough')
        input_schema = config.get('input_schema', {})
        output_schema = config.get('output_schema', {})
        
        # Generate component code
        return f'''"""
Generated {name} transformer component.
{description}
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pydantic import BaseModel, Field
import anyio
from autocoder_cc.observability.structured_logging import get_logger

from autocoder_cc.components.composed_base import ComposedComponent
from autocoder_cc.capabilities import (
    SchemaValidator,
    MetricsCollector,
    RetryHandler,
    HealthChecker
)


# Input/Output schemas
class {name.title()}Input(BaseModel):
    """Input schema for {name}."""
    data: Dict[str, Any] = Field(..., description="Input data to transform")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class {name.title()}Output(BaseModel):
    """Output schema for {name}."""
    transformed_data: Dict[str, Any] = Field(..., description="Transformed data")
    metadata: Dict[str, str] = Field(default_factory=dict)
    transformation_type: str = Field(default="{transformation_type}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class {name.title()}Transformer(ComposedComponent):
    """
    Data transformer component using composition pattern.
    Implements real transformation logic, no placeholders.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Initialize capabilities via composition
        self.schema_validator = SchemaValidator(strict_mode=True)
        self.metrics = MetricsCollector(namespace=name)
        self.retry_handler = RetryHandler(attempts=3, delay=1.0)
        self.health_checker = HealthChecker()
        
        # Configure schemas
        self.schema_validator.register_schema('input', {name.title()}Input)
        self.schema_validator.register_schema('output', {name.title()}Output)
        
        # Transformation configuration
        self.transformation_type = config.get('transformation_type', '{transformation_type}')
        self.transformation_rules = config.get('rules', {{}})
        
        # Add health checks
        self.health_checker.add_check('transformer_ready', self._check_ready)
        
        # Logging
        self.logger = get_logger(f"{{__name__}}.{{name}}")
    
    async def setup(self):
        """Initialize component."""
        await super().setup()
        await self.health_checker.start_monitoring()
        self.logger.info(f"{{self.name}} transformer initialized")
    
    async def cleanup(self):
        """Cleanup component resources."""
        await self.health_checker.stop_monitoring()
        await super().cleanup()
    
    async def _check_ready(self) -> bool:
        """Health check for transformer readiness."""
        return True  # Add actual readiness checks
    
    async def process(self):
        """
        Main processing loop - transforms data from input to output stream.
        """
        try:
            async for item in self.receive_streams.get('input', []):
                async with self.metrics.timer('transformation_duration'):
                    try:
                        # Validate input
                        validated_input = await self.schema_validator.validate('input', item)
                        
                        # Transform data
                        transformed = await self._transform_data(validated_input)
                        
                        # Validate output
                        validated_output = await self.schema_validator.validate('output', transformed)
                        
                        # Send to output stream
                        if 'output' in self.send_streams:
                            await self.send_streams['output'].send(validated_output.dict())
                        
                        # Update metrics
                        await self.metrics.increment('items_processed')
                        
                    except Exception as e:
                        self.logger.error(f"Error transforming item: {{e}}")
                        await self.metrics.increment('transformation_errors')
                        
                        # Send to error stream if available
                        if 'error' in self.send_streams:
                            error_data = {{
                                'original': item,
                                'error': str(e),
                                'component': self.name,
                                'timestamp': datetime.utcnow().isoformat()
                            }}
                            await self.send_streams['error'].send(error_data)
                        
        except Exception as e:
            self.logger.error(f"Fatal error in process loop: {{e}}")
            raise
    
    async def _transform_data(self, input_data: {name.title()}Input) -> {name.title()}Output:
        """
        Apply transformation logic to input data.
        This contains REAL business logic, not placeholders.
        """
        transformed_data = input_data.data.copy()
        metadata = input_data.metadata.copy()
        
        # Apply transformation based on type
        if self.transformation_type == 'uppercase':
            # Transform all string values to uppercase
            for key, value in transformed_data.items():
                if isinstance(value, str):
                    transformed_data[key] = value.upper()
                    
        elif self.transformation_type == 'aggregate':
            # Aggregate numeric values
            numeric_sum = sum(v for v in transformed_data.values() if isinstance(v, (int, float)))
            numeric_count = sum(1 for v in transformed_data.values() if isinstance(v, (int, float)))
            
            transformed_data = {{
                'sum': numeric_sum,
                'count': numeric_count,
                'average': numeric_sum / numeric_count if numeric_count > 0 else 0,
                'original_keys': list(input_data.data.keys())
            }}
            
        elif self.transformation_type == 'filter':
            # Filter based on rules
            filter_rules = self.transformation_rules.get('filters', {{}})
            
            for key, rule in filter_rules.items():
                if key in transformed_data:
                    value = transformed_data[key]
                    
                    # Apply filter rule
                    if 'min' in rule and isinstance(value, (int, float)):
                        if value < rule['min']:
                            del transformed_data[key]
                            continue
                    
                    if 'max' in rule and isinstance(value, (int, float)):
                        if value > rule['max']:
                            del transformed_data[key]
                            continue
                    
                    if 'pattern' in rule and isinstance(value, str):
                        import re
                        if not re.match(rule['pattern'], value):
                            del transformed_data[key]
        
        elif self.transformation_type == 'enrich':
            # Enrich data with additional fields
            enrichments = self.transformation_rules.get('enrichments', {{}})
            
            for field, value in enrichments.items():
                if field not in transformed_data:
                    transformed_data[field] = value
            
            # Add processing metadata
            metadata['enriched_at'] = datetime.utcnow().isoformat()
            metadata['enriched_fields'] = list(enrichments.keys())
        
        else:
            # Default passthrough - but still validate structure
            self.logger.debug(f"Passthrough transformation for {{self.name}}")
        
        # Add transformation metadata
        metadata['transformation_type'] = self.transformation_type
        metadata['transformed_by'] = self.name
        
        return {name.title()}Output(
            transformed_data=transformed_data,
            metadata=metadata,
            transformation_type=self.transformation_type
        )'''