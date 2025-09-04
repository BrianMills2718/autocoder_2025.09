#!/usr/bin/env python3
"""
Natural Language to Pydantic IntermediateSystem Translator using LLM
Takes a well-specified natural language request and generates a Pydantic IntermediateSystem model
"""
import os
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import json
from dotenv import load_dotenv
import asyncio

load_dotenv()
from autocoder_cc.blueprint_language.intermediate_format import IntermediateSystem, IntermediateComponent, IntermediatePort, IntermediateBinding
from autocoder_cc.core.config import settings
import time
import random
from autocoder_cc.blueprint_language.intermediate_to_blueprint_translator import IntermediateToBlueprintTranslator
from autocoder_cc.blueprint_language.intermediate_system_healer import heal_intermediate_system, IntermediateSystemHealer


class NaturalLanguageTranslationError(Exception):
    """Exception raised when natural language translation fails due to missing dependencies"""
    pass


class NaturalLanguageToPydanticTranslator:
    """
    Uses an LLM to convert natural language system descriptions into Pydantic IntermediateSystem models
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize the translator using UnifiedLLMProvider
        
        Args:
            llm_provider: Optional UnifiedLLMProvider instance.
                         If not provided, will create one automatically.
        """
        # Import UnifiedLLMProvider
        from autocoder_cc.llm_providers.unified_llm_provider import UnifiedLLMProvider
        
        if llm_provider:
            self.llm_provider = llm_provider
        else:
            # Create UnifiedLLMProvider with fallback enabled for robustness
            # It will handle API key detection and provider selection internally
            config = {'enable_fallback': True}
            self.llm_provider = UnifiedLLMProvider(config)
        
        # Store provider info for compatibility
        self.provider = self.llm_provider.fallback_sequence[0] if self.llm_provider.fallback_sequence else "gemini_2_5_flash"
        self.model = self.provider  # For backward compatibility
        
        self.blueprint_translator = IntermediateToBlueprintTranslator()
        
        # Error handling configuration (now handled by UnifiedLLMProvider)
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        
        # Load the IntermediateSystem schema for context
        schema_path = Path(__file__).parent / "intermediate_format.py"
        with open(schema_path, 'r') as f:
            self.intermediate_schema = f.read()
    
    def translate_to_intermediate(self, request: str) -> Tuple[IntermediateSystem, str]:
        """
        Translate natural language request to Pydantic IntermediateSystem model with structured NL output
        
        Args:
            request: Well-specified natural language description of the system
            
        Returns:
            Tuple of (IntermediateSystem model, Structured Natural Language output)
        """
        # System prompt that explains the task and provides context
        system_prompt = """You are an expert Autocoder System Architect AI. Your task is to interpret a well-specified natural language request for a distributed system and convert it into a structured Pydantic model representation called 'IntermediateSystem'.

CRITICAL ARCHITECTURAL REQUIREMENTS:
1. EVERY system MUST have at least one terminal component (Sink or Store)
2. EVERY Source MUST have a data path to at least one terminal component
3. NO component can be orphaned - all components MUST be connected via bindings
4. MINIMUM valid system: Source → [optional Transformer] → Sink/Store

CRITICAL SYSTEM NAMING RULES:
- Generate system names that EXACTLY match the user's request
- If user says "make me a to-do app", name it "todo_app_system" or similar
- If user says "build a chat application", name it "chat_application_system"
- NEVER use generic examples - ALWAYS match the user's specific domain

REQUIRED VALIDATION RULES YOUR SYSTEM MUST PASS:
✓ At least one data source (Source, EventSource, or APIEndpoint)
✓ At least one terminal component (Sink or Store) 
✓ Complete bindings connecting ALL components (no orphans)
✓ Every source must have a path to a terminal

COMMON VALID PATTERNS:
- API Pattern: APIEndpoint → Controller → Store
- Pipeline Pattern: Source → Transformer → Sink
- Service Pattern: APIEndpoint → Transformer → Store
- Simple Pattern: Source → Store

The IntermediateSystem model is defined as follows:

class IntermediateSystem(BaseModel):
    name: str # System name in snake_case (e.g., "my_new_system")
    description: str # Comprehensive architectural description
    version: str = "1.0.0" # System version (semver)
    components: list[IntermediateComponent] # List of system components
    bindings: list[IntermediateBinding] = [] # Data flow connections
    environment: Literal["development", "staging", "production"] = "development"

class IntermediateComponent(BaseModel):
    name: str # Component name in snake_case
    type: Literal["Source", "Transformer", "Accumulator", "Store", "Controller", "Sink", "StreamProcessor", "Model", "APIEndpoint", "Router"]
    description: str
    inputs: list[IntermediatePort] = []
    outputs: list[IntermediatePort] = []
    config: Dict[str, Any] = {}

class IntermediatePort(BaseModel):
    name: str # Port name in snake_case
    schema_type: Literal["object", "array", "string", "number", "integer", "boolean"]
    description: Optional[str] = None

class IntermediateBinding(BaseModel):
    from_component: str
    from_port: str
    to_component: str
    to_port: str

CRITICAL COMPONENT TYPE RULES:
Component types MUST be EXACTLY one of: "Source", "Transformer", "Accumulator", "Store", "Controller", "Sink", "StreamProcessor", "Model", "APIEndpoint", "Router"

CRITICAL SCHEMA CONSISTENCY RULES:
When creating bindings between components, you MUST ensure schema compatibility:

1. EXACT MATCH RULE: If you create a binding from ComponentA.output to ComponentB.input, then:
   - ComponentA.output.schema_type MUST be compatible with ComponentB.input.schema_type
   - Compatible means: same type OR the receiving port uses "object" (which can accept anything)

2. COMMON DATA FLOW PATTERNS:
   - Controller → Store: If Controller outputs business objects (schema_type: "object"), Store MUST accept "object"
   - APIEndpoint → Controller: Both should use "object" for request/response data
   - Source → Transformer: Match the data type (if Source outputs "array", Transformer accepts "array")
   - Transformer → Sink/Store: Output and input types must match

3. SCHEMA TYPE GUIDELINES:
   - "object": Use for complex business data (users, tasks, orders, etc.)
   - "integer": Use for IDs, counts, quantities
   - "string": Use for text, names, messages
   - "array": Use for collections of items
   - "boolean": Use for flags, status indicators
   - "number": Use for measurements, prices, decimals

4. BINDING VALIDATION BEFORE CREATION:
   Before adding any binding, verify:
   - Does from_component have an output port named from_port? 
   - Does to_component have an input port named to_port?
   - Are their schema_types compatible?
   - If not, adjust the port schema_types to ensure compatibility

COMPONENT-SPECIFIC PORT PATTERNS:
- APIEndpoint: inputs=[{name:"request", schema_type:"object"}], outputs=[{name:"response", schema_type:"object"}]
- Controller: inputs=[{name:"input", schema_type:"object"}], outputs=[{name:"output", schema_type:"object"}]
- Store: inputs=[{name:"data", schema_type:"object"}], outputs=[] (no outputs!)
- Sink: inputs=[{name:"input", schema_type:<match_source>}], outputs=[] (no outputs!)
- Transformer: inputs=[{name:"input", schema_type:<match_source>}], outputs=[{name:"output", schema_type:<match_target>}]

CRITICAL BINDING RULES:
- Bindings MUST connect from an OUTPUT port of one component to an INPUT port of another
- Store and Sink components have NO output ports (they are terminal)
- Source components have NO input ports (they generate data)
- APIEndpoint.request is an external entry point - do NOT create bindings TO it

EXAMPLE OF MINIMUM VALID SYSTEM:
{
  "name": "minimal_data_pipeline",
  "components": [
    {
      "name": "data_source",
      "type": "Source",
      "outputs": [{"name": "output", "schema_type": "object"}]
    },
    {
      "name": "data_store", 
      "type": "Store",
      "inputs": [{"name": "input", "schema_type": "object"}]
    }
  ],
  "bindings": [
    {
      "from_component": "data_source",
      "from_port": "output",
      "to_component": "data_store",
      "to_port": "input"
    }
  ]
}

VALIDATION CHECKLIST BEFORE RETURNING:
☐ Does the system have at least one terminal component (Sink/Store)?
☐ Are all sources connected to terminals via bindings?
☐ Are there any orphaned components with no connections?
☐ Do all bindings reference existing component ports?

Before returning your response, verify:
1. All component names match the user's domain (not generic examples)
2. All bindings connect existing ports
3. All connected ports have compatible schema_types
4. No bindings FROM components without outputs (Store, Sink)
5. No bindings TO APIEndpoint.request

Return ONLY the JSON object, no markdown formatting, no explanations.

CRITICAL JSON FORMAT:
Ports must be objects with name, schema_type, and description fields:
{
  "name": "port_name",
  "schema_type": "object",  // MUST match connected ports!
  "description": "Port description"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request}
        ]

        try:
            # Use standard completion and parse JSON manually
            # OpenAI's structured outputs has issues with Dict[str, Any] fields
            model = settings.get_llm_model()
            
            # Build parameters
            completion_params = {
                "model": model,
                "messages": messages
            }
            
            # Handle different parameter names for different models
            if model.startswith("o3") or model.startswith("o4"):
                # o3/o4 models support json_object response format but not temperature
                completion_params["response_format"] = {"type": "json_object"}
            elif model.startswith("gemini"):
                # Gemini models don't support temperature parameter
                # Add instruction to return JSON in the message
                messages[-1]["content"] += "\n\nIMPORTANT: Return ONLY valid JSON, no other text."
            elif model.startswith("gpt-4-turbo") or model.startswith("gpt-3.5-turbo"):
                # Newer models support both
                completion_params["response_format"] = {"type": "json_object"}
                completion_params["temperature"] = 0.1
            else:
                # Older models like gpt-4 don't support response_format
                completion_params["temperature"] = 0.1
                # Add instruction to return JSON in the message
                messages[-1]["content"] += "\n\nIMPORTANT: Return ONLY valid JSON, no other text."
            
            response = self._call_llm_with_retries(completion_params)

            if response.choices[0].message.refusal:
                # Handle model refusal for safety reasons
                print(f"Model refused to respond: {response.choices[0].message.refusal}")
                raise Exception(f"LLM refusal: {response.choices[0].message.refusal}")
            
            # Parse the JSON response - handle cases where response contains both text and JSON
            json_content = response.choices[0].message.content
            
            # Try to extract JSON from the response (it might be wrapped in markdown or other text)
            import re
            
            # First try to parse as pure JSON
            try:
                intermediate_data = json.loads(json_content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_content, re.DOTALL)
                if json_match:
                    intermediate_data = json.loads(json_match.group(1))
                else:
                    # Try to find JSON object in the text
                    json_match = re.search(r'(\{.*\})', json_content, re.DOTALL)
                    if json_match:
                        intermediate_data = json.loads(json_match.group(1))
                    else:
                        # Last resort: assume the entire content is JSON
                        intermediate_data = json.loads(json_content)
            
            # CRITICAL FIX: Generate bindings if they are missing or insufficient
            if 'bindings' not in intermediate_data or len(intermediate_data.get('bindings', [])) == 0:
                print(f"⚠️ No bindings generated by LLM, generating them automatically...")
                intermediate_data['bindings'] = self._generate_bindings(intermediate_data.get('components', []))
                print(f"   Generated {len(intermediate_data['bindings'])} bindings")
            
            # Fix common casing issues from LLMs
            if 'components' in intermediate_data:
                for component in intermediate_data['components']:
                    if 'type' in component and isinstance(component['type'], str):
                        # Map lowercase to correct casing
                        type_map = {
                            'source': 'Source',
                            'transformer': 'Transformer',
                            'accumulator': 'Accumulator',
                            'store': 'Store',
                            'controller': 'Controller',
                            'sink': 'Sink',
                            'streamprocessor': 'StreamProcessor',
                            'model': 'Model',
                            'apiendpoint': 'APIEndpoint',
                            'api_endpoint': 'APIEndpoint',
                            'router': 'Router'
                        }
                        original_type = component['type']
                        lower_type = component['type'].lower()
                        if lower_type in type_map:
                            component['type'] = type_map[lower_type]
                            print(f"   Fixed component type: '{original_type}' → '{component['type']}'")
            
            # Try to create intermediate system, with self-healing if validation fails
            try:
                intermediate_system = IntermediateSystem(**intermediate_data)
            except Exception as validation_error:
                print(f"⚠️ Initial validation failed, applying self-healing...")
                print(f"   Validation error: {str(validation_error)[:100]}...")
                
                # Apply self-healing to fix architectural issues
                
                # Create a raw system object without Pydantic validation for healing
                print(f"   Building raw system for healing...")
                
                # Create components manually without validation
                temp_components = []
                for comp_data in intermediate_data.get('components', []):
                    try:
                        # Build ports manually
                        inputs = []
                        for port_data in comp_data.get('inputs', []):
                            # Create port object manually
                            port = type('IntermediatePort', (), {
                                'name': port_data.get('name', ''),
                                'schema_type': port_data.get('schema_type', 'object'),
                                'description': port_data.get('description', ''),
                                'required': port_data.get('required', True)
                            })()
                            inputs.append(port)
                        
                        outputs = []
                        for port_data in comp_data.get('outputs', []):
                            port = type('IntermediatePort', (), {
                                'name': port_data.get('name', ''),
                                'schema_type': port_data.get('schema_type', 'object'),
                                'description': port_data.get('description', ''),
                                'required': port_data.get('required', True)
                            })()
                            outputs.append(port)
                        
                        # Create component manually
                        comp = type('IntermediateComponent', (), {
                            'name': comp_data.get('name', f'component_{len(temp_components)}'),
                            'type': comp_data.get('type', 'Transformer'),
                            'description': comp_data.get('description', ''),
                            'inputs': inputs,
                            'outputs': outputs,
                            'config': comp_data.get('config', comp_data.get('configuration', {}))
                        })()
                        temp_components.append(comp)
                        
                    except Exception as e:
                        print(f"   Skipping invalid component: {e}")
                        continue
                
                # Create bindings manually
                temp_bindings = []
                for bind_data in intermediate_data.get('bindings', []):
                    try:
                        binding = type('IntermediateBinding', (), {
                            'from_component': bind_data.get('from_component', ''),
                            'from_port': bind_data.get('from_port', ''),
                            'to_component': bind_data.get('to_component', ''),
                            'to_port': bind_data.get('to_port', '')
                        })()
                        temp_bindings.append(binding)
                        
                    except Exception as e:
                        print(f"   Skipping invalid binding: {e}")
                        continue
                
                # Create raw system object for healing
                temp_system = type('IntermediateSystem', (), {
                    'name': intermediate_data.get('name', 'generated_system'),
                    'description': intermediate_data.get('description', 'Generated system'),
                    'version': intermediate_data.get('version', '1.0.0'),
                    'components': temp_components,
                    'bindings': temp_bindings,
                    'environment': intermediate_data.get('environment', 'development')
                })()
                
                # Debug: Show bindings before healing
                print(f"\n   DEBUG: Bindings BEFORE healing:")
                for binding in temp_bindings:
                    print(f"      - {binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}")
                
                # Debug: Show Store components before healing
                store_components = [comp for comp in temp_components if comp.type == 'Store']
                if store_components:
                    print(f"\n   DEBUG: Store components BEFORE healing:")
                    for store in store_components:
                        print(f"      - {store.name} (type: {store.type})")
                        print(f"        Inputs: {[p.name for p in store.inputs]}")
                        print(f"        Outputs: {[p.name for p in store.outputs]}")
                        # Find bindings FROM this Store
                        store_output_bindings = [b for b in temp_bindings if b.from_component == store.name]
                        if store_output_bindings:
                            print(f"        OUTPUT bindings FROM this Store:")
                            for b in store_output_bindings:
                                print(f"          - {b.from_component}.{b.from_port} → {b.to_component}.{b.to_port}")
                
                # Apply healing
                print(f"\n   Applying healing operations...")
                healing_result = heal_intermediate_system(temp_system)
                
                if healing_result.success and healing_result.healed_system:
                    print(f"✅ Self-healing successful!")
                    print(f"   Operations performed: {len(healing_result.operations_performed)}")
                    # Show ALL operations for debugging, especially binding_removal operations
                    for i, op in enumerate(healing_result.operations_performed):
                        print(f"   {i+1}. {op.operation_type}: {op.description}")
                        if op.before_value:
                            print(f"      Before: {op.before_value}")
                        if op.after_value:
                            print(f"      After: {op.after_value}")
                    
                    # Debug: Show bindings AFTER healing
                    print(f"\n   DEBUG: Bindings AFTER healing:")
                    for binding in healing_result.healed_system.bindings:
                        print(f"      - {binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}")
                    
                    # Debug: Show Store components AFTER healing
                    healed_stores = [comp for comp in healing_result.healed_system.components if comp.type == 'Store']
                    if healed_stores:
                        print(f"\n   DEBUG: Store components AFTER healing:")
                        for store in healed_stores:
                            print(f"      - {store.name} (type: {store.type})")
                            print(f"        Inputs: {[p.name for p in store.inputs]}")
                            print(f"        Outputs: {[p.name for p in store.outputs]}")
                            # Find bindings FROM this Store
                            store_output_bindings = [b for b in healing_result.healed_system.bindings if b.from_component == store.name]
                            if store_output_bindings:
                                print(f"        OUTPUT bindings FROM this Store (SHOULD BE NONE!):")
                                for b in store_output_bindings:
                                    print(f"          - {b.from_component}.{b.from_port} → {b.to_component}.{b.to_port}")
                    
                    # Convert healed system back to proper Pydantic objects
                    print(f"\n   Converting healed system to Pydantic format...")
                    try:
                        healed = healing_result.healed_system
                        
                        # Create proper Pydantic components
                        pydantic_components = []
                        for comp in healed.components:
                            # Convert ports to proper Pydantic objects
                            pydantic_inputs = [IntermediatePort(
                                name=port.name,
                                schema_type=port.schema_type,
                                description=getattr(port, 'description', ''),
                                required=getattr(port, 'required', True)
                            ) for port in comp.inputs]
                            
                            pydantic_outputs = [IntermediatePort(
                                name=port.name,
                                schema_type=port.schema_type,
                                description=getattr(port, 'description', ''),
                                required=getattr(port, 'required', True)
                            ) for port in comp.outputs]
                            
                            pydantic_comp = IntermediateComponent(
                                name=comp.name,
                                type=comp.type,
                                description=comp.description,
                                inputs=pydantic_inputs,
                                outputs=pydantic_outputs,
                                config=getattr(comp, 'config', {})
                            )
                            pydantic_components.append(pydantic_comp)
                        
                        # Create proper Pydantic bindings
                        print(f"\n   DEBUG: Converting {len(healed.bindings)} bindings to Pydantic format...")
                        pydantic_bindings = []
                        for binding in healed.bindings:
                            pydantic_binding = IntermediateBinding(
                                from_component=binding.from_component,
                                from_port=binding.from_port,
                                to_component=binding.to_component,
                                to_port=binding.to_port
                            )
                            pydantic_bindings.append(pydantic_binding)
                            print(f"      - Converted: {binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}")
                        
                        # Create final Pydantic system
                        intermediate_system = IntermediateSystem(
                            name=healed.name,
                            description=healed.description,
                            version=healed.version,
                            components=pydantic_components,
                            bindings=pydantic_bindings,
                            environment=healed.environment
                        )
                        
                        print(f"   ✅ Healed system successfully converted!")
                        
                        # Debug: Final check on Store bindings in the intermediate_system
                        print(f"\n   DEBUG: FINAL intermediate_system bindings:")
                        for binding in intermediate_system.bindings:
                            print(f"      - {binding.from_component}.{binding.from_port} → {binding.to_component}.{binding.to_port}")
                        
                        final_stores = [comp for comp in intermediate_system.components if comp.type == 'Store']
                        if final_stores:
                            print(f"\n   DEBUG: FINAL Store components:")
                            for store in final_stores:
                                invalid_bindings = [b for b in intermediate_system.bindings if b.from_component == store.name]
                                if invalid_bindings:
                                    print(f"      ❌ PROBLEM: Store '{store.name}' still has output bindings!")
                                    for b in invalid_bindings:
                                        print(f"         - {b.from_component}.{b.from_port} → {b.to_component}.{b.to_port}")
                                else:
                                    print(f"      ✅ Store '{store.name}' has no output bindings (correct)")
                        
                    except Exception as conversion_error:
                        print(f"   ❌ Failed to convert healed system: {conversion_error}")
                        raise validation_error
                else:
                    print(f"❌ Self-healing failed: {healing_result.remaining_errors}")
                    raise NaturalLanguageTranslationError(
                        f"Natural language translation requires LLM configuration: {validation_error}. "
                        f"Set OPENAI_API_KEY or ANTHROPIC_API_KEY. NO FALLBACK MODES AVAILABLE - this exposes real dependency issues."
                    )
            
            # Generate the Structured Natural Language Summary
            structured_nl_messages = [
                {"role": "system", "content": "Generate a human-readable summary of the following system using this format:\n\nGOAL: [Concise statement of system's primary goal]\nCOMPONENTS:\n- [Component Name]: [Type] - [Description]\nBINDINGS:\n- [From Component].[From Port] -> [To Component].[To Port]\nCONFIGURATION:\n- [Key]: [Value]"},
                {"role": "user", "content": f"Generate the structured natural language summary for this system:\n\n{intermediate_system.model_dump_json(indent=2)}"}
            ]
            
            # Use model from environment
            model = settings.get_llm_model()
            
            # Build parameters for structured NL generation
            nl_params = {
                "model": model,
                "messages": structured_nl_messages
            }
            
            # Handle different parameter names for different models
            if not model.startswith("o3") and not model.startswith("o4") and not model.startswith("gemini"):
                nl_params["temperature"] = 0.3
            
            # Use the same retry mechanism that handles Gemini
            structured_nl_response = self._call_llm_with_retries(nl_params)
            
            structured_nl_output = structured_nl_response.choices[0].message.content

            return intermediate_system, structured_nl_output

        except Exception as e:
            print(f"Error during LLM call: {e}")
            # FAIL HARD - no fallback to mock response allowed
            raise NaturalLanguageTranslationError(
                f"Natural language translation requires LLM configuration: {e}. "
                f"Set OPENAI_API_KEY or ANTHROPIC_API_KEY. "
                f"NO FALLBACK MODES AVAILABLE - this exposes real dependency issues."
            )
    
    def generate_full_blueprint(self, request: str) -> str:
        """
        Complete pipeline: Natural Language → IntermediateSystem → Blueprint YAML
        
        Args:
            request: Well-specified natural language description of the system
            
        Returns:
            Blueprint YAML string
        """
        intermediate_system, structured_nl = self.translate_to_intermediate(request)
        blueprint_yaml = self.blueprint_translator.translate(intermediate_system)
        
        # CRITICAL FIX: Add required schema_version and policy fields
        lines = blueprint_yaml.split('\n')
        
        # Check if schema_version exists
        has_schema_version = any('schema_version:' in line for line in lines)
        has_policy = any(line.strip().startswith('policy:') for line in lines)
        
        # Build the required top-level structure
        new_lines = []
        
        # Add schema_version at the very top if missing
        if not has_schema_version:
            new_lines.append('schema_version: "1.0.0"')
            new_lines.append('')  # Empty line for readability
        
        # Add policy block if missing
        if not has_policy:
            policy_block = """policy:
  security:
    encryption_at_rest: true
    encryption_in_transit: true
    authentication_required: true
  resource_limits:
    max_memory_per_component: "512Mi"
    max_cpu_per_component: "500m"
  validation:
    strict_mode: true"""
            new_lines.extend(policy_block.split('\n'))
            new_lines.append('')  # Empty line for readability
        
        # Add the rest of the blueprint
        new_lines.extend(lines)
        
        blueprint_yaml = '\n'.join(new_lines)
        
        return blueprint_yaml
    
    def _parse_llm_response(self, response: str) -> Tuple[IntermediateSystem, str]:
        """
        Parse LLM response to extract JSON model and structured NL
        
        Args:
            response: Raw LLM response containing JSON and structured text
            
        Returns:
            Tuple of (IntermediateSystem model, Structured Natural Language output)
        """
        # Simple parsing - in practice would be more robust
        lines = response.strip().split('\n')
        json_lines = []
        structured_lines = []
        in_json = False
        
        for line in lines:
            if line.strip().startswith('{'):
                in_json = True
            elif line.strip() == '}':
                json_lines.append(line)
                in_json = False
            elif in_json:
                json_lines.append(line)
            elif line.strip().startswith(('GOAL:', 'COMPONENTS:', 'BINDINGS:', 'CONFIGURATION:')):
                structured_lines.append(line)
        
        json_str = '\n'.join(json_lines)
        structured_nl = '\n'.join(structured_lines)
        
        # Parse and validate the JSON
        intermediate_data = json.loads(json_str)
        intermediate_system = IntermediateSystem(**intermediate_data)
        
        return intermediate_system, structured_nl
    
    def _generate_mock_intermediate(self, request: str) -> Tuple[IntermediateSystem, str]:
        """
        FAIL-HARD: Mock system generation is not allowed.
        This was a lazy fallback that masks real LLM dependency issues.
        """
        raise NaturalLanguageTranslationError(
            f"Mock system generation is not permitted in fail-hard mode. "
            f"This method was a lazy fallback that hides LLM dependency failures. "
            f"Configure OPENAI_API_KEY or ANTHROPIC_API_KEY for real system generation. "
            f"NO FALLBACK MODES AVAILABLE - this exposes real dependency issues."
        )
    
    def _generate_bindings(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate bindings between components based on component types and data flow patterns.
        This ensures all components are properly connected even if LLM doesn't generate bindings.
        """
        bindings = []
        
        # Categorize components by type for easier connection logic
        components_by_type = {}
        for comp in components:
            comp_type = comp.get('type', 'Unknown')
            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(comp)
        
        # Create a name->component mapping for easy lookup
        comp_by_name = {comp['name']: comp for comp in components}
        
        # Helper function to get first output port name
        def get_output_port(comp):
            outputs = comp.get('outputs', [])
            if outputs and len(outputs) > 0:
                return outputs[0].get('name', 'output')
            return None
        
        # Helper function to get first input port name
        def get_input_port(comp):
            inputs = comp.get('inputs', [])
            if inputs and len(inputs) > 0:
                return inputs[0].get('name', 'input')
            return None
        
        # Connect Sources to data processors (Transformers, Models, Controllers)
        sources = components_by_type.get('Source', [])
        data_processors = (components_by_type.get('Transformer', []) + 
                          components_by_type.get('Model', []) + 
                          components_by_type.get('Controller', []))
        
        for source in sources:
            output_port = get_output_port(source)
            if output_port:
                # Find semantically related processor
                for processor in data_processors:
                    input_port = get_input_port(processor)
                    if input_port and self._is_semantically_related(source['name'], processor['name']):
                        bindings.append({
                            'from_component': source['name'],
                            'from_port': output_port,
                            'to_component': processor['name'],
                            'to_port': input_port
                        })
                        print(f"   Connected: {source['name']}.{output_port} → {processor['name']}.{input_port}")
                        break
        
        # Connect APIEndpoints to Controllers/Transformers
        api_endpoints = components_by_type.get('APIEndpoint', [])
        for api in api_endpoints:
            output_port = get_output_port(api)
            if output_port:
                # Find related controllers or transformers
                for processor in data_processors:
                    input_port = get_input_port(processor)
                    if input_port and self._is_semantically_related(api['name'], processor['name']):
                        bindings.append({
                            'from_component': api['name'],
                            'from_port': output_port,
                            'to_component': processor['name'],
                            'to_port': input_port
                        })
                        print(f"   Connected: {api['name']}.{output_port} → {processor['name']}.{input_port}")
                        break
        
        # IMPORTANT: Do NOT create bindings TO APIEndpoint.request ports
        # This would violate the architecture (APIEndpoints are entry points)
        
        # Connect data processors to Stores/Sinks
        stores = components_by_type.get('Store', [])
        sinks = components_by_type.get('Sink', [])
        data_consumers = stores + sinks
        
        for processor in data_processors:
            output_port = get_output_port(processor)
            if output_port:
                # Find semantically related store/sink
                for consumer in data_consumers:
                    input_port = get_input_port(consumer)
                    if input_port and self._is_semantically_related(processor['name'], consumer['name']):
                        bindings.append({
                            'from_component': processor['name'],
                            'from_port': output_port,
                            'to_component': consumer['name'],
                            'to_port': input_port
                        })
                        print(f"   Connected: {processor['name']}.{output_port} → {consumer['name']}.{input_port}")
                        break
        
        # Special case: Connect Routers to multiple components
        routers = components_by_type.get('Router', [])
        for router in routers:
            # Routers typically receive from APIs and route to different processors
            input_port = get_input_port(router)
            output_port = get_output_port(router)
            
            if input_port:
                # Find API endpoints to connect to router input
                for api in api_endpoints:
                    api_output = get_output_port(api)
                    if api_output:
                        bindings.append({
                            'from_component': api['name'],
                            'from_port': api_output,
                            'to_component': router['name'],
                            'to_port': input_port
                        })
                        print(f"   Connected: {api['name']}.{api_output} → {router['name']}.{input_port}")
                        break
            
            if output_port:
                # Connect router to multiple processors
                for processor in data_processors[:2]:  # Connect to first 2 processors
                    proc_input = get_input_port(processor)
                    if proc_input:
                        bindings.append({
                            'from_component': router['name'],
                            'from_port': output_port,
                            'to_component': processor['name'],
                            'to_port': proc_input
                        })
                        print(f"   Connected: {router['name']}.{output_port} → {processor['name']}.{proc_input}")
        
        # Ensure no orphaned components - connect any remaining unconnected components
        connected_components = set()
        for binding in bindings:
            connected_components.add(binding['from_component'])
            connected_components.add(binding['to_component'])
        
        orphaned = [comp for comp in components if comp['name'] not in connected_components]
        
        for orphan in orphaned:
            # Try to connect orphaned component based on its type
            if orphan['type'] in ['Source', 'APIEndpoint'] and get_output_port(orphan):
                # Connect to first available processor
                for processor in data_processors:
                    if processor['name'] not in [b['to_component'] for b in bindings]:
                        input_port = get_input_port(processor)
                        if input_port:
                            bindings.append({
                                'from_component': orphan['name'],
                                'from_port': get_output_port(orphan),
                                'to_component': processor['name'],
                                'to_port': input_port
                            })
                            print(f"   Connected orphan: {orphan['name']} → {processor['name']}")
                            break
            
            elif orphan['type'] in ['Store', 'Sink'] and get_input_port(orphan):
                # Connect from first available processor
                for processor in data_processors:
                    if get_output_port(processor):
                        bindings.append({
                            'from_component': processor['name'],
                            'from_port': get_output_port(processor),
                            'to_component': orphan['name'],
                            'to_port': get_input_port(orphan)
                        })
                        print(f"   Connected to orphan: {processor['name']} → {orphan['name']}")
                        break
        
        return bindings
    
    def _is_semantically_related(self, name1: str, name2: str) -> bool:
        """Check if two component names are semantically related"""
        # Convert to lowercase for comparison
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Extract key terms
        terms1 = set(name1_lower.replace('_', ' ').split())
        terms2 = set(name2_lower.replace('_', ' ').split())
        
        # Check for common terms
        common_terms = terms1.intersection(terms2)
        if common_terms:
            return True
        
        # Check for related concepts
        related_concepts = [
            ('user', 'auth'),
            ('user', 'authentication'),
            ('task', 'todo'),
            ('api', 'endpoint'),
            ('data', 'store'),
            ('data', 'database'),
            ('message', 'queue'),
            ('event', 'stream'),
            ('log', 'monitor'),
            ('metric', 'monitor'),
            ('transform', 'process'),
            ('validate', 'check'),
            ('analyze', 'insight'),
            ('report', 'dashboard')
        ]
        
        for concept1, concept2 in related_concepts:
            if ((concept1 in name1_lower and concept2 in name2_lower) or
                (concept2 in name1_lower and concept1 in name2_lower)):
                return True
        
        # Default: consider generic processors as related to anything
        generic_terms = ['service', 'manager', 'handler', 'processor', 'controller']
        for term in generic_terms:
            if term in name1_lower or term in name2_lower:
                return True
        
        return False
    
    def _call_llm_with_retries(self, completion_params: Dict[str, Any]):
        """Call LLM using UnifiedLLMProvider with enhanced error handling and retry logic."""
        from autocoder_cc.llm_providers.unified_llm_provider import LLMRequest
        import json
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Extract messages from completion params
        messages = completion_params.get("messages", [])
        
        # Combine system and user messages
        system_prompt = ""
        user_prompt = ""
        
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                user_prompt = msg['content']
        
        # Create LLMRequest
        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=completion_params.get("temperature", 0.1),
            max_tokens=completion_params.get("max_tokens", 8192),
            json_mode=True if "response_format" in completion_params else False
        )
        
        # Enhanced retry logic for JSON parsing issues
        max_json_retries = 3
        last_error = None
        
        for attempt in range(max_json_retries):
            try:
                # Use UnifiedLLMProvider's synchronous method
                response = self.llm_provider.generate_sync(request)
                
                # Check if response is empty BEFORE wrapping
                if not response.content or response.content.strip() == "":
                    logger.warning(f"Empty response on attempt {attempt + 1}/{max_json_retries}")
                    if attempt < max_json_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise NaturalLanguageTranslationError(
                        f"LLM returned empty response after {max_json_retries} attempts"
                    )
                
                # If JSON mode is enabled, validate the response is valid JSON
                if request.json_mode:
                    try:
                        # Try to parse as JSON to validate
                        json.loads(response.content)
                        logger.debug(f"Valid JSON response received on attempt {attempt + 1}")
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Invalid JSON on attempt {attempt + 1}/{max_json_retries}: {e}\n"
                            f"Response content (first 500 chars): {response.content[:500]}"
                        )
                        if attempt < max_json_retries - 1:
                            # Add explicit JSON instruction for retry
                            if "Return ONLY valid JSON" not in user_prompt:
                                user_prompt += "\n\nIMPORTANT: Return ONLY valid JSON, no other text."
                                request.user_prompt = user_prompt
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        # On final attempt, try to extract JSON from the response
                        import re
                        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                        if json_match:
                            try:
                                json.loads(json_match.group(0))
                                response.content = json_match.group(0)
                                logger.info("Successfully extracted valid JSON from response")
                            except json.JSONDecodeError:
                                raise NaturalLanguageTranslationError(
                                    f"Could not parse valid JSON after {max_json_retries} attempts. "
                                    f"Last error: {e}"
                                )
                        else:
                            raise NaturalLanguageTranslationError(
                                f"No valid JSON found in response after {max_json_retries} attempts"
                            )
                
                # Wrap response in OpenAI-compatible format for backward compatibility
                class ResponseWrapper:
                    class Choice:
                        class Message:
                            def __init__(self, content):
                                self.content = content
                                self.refusal = None
                        def __init__(self, content):
                            self.message = self.Message(content)
                    def __init__(self, content):
                        self.choices = [self.Choice(content)]
                
                return ResponseWrapper(response.content)
                
            except NaturalLanguageTranslationError:
                raise  # Re-raise our custom errors
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed on attempt {attempt + 1}/{max_json_retries}: {e}")
                if attempt < max_json_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
        # All attempts failed
        raise NaturalLanguageTranslationError(
            f"LLM service failed after {max_json_retries} attempts. "
            f"Last error: {last_error}. "
            f"This indicates an issue with the LLM service or response format."
        )


