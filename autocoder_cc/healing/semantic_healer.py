from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Semantic Healer for Autocoder v5.0

Uses LLM to fix business logic issues:
- Corrects unreasonable transformations
- Enhances test data to be domain-specific
- Injects output validation
- Fixes business logic errors
"""

import logging
import ast
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import os
from autocoder_cc.core.config import settings

# Import semantic validator for reasonableness checking
try:
    from blueprint_language.semantic_validator import SemanticValidator
    HAS_SEMANTIC_VALIDATOR = True
except ImportError:
    HAS_SEMANTIC_VALIDATOR = False

# Check for LLM libraries
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class SemanticHealingConfigurationError(Exception):
    """Exception raised when semantic healing configuration is invalid or missing"""
    pass


@dataclass
class SemanticHealingResult:
    """Result of semantic healing operation"""
    success: bool
    original_code: str
    healed_code: str
    reasoning: str
    changes_made: List[str]
    error_message: Optional[str] = None


class SemanticHealer:
    """
    Heals business logic issues using LLM reasoning.
    
    Focuses on:
    - Business logic corrections
    - Domain-specific test data generation
    - Output validation injection
    - Placeholder detection and replacement
    """
    
    def __init__(self, llm_provider: str = "openai", api_key: str = None):
        self.logger = get_logger("SemanticHealer")
        self.llm_provider = llm_provider
        
        # Get API key - REQUIRED, no fallbacks
        if api_key:
            self.api_key = api_key
        else:
            # Try environment variable
            if llm_provider == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")
            elif llm_provider == "anthropic":
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif llm_provider == "gemini":
                self.api_key = os.environ.get("GEMINI_API_KEY")
            else:
                raise SemanticHealingConfigurationError(
                    f"Unknown LLM provider: {llm_provider}. Use 'openai', 'anthropic', or 'gemini'"
                )
        
        # FAIL FAST if no API key
        if not self.api_key:
            raise SemanticHealingConfigurationError(
                f"CRITICAL: {llm_provider.upper()} API key REQUIRED for semantic healing. "
                f"Provide api_key parameter or set {llm_provider.upper()}_API_KEY environment variable. "
                "NO FALLBACKS - System cannot function without LLM."
            )
        
        # Initialize LLM client
        self.logger.info(f"🤖 SEMANTIC HEALER USING {llm_provider.upper()} LLM")
        if llm_provider == "openai" and HAS_OPENAI:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = settings.get_llm_model()
        elif llm_provider == "anthropic" and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = settings.ANTHROPIC_MODEL
        elif llm_provider == "gemini" and HAS_GEMINI:
            genai.configure(api_key=self.api_key)
            self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
            self.client = genai.GenerativeModel(self.model)
        else:
            raise SemanticHealingConfigurationError(f"Unsupported or unavailable LLM provider: {llm_provider}")
        
        # Initialize semantic validator if available
        self.semantic_validator = None
        if HAS_SEMANTIC_VALIDATOR:
            try:
                self.semantic_validator = SemanticValidator(llm_provider, api_key)
            except:
                self.logger.warning("Could not initialize semantic validator")
    
    def _is_llm_available(self) -> bool:
        """Check if LLM configuration is available"""
        openai_available = HAS_OPENAI and bool(os.environ.get("OPENAI_API_KEY"))
        anthropic_available = HAS_ANTHROPIC and bool(os.environ.get("ANTHROPIC_API_KEY"))
        gemini_available = HAS_GEMINI and bool(os.environ.get("GEMINI_API_KEY"))
        return openai_available or anthropic_available or gemini_available
    
    def heal_business_logic(self, code: str, component_purpose: str, 
                          input_schema: Dict[str, Any], output_schema: Dict[str, Any]) -> SemanticHealingResult:
        """
        Fix business logic issues in component code.
        
        Args:
            code: Component code with potential logic issues
            component_purpose: What the component should do
            input_schema: Expected input data schema
            output_schema: Expected output data schema
            
        Returns:
            SemanticHealingResult with corrected business logic
        """
        self.logger.debug("🤖 PERFORMING LLM-ENHANCED SEMANTIC HEALING")
        prompt = f"""You are fixing business logic in a data processing component.

