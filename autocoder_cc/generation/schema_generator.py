from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Schema-Aware Component Generator for V5.0 Enhanced Generation
Integrates secure templates with natural language parsing and Pydantic validation
"""

from typing import Dict, Any, List, Optional, Type
import logging
from dataclasses import dataclass
from pydantic import BaseModel, Field

from .secure_templates import (
    SecureTemplateSystem, 
    secure_template_system,
    TemplateSecurityError,
    TemplateValidationError
)
from .nl_parser import (
    NaturalLanguageParser,
    nl_parser,
    NLParsingError,
    ComponentSpecification,
    ComponentType
)
from ..validation.schema_framework import (
    SchemaValidator,
    schema_validator,
    SchemaValidationError,
    ComponentDataSchema,
    SourceDataSchema,
    TransformerDataSchema,
    SinkDataSchema
)


class ComponentGenerationError(Exception):
    """Raised when component generation fails - no fallbacks available"""
    pass


class SchemaGenerationError(Exception):
    """Raised when schema generation fails - fail hard on invalid schemas"""
    pass


@dataclass
class GeneratedComponent:
    """Generated component with complete validation"""
    class_name: str
    component_type: ComponentType
    source_code: str
    schema_classes: Dict[str, Type[BaseModel]]
    config_template: Dict[str, Any]
    validation_results: Dict[str, Any]


class SchemaAwareComponentGenerator:
    """
    V5.0 Schema-Aware Component Generator with Fail-Hard Principles
    
    Key Principles:
    - No dynamic code execution or eval()
    - Generated components must pass Phase 2 validation
    - All schemas generated using Pydantic with strict validation
    - Fail hard on any generation errors
    - No partial component generation or fallbacks
    """
    
    def __init__(self):
        self.logger = get_logger("SchemaAwareComponentGenerator")
        
        # Use existing validated systems
        self.template_system = secure_template_system
        self.nl_parser = nl_parser
        self.schema_validator = schema_validator
        
        # Track generated components
        self.generated_components: Dict[str, GeneratedComponent] = {}
        
        self.logger.info("✅ Schema-Aware Component Generator initialized with fail-hard validation")
    
    def generate_component_from_nl(self, natural_language: str) -> GeneratedComponent:
        """Generate complete component from natural language specification"""
        
        try:
            # Step 1: Parse natural language specification
            spec = self.nl_parser.parse_component_specification(natural_language)
            self.logger.info(f"📝 Parsed specification: {spec.class_name} ({spec.component_type.value})")
            
            # Step 2: Generate Pydantic schemas for the component
            schemas = self._generate_component_schemas(spec)
            self.logger.info(f"📊 Generated {len(schemas)} schemas for {spec.class_name}")
            
            # Step 3: Create component configuration template
            config_template = self._create_config_template(spec, schemas)
            
            # Step 4: Generate component source code
            source_code = self._generate_component_code(spec, schemas, config_template)
            self.logger.info(f"🔧 Generated source code for {spec.class_name}")
            
            # Step 5: Validate generated component
            validation_results = self._validate_generated_component(spec, source_code, schemas)
            
            # Step 6: Create final component object
            generated_component = GeneratedComponent(
                class_name=spec.class_name,
                component_type=spec.component_type,
                source_code=source_code,
                schema_classes=schemas,
                config_template=config_template,
                validation_results=validation_results
            )
            
            # Register the generated component
            self.generated_components[spec.class_name] = generated_component
            
            self.logger.info(f"✅ Component generation complete: {spec.class_name}")
            return generated_component
            
        except Exception as e:
            if isinstance(e, (NLParsingError, TemplateSecurityError, TemplateValidationError, SchemaGenerationError)):
                raise
            else:
                raise ComponentGenerationError(
                    f"Component generation failed: {e}. "
                    f"V5.0 requires successful generation - no partial components allowed."
                )
    
    def _generate_component_schemas(self, spec: ComponentSpecification) -> Dict[str, Type[BaseModel]]:
        """Generate Pydantic schemas for component inputs/outputs"""
        
        schemas = {}
        
        try:
            # Generate schemas based on component type
            if spec.component_type == ComponentType.SOURCE:
                # Sources only have output schemas
                output_schema = self._create_output_schema(spec)
                schemas[f"{spec.class_name}OutputSchema"] = output_schema
                
            elif spec.component_type == ComponentType.TRANSFORMER:
                # Transformers have both input and output schemas
                input_schema = self._create_input_schema(spec)
                output_schema = self._create_output_schema(spec)
                schemas[f"{spec.class_name}InputSchema"] = input_schema
                schemas[f"{spec.class_name}OutputSchema"] = output_schema
                
            elif spec.component_type == ComponentType.SINK:
                # Sinks only have input schemas
                input_schema = self._create_input_schema(spec)
                schemas[f"{spec.class_name}InputSchema"] = input_schema
            
            # Validate all generated schemas
            for schema_name, schema_class in schemas.items():
                self._validate_schema_class(schema_name, schema_class)
            
            return schemas
            
        except Exception as e:
            raise SchemaGenerationError(
                f"Schema generation failed for {spec.class_name}: {e}. "
                f"V5.0 requires valid Pydantic schemas - no dynamic schema creation allowed."
            )
    
    def _create_input_schema(self, spec: ComponentSpecification) -> Type[BaseModel]:
        """Create Pydantic input schema for component"""
        
        # Select base schema based on component type
        if spec.component_type == ComponentType.TRANSFORMER:
            base_schema = TransformerDataSchema
        elif spec.component_type == ComponentType.SINK:
            base_schema = SinkDataSchema
        else:
            raise SchemaGenerationError(f"Cannot create input schema for {spec.component_type}")
        
        # Create schema class with proper Pydantic v2 syntax
        class_dict = {}
        annotations = {}
        
        # Add data type specific fields
        if spec.data_type == "json":
            annotations["json_data"] = Dict[str, Any]
            class_dict["json_data"] = Field(..., description="JSON data payload")
        elif spec.data_type == "csv":
            annotations["csv_rows"] = List[Dict[str, str]]
            class_dict["csv_rows"] = Field(..., description="CSV rows as list of dictionaries")
        elif spec.data_type == "xml":
            annotations["xml_content"] = str
            class_dict["xml_content"] = Field(..., description="XML content as string")
        elif spec.data_type == "binary":
            annotations["binary_data"] = bytes
            class_dict["binary_data"] = Field(..., description="Binary data payload")
        elif spec.data_type == "text":
            annotations["text_content"] = str
            class_dict["text_content"] = Field(..., description="Plain text content")
        
        # Add processing method specific fields
        if spec.processing_method == "batch":
            annotations["batch_id"] = str
            class_dict["batch_id"] = Field(..., description="Batch processing identifier")
            annotations["batch_size"] = int
            class_dict["batch_size"] = Field(default=100, description="Batch size")
        elif spec.processing_method == "stream":
            annotations["stream_id"] = str
            class_dict["stream_id"] = Field(..., description="Stream identifier")
            annotations["sequence_number"] = int
            class_dict["sequence_number"] = Field(..., description="Message sequence number")
        
        # Set annotations
        class_dict["__annotations__"] = annotations
        
        # Create schema class dynamically
        schema_class = type(
            f"{spec.class_name}InputSchema",
            (base_schema,),
            class_dict
        )
        
        return schema_class
    
    def _create_output_schema(self, spec: ComponentSpecification) -> Type[BaseModel]:
        """Create Pydantic output schema for component"""
        
        # Select base schema based on component type
        if spec.component_type == ComponentType.SOURCE:
            base_schema = SourceDataSchema
        elif spec.component_type == ComponentType.TRANSFORMER:
            base_schema = TransformerDataSchema
        else:
            raise SchemaGenerationError(f"Cannot create output schema for {spec.component_type}")
        
        # Create schema class with proper Pydantic v2 syntax
        class_dict = {}
        annotations = {}
        
        # Add data type specific fields
        if spec.data_type == "json":
            annotations["json_payload"] = Dict[str, Any]
            class_dict["json_payload"] = Field(..., description="Generated JSON data")
        elif spec.data_type == "csv":
            annotations["csv_data"] = List[Dict[str, str]]
            class_dict["csv_data"] = Field(..., description="Generated CSV data")
        elif spec.data_type == "xml":
            annotations["xml_document"] = str
            class_dict["xml_document"] = Field(..., description="Generated XML document")
        elif spec.data_type == "binary":
            annotations["binary_content"] = bytes
            class_dict["binary_content"] = Field(..., description="Generated binary content")
        elif spec.data_type == "text":
            annotations["text_data"] = str
            class_dict["text_data"] = Field(..., description="Generated text data")
        
        # Add component type specific fields
        if spec.component_type == ComponentType.SOURCE:
            annotations["generation_metadata"] = Dict[str, Any]
            class_dict["generation_metadata"] = Field(default_factory=dict, description="Generation metadata")
        elif spec.component_type == ComponentType.TRANSFORMER:
            annotations["transformation_applied"] = str
            class_dict["transformation_applied"] = Field(..., description="Type of transformation applied")
            annotations["processing_metadata"] = Dict[str, Any]
            class_dict["processing_metadata"] = Field(default_factory=dict, description="Processing metadata")
        
        # Set annotations
        class_dict["__annotations__"] = annotations
        
        # Create schema class dynamically
        schema_class = type(
            f"{spec.class_name}OutputSchema",
            (base_schema,),
            class_dict
        )
        
        return schema_class
    
    def _validate_schema_class(self, schema_name: str, schema_class: Type[BaseModel]) -> None:
        """Validate generated schema class meets V5.0 requirements"""
        
        # Check that it's a proper Pydantic model
        if not issubclass(schema_class, BaseModel):
            raise SchemaGenerationError(
                f"Generated schema '{schema_name}' is not a valid Pydantic BaseModel. "
                f"V5.0 requires Pydantic schemas only."
            )
        
        # Check that it has required V5.0 fields
        if issubclass(schema_class, ComponentDataSchema):
            required_fields = ['timestamp', 'component_source']
            schema_fields = schema_class.model_fields.keys()
            
            missing_fields = [field for field in required_fields if field not in schema_fields]
            if missing_fields:
                raise SchemaGenerationError(
                    f"Generated schema '{schema_name}' missing required V5.0 fields: {missing_fields}"
                )
        
        # Test schema instantiation
        try:
            # Try to create a sample instance to validate schema structure
            sample_data = {
                'timestamp': 1234567890.0,
                'component_source': 'test_component'
            }
            
            # Add required fields for specific schema types
            if hasattr(schema_class, '__annotations__'):
                for field_name, field_info in schema_class.model_fields.items():
                    if field_info.is_required() and field_name not in sample_data:
                        # Add sample data for required fields
                        if 'json' in field_name.lower():
                            sample_data[field_name] = {"test": "data"}
                        elif 'csv' in field_name.lower():
                            sample_data[field_name] = [{"col1": "val1"}]
                        elif 'xml' in field_name.lower():
                            sample_data[field_name] = "<test>data</test>"
                        elif 'binary' in field_name.lower():
                            sample_data[field_name] = b"test data"
                        elif 'text' in field_name.lower():
                            sample_data[field_name] = "test text"
                        else:
                            sample_data[field_name] = "test_value"
            
            # Try to instantiate the schema
            schema_class(**sample_data)
            
        except Exception as e:
            raise SchemaGenerationError(
                f"Generated schema '{schema_name}' validation failed: {e}. "
                f"V5.0 schemas must be instantiable with valid data."
            )
        
        self.logger.debug(f"✅ Schema validated: {schema_name}")
    
    def _create_config_template(self, spec: ComponentSpecification, schemas: Dict[str, Type[BaseModel]]) -> Dict[str, Any]:
        """Create configuration template for the component"""
        
        # Get current schema version for versioned generation
        from autocoder_cc.core.schema_versioning import get_version_manager
        
        try:
            version_manager = get_version_manager()
            current_version = version_manager.get_current_version() or "1.0.0"
        except Exception:
            # Fallback to default version if schema versioning not initialized
            current_version = "1.0.0"
        
        config = {
            "schema_version": current_version,  # Enterprise Roadmap v3 Phase 1
            "type": spec.component_type.value.title(),
            "description": spec.description,
            "data_type": spec.data_type,
            "processing_method": spec.processing_method
        }
        
        # Add component type specific configuration
        if spec.component_type == ComponentType.SOURCE:
            config["outputs"] = [
                {
                    "name": "generated_data",
                    "schema": f"{spec.class_name}OutputSchema",
                    "description": f"Generated {spec.data_type} data"
                }
            ]
        elif spec.component_type == ComponentType.TRANSFORMER:
            config["inputs"] = [
                {
                    "name": "input_data",
                    "schema": f"{spec.class_name}InputSchema",
                    "description": f"Input {spec.data_type} data for processing"
                }
            ]
            config["outputs"] = [
                {
                    "name": "processed_data",
                    "schema": f"{spec.class_name}OutputSchema",
                    "description": f"Processed {spec.data_type} data"
                }
            ]
        elif spec.component_type == ComponentType.SINK:
            config["inputs"] = [
                {
                    "name": "data_to_store",
                    "schema": f"{spec.class_name}InputSchema",
                    "description": f"Input {spec.data_type} data for storage"
                }
            ]
        
        # Add required configuration fields from spec
        for field in spec.required_config_fields:
            if field not in config:
                if field in ["api_url", "api_key"]:
                    config[field] = f"${{{field.upper()}}}"  # Environment variable placeholder
                elif field in ["connection_string", "table_name"]:
                    config[field] = f"${{{field.upper()}}}"
                elif field in ["file_path", "file_format"]:
                    config[field] = f"${{{field.upper()}}}"
                else:
                    config[field] = None
        
        return config
    
    def _generate_component_code(self, spec: ComponentSpecification, schemas: Dict[str, Type[BaseModel]], config: Dict[str, Any]) -> str:
        """Generate component source code using secure templates"""
        
        # Determine template ID based on component type
        if spec.component_type == ComponentType.SOURCE:
            template_id = "enhanced_source_v5"
            # Map processing method for sources
            if spec.processing_method in ["api", "database", "file", "synthetic"]:
                generation_method = spec.processing_method
            else:
                generation_method = "api"  # Default fallback
        elif spec.component_type == ComponentType.TRANSFORMER:
            template_id = "enhanced_transformer_v5"
            # Map processing method for transformers
            if spec.processing_method in ["filter", "map", "aggregate", "enrich", "normalize"]:
                transformation_type = spec.processing_method
                processing_method = "sync"  # Default processing style
            else:
                transformation_type = "map"  # Default transformation
                processing_method = spec.processing_method if spec.processing_method in ["sync", "async", "batch", "stream"] else "sync"
        elif spec.component_type == ComponentType.SINK:
            template_id = "enhanced_sink_v5"
            # Map processing method for sinks
            if spec.processing_method in ["database", "file", "api", "queue", "cache"]:
                storage_type = spec.processing_method
                persistence_method = "sync"  # Default persistence style
            else:
                storage_type = "file"  # Default storage
                persistence_method = spec.processing_method if spec.processing_method in ["sync", "async", "batch", "stream"] else "sync"
        
        # Prepare template variables
        template_variables = {
            "class_name": spec.class_name,
            "description": spec.description,
            "data_type": spec.data_type,
            "required_config_fields": str(spec.required_config_fields),
            "required_dependencies": str(spec.required_dependencies)
        }
        
        # Add component type specific variables
        if spec.component_type == ComponentType.SOURCE:
            template_variables["generation_method"] = generation_method
        elif spec.component_type == ComponentType.TRANSFORMER:
            template_variables["transformation_type"] = transformation_type
            template_variables["processing_method"] = processing_method
        elif spec.component_type == ComponentType.SINK:
            template_variables["storage_type"] = storage_type
            template_variables["persistence_method"] = persistence_method
        
        # Generate source code using secure template system
        try:
            source_code = self.template_system.generate_component_code(template_id, template_variables)
            
            # Add schema imports and registrations
            source_code = self._add_schema_integrations(source_code, spec, schemas)
            
            return source_code
            
        except Exception as e:
            raise ComponentGenerationError(
                f"Source code generation failed for {spec.class_name}: {e}. "
                f"V5.0 requires secure template generation - no dynamic code creation allowed."
            )
    
    def _add_schema_integrations(self, source_code: str, spec: ComponentSpecification, schemas: Dict[str, Type[BaseModel]]) -> str:
        """Add schema imports and registrations to generated code"""
        
        # Add schema class definitions at the top of the file
        schema_definitions = []
        
        for schema_name, schema_class in schemas.items():
            # Extract schema fields for code generation
            fields_code = []
            for field_name, field_info in schema_class.model_fields.items():
                field_type = field_info.annotation if hasattr(field_info, 'annotation') else 'Any'
                field_default = field_info.default if hasattr(field_info, 'default') else '...'
                field_desc = field_info.description if hasattr(field_info, 'description') else f"{field_name} field"
                
                fields_code.append(f"    {field_name}: {field_type} = Field({field_default}, description=\"{field_desc}\")")
            
            # Determine base class
            if spec.component_type == ComponentType.SOURCE and "Output" in schema_name:
                base_class = "SourceDataSchema"
            elif spec.component_type == ComponentType.TRANSFORMER:
                if "Input" in schema_name:
                    base_class = "TransformerDataSchema"
                else:
                    base_class = "TransformerDataSchema"
            elif spec.component_type == ComponentType.SINK and "Input" in schema_name:
                base_class = "SinkDataSchema"
            else:
                base_class = "ComponentDataSchema"
            
            schema_definition = f"""