# Example usage and testing
def demonstrate_usage():
    """Show how the translator would be used"""
    
    translator = NaturalLanguageToPydanticTranslator()
    
    # Example well-specified requests
    requests = [
        """I need a financial news analysis system that:
        1. Continuously monitors MSNBC and Yahoo Finance for breaking news
        2. Extracts ticker symbols and company names from articles using entity recognition
        3. Performs sentiment analysis on the news stories to gauge market sentiment
        4. Stores the results in a PostgreSQL database for historical analysis
        5. Sends alerts when sentiment is strongly positive or negative for specific stocks
        The system should handle high volume (1000+ articles per hour) and be highly available.""",
        
        """Build a real-time IoT sensor monitoring system that:
        - Ingests temperature and humidity data from 500 sensors via MQTT
        - Validates the sensor readings and filters out anomalies
        - Aggregates data into 5-minute windows with min/max/avg calculations
        - Stores raw and aggregated data in TimescaleDB
        - Exposes a REST API for querying recent and historical data
        - Sends alerts via SMS when temperature exceeds thresholds
        Must process 10,000 readings per second with sub-second latency.""",
        
        """Create a customer support ticket processing system:
        - Receives support tickets via email, web form, and API
        - Uses NLP to categorize tickets by topic and urgency
        - Routes tickets to appropriate support teams based on category
        - Enriches tickets with customer history from CRM
        - Tracks SLA compliance and escalates overdue tickets
        - Provides real-time dashboard of ticket metrics
        Should integrate with Zendesk and Salesforce."""
    ]
    
    print("=== Natural Language to Pydantic IntermediateSystem Translator ===\n")
    
    for i, request in enumerate(requests, 1):
        print(f"Request {i}:")
        print("-" * 50)
        print(request[:200] + "..." if len(request) > 200 else request)
        print("\nTranslating to IntermediateSystem...\n")
        
        # Test NL → IntermediateSystem translation
        intermediate_system, structured_nl = translator.translate_to_intermediate(request)
        
        print("✅ Generated IntermediateSystem:")
        print(f"   Name: {intermediate_system.name}")
        print(f"   Description: {intermediate_system.description}")
        print(f"   Components: {len(intermediate_system.components)}")
        print(f"   Bindings: {len(intermediate_system.bindings)}")
        print(f"   Environment: {intermediate_system.environment}")
        
        print("\n📋 Structured Natural Language Analysis:")
        print(structured_nl)
        
        print("\n🔄 Testing full pipeline (NL → IntermediateSystem → Blueprint YAML)...")
        blueprint_yaml = translator.generate_full_blueprint(request)
        line_count = len(blueprint_yaml.split('\n'))
        print(f"✅ Generated {line_count} lines of Blueprint YAML")
        
        print("=" * 80 + "\n")