COMPONENT PURPOSE:
{component_purpose}

INPUT SCHEMA:
{json.dumps(input_schema, indent=2)}

OUTPUT SCHEMA:
{json.dumps(output_schema, indent=2)}

CURRENT CODE:
```python
{code}
```

TASK:
1. Analyze if the current code correctly implements the stated purpose
2. Fix any business logic errors or unreasonable transformations
3. Ensure the code produces outputs that match the schema and make business sense
4. Remove any placeholder logic (like return {{"value": 42}})
5. Add proper data validation and error handling

Return the corrected code that properly implements the business logic.
Format your response as:
REASONING: [explain what was wrong and what you fixed]
FIXED_CODE:
```python
[corrected code here]
```
CHANGES:
- [list each change made]"""

        try:
            response = self._query_llm(prompt)
            return self._parse_healing_response(response, code)
        except Exception as e:
            return SemanticHealingResult(
                success=False,
                original_code=code,
                healed_code=code,
                reasoning="",
                changes_made=[],
                error_message=f"Failed to heal business logic: {str(e)}"
            )
    
    def generate_domain_specific_test_data(self, schema: Dict[str, Any], 
                                         domain_description: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate realistic, domain-specific test data.
        
        Args:
            schema: Data schema to follow
            domain_description: Description of the business domain
            count: Number of test examples to generate
            
        Returns:
            List of domain-specific test data
        """
        prompt = f"""Generate realistic test data for the following domain and schema.

DOMAIN:
{domain_description}

SCHEMA:
{json.dumps(schema, indent=2)}

REQUIREMENTS:
1. Generate {count} diverse, realistic examples
2. Use domain-appropriate values (not generic placeholders)
3. Include edge cases and normal cases
4. Make the data believable for the given domain

Return the test data as a JSON array of objects matching the schema."""

        try:
            response = self._query_llm(prompt)
            
            # Robust JSON extraction and parsing
            parsed_data = self._extract_and_parse_json(response)
            if parsed_data and isinstance(parsed_data, list):
                return parsed_data
                
            # Fallback to generic test data if parsing fails
            self.logger.warning(f"Could not parse LLM response as JSON, using fallback data")
            return self._generate_fallback_test_data(domain_description, count)
            
        except Exception as e:
            self.logger.error(f"Failed to generate test data: {e}")
            # Return domain-specific fallback data
            return self._generate_fallback_test_data(domain_description, count)
    
    def _extract_and_parse_json(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """
        Robustly extract and parse JSON from LLM response.
        
        Args:
            response: Raw LLM response that may contain JSON
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        import re
        
        # Strategy 1: Try parsing entire response as JSON
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON array using regex
        json_patterns = [
            r'\[[\s\S]*?\]',  # Match array brackets with content
            r'\{[\s\S]*?\}',  # Match object brackets (in case single object)
            r'```json\s*([\s\S]*?)\s*```',  # Match JSON code blocks
            r'```\s*([\s\S]*?)\s*```',  # Match any code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict):
                        return [parsed]  # Convert single object to array
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Try to fix common JSON issues
        cleaned_response = response.strip()
        
        # Remove common LLM text before/after JSON
        json_start = max(cleaned_response.find('['), cleaned_response.find('{'))
        json_end = max(cleaned_response.rfind(']'), cleaned_response.rfind('}'))
        
        if json_start >= 0 and json_end >= json_start:
            potential_json = cleaned_response[json_start:json_end + 1]
            try:
                parsed = json.loads(potential_json)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _generate_fallback_test_data(self, domain_description: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate fallback test data when LLM parsing fails.
        
        Args:
            domain_description: Description of the business domain
            count: Number of test examples to generate
            
        Returns:
            List of domain-appropriate test data
        """
        import random
        import datetime
        
        test_data = []
        domain_lower = domain_description.lower()
        
        for i in range(count):
            if "fraud" in domain_lower or "risk" in domain_lower or "transaction" in domain_lower:
                # Financial/fraud domain
                item = {
                    "transaction_id": f"TXN-2024-{1000 + i}",
                    "amount": round(random.uniform(10.0, 5000.0), 2),
                    "merchant": f"Merchant_{chr(65 + i)}",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "user_id": f"USER-{100 + i}",
                    "location": random.choice(["US", "UK", "FR", "DE", "JP"])
                }
            elif "content" in domain_lower or "analysis" in domain_lower or "sentiment" in domain_lower:
                # Content analysis domain
                item = {
                    "content_id": f"CONTENT-{1000 + i}",
                    "content_type": random.choice(["text", "image", "video"]),
                    "raw_data": f"Sample content data {i}",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "source_metadata": {"origin": f"source_{i}"}
                }
            elif "user" in domain_lower or "customer" in domain_lower:
                # User/customer domain
                item = {
                    "user_id": f"USER-{1000 + i}",
                    "name": f"Test User {i+1}",
                    "email": f"user{i+1}@example.com",
                    "created_at": datetime.datetime.now().isoformat(),
                    "status": random.choice(["active", "inactive"])
                }
            elif "order" in domain_lower or "purchase" in domain_lower or "product" in domain_lower:
                # E-commerce domain
                item = {
                    "order_id": f"ORD-2024-{1000 + i}",
                    "customer_id": f"CUST-{100 + i}",
                    "total": round(random.uniform(20.0, 500.0), 2),
                    "status": random.choice(["pending", "processing", "shipped"]),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                # Generic business data
                item = {
                    "id": f"ID-{1000 + i}",
                    "name": f"Item {i+1}",
                    "value": round(random.uniform(1.0, 100.0), 2),
                    "category": random.choice(["A", "B", "C"]),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "active": random.choice([True, False])
                }
            
            test_data.append(item)
        
        return test_data
    
    def detect_placeholder_logic(self, code: str) -> bool:
        """
        Detect if code contains placeholder/demo logic.
        
        Args:
            code: Python code to check
            
        Returns:
            bool: True if placeholder logic detected
        """
        placeholder_patterns = [
            'return {"value": 42}',
            'return {"test": True}',
            'return "TODO"',
            'pass  # TODO',
            'raise NotImplementedError',
            'return {}',
            'return []',
            'return None  # TODO',
        ]
        
        # Check for exact patterns
        for pattern in placeholder_patterns:
            if pattern in code:
                return True
        
        # Check for minimal implementations
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == "process" and len(node.body) == 1:
                        stmt = node.body[0]
                        # Single return statement with constant
                        if isinstance(stmt, ast.Return) and isinstance(stmt.value, (ast.Constant, ast.Dict, ast.List)):
                            return True
        except:
            pass
        
        return False
    
    def inject_output_validation(self, code: str, output_schema: Dict[str, Any]) -> SemanticHealingResult:
        """
        Inject output validation to ensure reasonable results.
        
        Args:
            code: Component code
            output_schema: Expected output schema
            
        Returns:
            SemanticHealingResult with validation added
        """
        prompt = f"""Add output validation to ensure the component produces reasonable results.

CURRENT CODE:
```python
{code}
```

OUTPUT SCHEMA:
{json.dumps(output_schema, indent=2)}

TASK:
1. Add validation before returning results
2. Ensure outputs match the schema
3. Add reasonableness checks (e.g., scores in valid ranges, non-empty lists for required data)
4. Log warnings for suspicious outputs
5. Don't change the core logic, just add validation

Return the code with validation added."""

        try:
            response = self._query_llm(prompt)
            return self._parse_healing_response(response, code)
        except Exception as e:
            return SemanticHealingResult(
                success=False,
                original_code=code,
                healed_code=code,
                reasoning="",
                changes_made=[],
                error_message=f"Failed to inject validation: {str(e)}"
            )
    
    def heal_unreasonable_output(self, code: str, component_purpose: str,
                               sample_input: Dict[str, Any], 
                               unreasonable_output: Dict[str, Any]) -> SemanticHealingResult:
        """
        Fix code that produces unreasonable outputs.
        
        Args:
            code: Component code producing bad output
            component_purpose: What the component should do
            sample_input: Example input that produced bad output
            unreasonable_output: The unreasonable output produced
            
        Returns:
            SemanticHealingResult with fixed logic
        """
        # First check if output is actually unreasonable
        if self.semantic_validator:
            result = self.semantic_validator.validate_component_output(
                component_name="component",
                component_purpose=component_purpose,
                input_data=sample_input,
                output_data=unreasonable_output
            )
            
            if result.is_reasonable:
                return SemanticHealingResult(
                    success=False,
                    original_code=code,
                    healed_code=code,
                    reasoning="Output is actually reasonable",
                    changes_made=[]
                )
        
        prompt = f"""Fix the component logic that produces unreasonable output.

COMPONENT PURPOSE:
{component_purpose}

CURRENT CODE:
```python
{code}
```

SAMPLE INPUT:
{json.dumps(sample_input, indent=2)}

UNREASONABLE OUTPUT PRODUCED:
{json.dumps(unreasonable_output, indent=2)}

PROBLEMS WITH OUTPUT:
- The output doesn't make sense given the component's purpose
- Values may be nonsensical or placeholder data

TASK:
Fix the logic to produce reasonable output that matches the component's purpose.
The output should make business sense given the input.

Return the fixed code."""

        try:
            response = self._query_llm(prompt)
            return self._parse_healing_response(response, code)
        except Exception as e:
            return SemanticHealingResult(
                success=False,
                original_code=code,
                healed_code=code,
                reasoning="",
                changes_made=[],
                error_message=f"Failed to fix unreasonable output: {str(e)}"
            )
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with a prompt"""
        if self.llm_provider == "openai":
            # Handle temperature for different models (o3 doesn't support temperature)
            completion_args = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert software engineer fixing code issues."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Only add temperature for models that support it (o3 doesn't)
            if not self.model.startswith("o3"):
                completion_args["temperature"] = 0.3
            
            response = self.client.chat.completions.create(**completion_args)
            return response.choices[0].message.content
        
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.content[0].text
        
        elif self.llm_provider == "gemini":
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000
            )
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
    
    def _parse_healing_response(self, response: str, original_code: str) -> SemanticHealingResult:
        """Parse LLM response into SemanticHealingResult"""
        import re
        
        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.*?)(?=FIXED_CODE:|```|$)', response, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
        
        # Extract code
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if not code_match:
            # Try without newline after FIXED_CODE:
            code_match = re.search(r'FIXED_CODE:.*?```python\n(.*?)```', response, re.DOTALL)
        if not code_match:
            code_match = re.search(r'FIXED_CODE:\s*\n(.*?)(?=CHANGES:|$)', response, re.DOTALL)
        
        healed_code = code_match.group(1).strip() if code_match else original_code
        
        # Extract changes
        changes = []
        changes_match = re.search(r'CHANGES:\s*\n(.*?)$', response, re.DOTALL)
        if changes_match:
            changes_text = changes_match.group(1)
            changes = [line.strip('- ').strip() for line in changes_text.split('\n') if line.strip().startswith('-')]
        
        return SemanticHealingResult(
            success=healed_code != original_code,
            original_code=original_code,
            healed_code=healed_code,
            reasoning=reasoning,
            changes_made=changes if changes else ["Modified business logic"]
        )
    
    def generate_config_value(self, field_name: str, field_requirement: 'ConfigRequirement',
                             context: 'PipelineContext') -> Tuple[bool, Any, str]:
        """
        Generate a configuration value for a missing field using LLM.
        
        Args:
            field_name: Name of the configuration field
            field_requirement: ConfigRequirement object describing the field
            context: PipelineContext with environment and pipeline information
            
        Returns:
            Tuple of (success, generated_value, reasoning)
        """
        from autocoder_cc.validation.config_requirement import ConfigType
        
        prompt = f"""Generate a configuration value for a data pipeline component.

{context.to_llm_context()}

Configuration Field Details:
- Field Name: {field_name}
- Type: {field_requirement.type}
- Description: {field_requirement.description}
- Required: {field_requirement.required}
- Semantic Type: {getattr(field_requirement, 'semantic_type', 'generic')}"""
        
        if field_requirement.example:
            prompt += f"\n- Example: {field_requirement.example}"
        
        if field_requirement.options:
            prompt += f"\n- Valid Options: {', '.join(field_requirement.options)}"
            
        if field_requirement.depends_on:
            prompt += f"\n- Depends On: {field_requirement.depends_on}"
            
        # Add environment-specific hints
        hints = context.get_environment_hints()
        if hints:
            prompt += "\n\nEnvironment Hints:"
            for key, hint in hints.items():
                prompt += f"\n- {key}: {hint}"
        
        prompt += """\n\nGenerate an appropriate value for this configuration field.
Consider the environment, deployment target, and component position in the pipeline.

Return ONLY the value, nothing else. No quotes for strings unless part of the value.

Examples of good values:
- For storage_url in production: s3://my-bucket/data/
- For storage_url in development: file:///tmp/local_data/
- For network_port: 8080
- For database_url: postgres://localhost:5432/mydb
- For kafka_broker: kafka-broker.internal:9092"""
        
        try:
            response = self._query_llm(prompt)
            generated_value = response.strip()
            
            # Parse the value based on type
            parsed_value = self._parse_config_value(generated_value, field_requirement.type)
            
            # Validate if provided
            if hasattr(field_requirement, 'validator') and field_requirement.validator:
                if not field_requirement.validator(parsed_value):
                    return False, None, "Generated value failed validation"
            
            reasoning = f"Generated {field_requirement.type} value for {context.environment.value} environment"
            return True, parsed_value, reasoning
            
        except Exception as e:
            self.logger.error(f"Failed to generate config value: {e}")
            return False, None, f"Error generating value: {str(e)}"
    
    def generate_missing_configs(self, missing_fields: List[str], 
                                requirements: List['ConfigRequirement'],
                                context: 'PipelineContext',
                                existing_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate values for all missing configuration fields.
        
        Args:
            missing_fields: List of missing field names
            requirements: List of ConfigRequirement objects
            context: PipelineContext with environment information
            existing_config: Existing configuration values
            
        Returns:
            Dictionary of generated configuration values
        """
        generated = {}
        existing = existing_config or {}
        
        # Create requirement lookup
        req_map = {req.name: req for req in requirements}
        
        for field_name in missing_fields:
            if field_name not in req_map:
                self.logger.warning(f"No requirement definition for field: {field_name}")
                continue
                
            requirement = req_map[field_name]
            
            # Check if conditional dependency is met
            if requirement.depends_on:
                conditions_met = all(
                    existing.get(dep_field) == dep_value
                    for dep_field, dep_value in requirement.depends_on.items()
                )
                if not conditions_met:
                    continue  # Skip this field if conditions not met
            
            success, value, reasoning = self.generate_config_value(
                field_name, requirement, context
            )
            
            if success:
                generated[field_name] = value
                self.logger.info(f"Generated config for {field_name}: {value} ({reasoning})")
            else:
                self.logger.warning(f"Failed to generate config for {field_name}: {reasoning}")
                # Use default if available
                if hasattr(requirement, 'default'):
                    generated[field_name] = requirement.default
                    self.logger.info(f"Using default for {field_name}: {requirement.default}")
        
        return generated
    
    def _parse_config_value(self, value_str: str, expected_type: str) -> Any:
        """
        Parse generated string value to expected type.
        
        Args:
            value_str: String value from LLM
            expected_type: Expected type (str, int, float, bool, list, dict)
            
        Returns:
            Parsed value in correct type
        """
        value_str = value_str.strip()
        
        if expected_type == "str" or expected_type == "string":
            # Remove quotes if present
            if value_str.startswith('"') and value_str.endswith('"'):
                return value_str[1:-1]
            if value_str.startswith("'") and value_str.endswith("'"):
                return value_str[1:-1]
            return value_str
            
        elif expected_type == "int" or expected_type == "integer":
            return int(value_str)
            
        elif expected_type == "float" or expected_type == "number":
            return float(value_str)
            
        elif expected_type == "bool" or expected_type == "boolean":
            return value_str.lower() in ['true', 'yes', '1', 'on']
            
        elif expected_type == "list" or expected_type == "array":
            # Try to parse as JSON
            if value_str.startswith('['):
                return json.loads(value_str)
            # Otherwise split by comma
            return [v.strip() for v in value_str.split(',')]
            
        elif expected_type == "dict" or expected_type == "object":
            # Try to parse as JSON
            if value_str.startswith('{'):
                return json.loads(value_str)
            # Otherwise return as-is
            return {"value": value_str}
            
        else:
            # Default to string
            return value_str


def heal_business_logic(file_path: str, component_purpose: str,
                       input_schema: Dict[str, Any], output_schema: Dict[str, Any]) -> bool:
    """
    Convenience function to heal business logic in a component file.
    
    Args:
        file_path: Path to component file
        component_purpose: What the component should do
        input_schema: Expected input schema
        output_schema: Expected output schema
        
    Returns:
        bool: True if healing was successful
    """
    try:
        healer = SemanticHealer()
        
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Check if code has placeholder logic
        if healer.detect_placeholder_logic(code):
            logging.info(f"Placeholder logic detected in {file_path}")
        
        result = healer.heal_business_logic(code, component_purpose, input_schema, output_schema)
        
        if result.success:
            # Backup original
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w') as f:
                f.write(code)
            
            # Write healed code
            with open(file_path, 'w') as f:
                f.write(result.healed_code)
            
            logging.info(f"Business logic healed: {file_path}")
            logging.info(f"Reasoning: {result.reasoning}")
            logging.info(f"Changes: {result.changes_made}")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Failed to heal business logic: {e}")
        return False
    
    # Test semantic healer
    test_code = '''
async def process(self):
    """Process fraud detection logic"""
    async for transaction in self.receive_streams["input"]:
        # Placeholder logic
        result = {
            "value": 42,
            "status": "OK"
        }
        await self.send_streams["output"].send(result)
'''
    
    print("Testing Semantic Healer...")
    print("Original code:")
    print(test_code)
    print("\n" + "="*50 + "\n")
    
    try:
        healer = SemanticHealer()
        
        # Test placeholder detection
        has_placeholder = healer.detect_placeholder_logic(test_code)
        print(f"Placeholder detected: {has_placeholder}")
        
        # Test business logic healing
        result = healer.heal_business_logic(
            test_code,
            "Analyze financial transactions for fraud risk",
            {"transaction": {"amount": "number", "merchant": "string", "country": "string"}},
            {"fraud_score": "number", "risk_level": "string", "reasons": "array"}
        )
        
        if result.success:
            print("\nHealed code:")
            print(result.healed_code)
            print(f"\nReasoning: {result.reasoning}")
            print(f"Changes: {result.changes_made}")
        else:
            print(f"Healing failed: {result.error_message}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Semantic healer requires OPENAI_API_KEY or ANTHROPIC_API_KEY")