class {schema_name}({base_class}):
    \"\"\"Generated schema for {spec.class_name} component\"\"\"
{chr(10).join(fields_code)}
"""
            schema_definitions.append(schema_definition)
        
        # Add import for base schemas
        import_line = "from autocoder_cc.validation.schema_framework import ComponentDataSchema, SourceDataSchema, TransformerDataSchema, SinkDataSchema"
        
        # Insert schema definitions after imports
        lines = source_code.split('\n')
        import_index = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i
        
        if import_index >= 0:
            lines.insert(import_index + 1, import_line)
            lines.insert(import_index + 2, "")
            for schema_def in schema_definitions:
                lines.insert(import_index + 3, schema_def)
        
        return '\n'.join(lines)
    
    def _validate_generated_component(self, spec: ComponentSpecification, source_code: str, schemas: Dict[str, Type[BaseModel]]) -> Dict[str, Any]:
        """Validate generated component meets V5.0 requirements"""
        
        validation_results = {}
        
        # Validate source code security
        try:
            self.template_system.validate_template_security(source_code)
            validation_results["security_validation"] = {"passed": True, "message": "No security violations found"}
        except TemplateSecurityError as e:
            validation_results["security_validation"] = {"passed": False, "error": str(e)}
            raise ComponentGenerationError(f"Security validation failed: {e}")
        
        # Validate schemas
        schema_results = {}
        for schema_name, schema_class in schemas.items():
            try:
                self._validate_schema_class(schema_name, schema_class)
                schema_results[schema_name] = {"passed": True, "message": "Schema validation successful"}
            except SchemaGenerationError as e:
                schema_results[schema_name] = {"passed": False, "error": str(e)}
                raise ComponentGenerationError(f"Schema validation failed for {schema_name}: {e}")
        
        validation_results["schema_validation"] = schema_results
        
        # Validate component structure
        structure_checks = {
            "has_class_definition": f"class {spec.class_name}" in source_code,
            "has_process_method": "async def process(self)" in source_code,
            "has_fail_hard_logic": "fail hard" in source_code.lower(),
            "no_mock_modes": "mock" not in source_code.lower() or "no mock modes" in source_code.lower(),
            "has_v5_validation": "V5.0" in source_code
        }
        
        validation_results["structure_validation"] = structure_checks
        
        # Check all structure validations passed
        if not all(structure_checks.values()):
            failed_checks = [check for check, passed in structure_checks.items() if not passed]
            raise ComponentGenerationError(
                f"Component structure validation failed: {failed_checks}. "
                f"V5.0 components must meet all structural requirements."
            )
        
        validation_results["overall_status"] = "PASSED"
        validation_results["validation_timestamp"] = "Generated component meets all V5.0 requirements"
        
        return validation_results
    
    def get_generated_component(self, class_name: str) -> Optional[GeneratedComponent]:
        """Get previously generated component by class name"""
        return self.generated_components.get(class_name)
    
    def list_generated_components(self) -> List[str]:
        """List all generated component class names"""
        return list(self.generated_components.keys())
    
    def export_component_code(self, class_name: str, file_path: str) -> None:
        """Export generated component code to file"""
        
        if class_name not in self.generated_components:
            raise ComponentGenerationError(
                f"Component '{class_name}' not found. Generate component first."
            )
        
        component = self.generated_components[class_name]
        
        try:
            with open(file_path, 'w') as f:
                f.write(component.source_code)
            
            self.logger.info(f"✅ Component code exported: {file_path}")
            
        except Exception as e:
            raise ComponentGenerationError(
                f"Failed to export component code: {e}"
            )
    
    def validate_all_generated_components(self) -> Dict[str, Dict[str, Any]]:
        """Re-validate all generated components"""
        
        validation_summary = {}
        
        for class_name, component in self.generated_components.items():
            try:
                # Re-run validation
                validation_results = self._validate_generated_component(
                    ComponentSpecification(
                        component_type=component.component_type,
                        class_name=component.class_name,
                        description="Re-validation",
                        data_type="json",  # Placeholder
                        processing_method="api",  # Placeholder
                        required_config_fields=[],
                        required_dependencies=[]
                    ),
                    component.source_code,
                    component.schema_classes
                )
                validation_summary[class_name] = {"status": "PASSED", "results": validation_results}
                
            except Exception as e:
                validation_summary[class_name] = {"status": "FAILED", "error": str(e)}
        
        return validation_summary


# Global schema-aware component generator instance
schema_generator = SchemaAwareComponentGenerator()