def test_specific_request():
    """Test with a specific well-specified request for validation"""
    translator = NaturalLanguageToPydanticTranslator()
    
    # Simple test case
    simple_request = """I need a financial news analysis system that:
1. Continuously monitors MSNBC and Yahoo Finance for breaking news
2. Extracts ticker symbols and company names from articles using entity recognition
3. Performs sentiment analysis on the news stories to gauge market sentiment
4. Stores the results in a PostgreSQL database for historical analysis
5. Sends alerts when sentiment is strongly positive or negative for specific stocks
The system should handle high volume (1000+ articles per hour) and be highly available."""

    print("=== TASK 2 EVIDENCE: Simple NL Request Translation ===")
    print("Input Natural Language Request:")
    print(simple_request)
    print("\n" + "="*50)
    
    intermediate_system, structured_nl = translator.translate_to_intermediate(simple_request)
    
    print("Generated Pydantic IntermediateSystem (JSON representation):")
    print(intermediate_system.model_dump_json(indent=2))
    
    print("\n" + "="*50)
    print("Generated Structured Natural Language Output:")
    print(structured_nl)
    
    print("\n" + "="*50)
    print("Pydantic Validation Results:")
    try:
        # Validation happens automatically during construction
        print("✅ Pydantic validation PASSED")
        print(f"   System name: {intermediate_system.name}")
        print(f"   Components count: {len(intermediate_system.components)}")
        print(f"   Bindings count: {len(intermediate_system.bindings)}")
        print(f"   Environment: {intermediate_system.environment}")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED: {e}")
    
    return intermediate_system, structured_nl


def test_complex_request():
    """Test with a complex well-specified request for validation"""
    translator = NaturalLanguageToPydanticTranslator()
    
    # Complex test case
    complex_request = """Build a real-time IoT sensor monitoring system that:
- Ingests temperature and humidity data from 500 sensors via MQTT broker
- Each sensor sends JSON messages every 30 seconds with sensor_id, temperature, humidity, timestamp
- Validates sensor readings (temperature: -40°C to +85°C, humidity: 0-100%)
- Filters out readings that deviate >3 standard deviations from sensor's 24-hour average
- Aggregates valid readings into 5-minute windows with min/max/avg calculations
- Stores raw readings in TimescaleDB hypertable partitioned by time
- Stores aggregated data in separate table for fast querying
- Sends SMS alerts via Twilio when temperature exceeds building-specific thresholds
- Exposes REST API for querying current and historical sensor data
- Provides WebSocket endpoint for real-time sensor feeds
Must process 10,000 readings per second with sub-second latency and 99.95% data capture rate."""

    print("=== TASK 2 EVIDENCE: Complex NL Request Translation ===")
    print("Input Natural Language Request:")
    print(complex_request)
    print("\n" + "="*50)
    
    intermediate_system, structured_nl = translator.translate_to_intermediate(complex_request)
    
    print("Generated Pydantic IntermediateSystem (JSON representation):")
    print(intermediate_system.model_dump_json(indent=2))
    
    print("\n" + "="*50)
    print("Generated Structured Natural Language Output:")
    print(structured_nl)
    
    print("\n" + "="*50)
    print("Pydantic Validation Results:")
    try:
        # Validation happens automatically during construction
        print("✅ Pydantic validation PASSED")
        print(f"   System name: {intermediate_system.name}")
        print(f"   Components count: {len(intermediate_system.components)}")
        print(f"   Bindings count: {len(intermediate_system.bindings)}")
        print(f"   Environment: {intermediate_system.environment}")
    except Exception as e:
        print(f"❌ Pydantic validation FAILED: {e}")
    
    return intermediate_system, structured_nl


def generate_system_from_description(description: str, output_dir: str = "./generated_system", skip_deployment: bool = True) -> str:
    """
    Full pipeline: Natural Language → Blueprint → System Generation
    This is the main entry point expected by the CLI
    
    Args:
        description: Natural language description of the system
        output_dir: Directory to generate the system in
        skip_deployment: Skip Kubernetes deployment generation (default: True to avoid k8s dependency)
    """
    import asyncio
    from pathlib import Path
    from . import SystemGenerator
    
    print(f"🤖 Translating natural language to blueprint...")
    translator = NaturalLanguageToPydanticTranslator()
    
    # Generate blueprint YAML from natural language
    blueprint_yaml = translator.generate_full_blueprint(description)
    
    print(f"✅ Generated blueprint YAML")
    print(f"📝 Blueprint preview (first 200 chars):")
    print(blueprint_yaml[:200] + "..." if len(blueprint_yaml) > 200 else blueprint_yaml)
    print()
    
    # Generate the complete system
    print(f"🔧 Generating system components...")
    generator = SystemGenerator(Path(output_dir), skip_deployment=skip_deployment)
    
    # Run the async system generation
    async def run_generation():
        return await generator.generate_system_from_yaml(blueprint_yaml)
    
    generated_system = asyncio.run(run_generation())
    
    print(f"✅ System generation complete!")
    print(f"   Output directory: {generated_system.output_directory}")
    print(f"   System name: {generated_system.name}")
    print(f"   Components: {len(generated_system.components)}")
    
    return str(generated_system.output_directory)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run specific tests for Task 2 evidence
        print("Running Task 2 Tests for Evidence Collection...\n")
        
        # Test simple request
        test_specific_request()
        print("\n" + "="*80 + "\n")
        
        # Test complex request  
        test_complex_request()
        
    elif len(sys.argv) > 2 and sys.argv[1] == "--request":
        # Run translation on specific request
        translator = NaturalLanguageToPydanticTranslator()
        request = sys.argv[2]
        
        print(f"=== Translating Request ===")
        print(f"Input: {request}")
        print()
        
        intermediate_system, structured_nl = translator.translate_to_intermediate(request)
        
        print("Generated IntermediateSystem (JSON):")
        print(intermediate_system.model_dump_json(indent=2))
        print()
        print("Structured Natural Language:")
        print(structured_nl)
        
    else:
        # Run general demonstration
        demonstrate_usage()