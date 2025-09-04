#!/usr/bin/env python3
"""
Semantic Validator for Autocoder v5.0
Implements Level 4 validation using LLM to verify business logic reasonableness

According to CLAUDE.md and Problems_2025.0620.md:
- Validates that system outputs make semantic sense for the given business purpose
- Uses LLM to check if the output is "reasonable" given the system description
- Prevents systems that pass tests but produce nonsensical results
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv
from autocoder_cc.observability.structured_logging import get_logger

load_dotenv()

# Check for available LLM libraries
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


class SemanticValidationError(Exception):
    """Exception raised when semantic validation fails due to missing dependencies"""
    pass


@dataclass
class SemanticValidationResult:
    """Result of semantic validation check"""
    is_reasonable: bool
    reasoning: str
    issues: List[str]
    suggestions: Optional[List[str]] = None


class SemanticValidator:
    """
    Validates that system outputs make business sense using LLM reasoning.
    
    This validator checks if the actual output of a system is reasonable
    given its stated purpose and expected behavior.
    """
    
    def __init__(self, llm_provider: str = "openai", api_key: str = None):
        """
        Initialize semantic validator with LLM provider.
        
        Args:
            llm_provider: "openai" or "anthropic"
            api_key: API key for LLM provider (REQUIRED - falls back to env var if not provided)
        """
        self.llm_provider = llm_provider
        self.logger = get_logger("SemanticValidator")
        
        # Get API key - REQUIRED, no fallbacks
        if api_key:
            self.api_key = api_key
        else:
            # Try environment variable
            if llm_provider == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")
            elif llm_provider == "anthropic":
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            else:
                raise SemanticValidationError(
                    f"Unknown LLM provider: {llm_provider}. Use 'openai' or 'anthropic'"
                )
        
        # FAIL FAST if no API key
        if not self.api_key:
            raise SemanticValidationError(
                f"CRITICAL: {llm_provider.upper()} API key REQUIRED for semantic validation. "
                f"Provide api_key parameter or set {llm_provider.upper()}_API_KEY environment variable. "
                "NO FALLBACKS - System cannot function without LLM."
            )
        
        # Initialize LLM client based on provider
        if llm_provider == "openai" and HAS_OPENAI:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = "o3-mini"
        elif llm_provider == "anthropic" and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-opus-20240229"
        else:
            raise SemanticValidationError(
                f"LLM provider '{llm_provider}' library not available. "
                f"Install openai or anthropic library. "
                f"NO MOCK MODES - System requires real LLM."
            )
    
    def validate_reasonableness(self, system_description: str, final_output: Dict[str, Any]) -> bool:
        """
        Validate if the system output is reasonable given its description.
        
        This is the main method required by CLAUDE.md specification.
        
        Args:
            system_description: Natural language description of what the system should do
            final_output: The actual output produced by the system
            
        Returns:
            bool: True if output is reasonable, False otherwise
        """
        result = self.validate_with_reasoning(system_description, final_output)
        return result.is_reasonable
    
    def validate_with_reasoning(self, system_description: str, final_output: Dict[str, Any]) -> SemanticValidationResult:
        """
        Validate with detailed reasoning about why output is reasonable or not.
        
        Args:
            system_description: Natural language description of what the system should do
            final_output: The actual output produced by the system
            
        Returns:
            SemanticValidationResult with detailed reasoning
        """
        # Construct prompt for LLM to analyze reasonableness
        prompt = self._construct_validation_prompt(system_description, final_output)
        
        # Get LLM response
        try:
            response = self._query_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            # Default to unreasonable if LLM fails
            return SemanticValidationResult(
                is_reasonable=False,
                reasoning=f"LLM validation failed: {str(e)}",
                issues=["Could not validate with LLM"],
                suggestions=["Check LLM API configuration"]
            )
    
    def _construct_validation_prompt(self, system_description: str, final_output: Dict[str, Any]) -> str:
        """Construct prompt for LLM to validate reasonableness"""
        return f"""You are a quality assurance expert validating that a software system produces reasonable outputs.

SYSTEM DESCRIPTION:
{system_description}

ACTUAL OUTPUT PRODUCED:
{final_output}

TASK:
Analyze whether this output is reasonable given what the system is supposed to do. Consider:
1. Does the output match the expected purpose of the system?
2. Are the values/data in the output sensible for this use case?
3. Is there any obviously wrong, placeholder, or nonsensical data?
4. Would a business user accept this output as valid?

Respond in this exact JSON format:
{{
    "is_reasonable": true/false,
    "reasoning": "Brief explanation of your decision",
    "issues": ["List of specific problems found, if any"],
    "suggestions": ["List of improvements needed, if any"]
}}

Be strict - the output should truly make business sense, not just be syntactically correct."""
    
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the validation prompt"""
        if self.llm_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a software quality expert who validates system outputs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent validation
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _parse_llm_response(self, response: str) -> SemanticValidationResult:
        """Parse LLM response into SemanticValidationResult"""
        import json
        
        try:
            # Parse JSON response
            data = json.loads(response)
            
            return SemanticValidationResult(
                is_reasonable=bool(data.get("is_reasonable", False)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", [])
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Try to extract a boolean decision from the text
            response_lower = response.lower()
            is_reasonable = "reasonable" in response_lower and "not reasonable" not in response_lower
            
            return SemanticValidationResult(
                is_reasonable=is_reasonable,
                reasoning=response[:200] + "..." if len(response) > 200 else response,
                issues=["Could not parse structured response from LLM"],
                suggestions=[]
            )
    
    def validate_component_output(self, 
                                component_name: str,
                                component_purpose: str,
                                input_data: Dict[str, Any],
                                output_data: Dict[str, Any]) -> SemanticValidationResult:
        """
        Validate a single component's output for reasonableness.
        
        Args:
            component_name: Name of the component
            component_purpose: What the component is supposed to do
            input_data: Input that was provided to the component
            output_data: Output produced by the component
            
        Returns:
            SemanticValidationResult with validation details
        """
        prompt = f"""You are validating a single component's output for reasonableness.

COMPONENT: {component_name}
PURPOSE: {component_purpose}

INPUT PROVIDED:
{input_data}

OUTPUT PRODUCED:
{output_data}

TASK:
Determine if this output makes sense given the component's purpose and input. Consider:
1. Is the transformation/processing logical?
2. Are output values reasonable given the input?
3. Is this what a developer would expect from this component?

Respond in this exact JSON format:
{{
    "is_reasonable": true/false,
    "reasoning": "Brief explanation",
    "issues": ["Specific problems, if any"],
    "suggestions": ["Improvements, if any"]
}}"""
        
        try:
            response = self._query_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            self.logger.error(f"Component validation failed: {e}")
            return SemanticValidationResult(
                is_reasonable=False,
                reasoning=f"Validation error: {str(e)}",
                issues=[f"Could not validate {component_name}"],
                suggestions=[]
            )
    
    def validate_test_data_quality(self, 
                                 schema_description: str,
                                 test_data: List[Dict[str, Any]]) -> SemanticValidationResult:
        """
        Validate that test data is realistic and not generic placeholders.
        
        Args:
            schema_description: Description of what the data represents
            test_data: List of test data items
            
        Returns:
            SemanticValidationResult indicating if test data is realistic
        """
        prompt = f"""Evaluate if this test data is realistic or just generic placeholders.

DATA SCHEMA/PURPOSE:
{schema_description}

TEST DATA SAMPLES:
{test_data[:5]}  # Show first 5 items

TASK:
Determine if this test data is:
1. Realistic and domain-specific
2. Just generic placeholders like {{"value": 42}}
3. Appropriate for testing the described schema

Respond in this exact JSON format:
{{
    "is_reasonable": true/false,
    "reasoning": "Assessment of data quality",
    "issues": ["Problems with test data"],
    "suggestions": ["How to make data more realistic"]
}}"""
        
        try:
            response = self._query_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            self.logger.error(f"Test data validation failed: {e}")
            return SemanticValidationResult(
                is_reasonable=False,
                reasoning=f"Validation error: {str(e)}",
                issues=["Could not validate test data"],
                suggestions=[]
            )
    

# Example usage and testing
if __name__ == "__main__":
    import anyio
    
    # Example system output to validate
    example_system_description = """
    A fraud detection system that analyzes financial transactions and scores them
    for fraud risk. It should intake transaction data, analyze patterns, and output
    risk scores between 0-100 with explanations.
    """
    
    # Example of good output
    good_output = {
        "transaction_id": "TXN-2024-001234",
        "fraud_score": 87,
        "risk_level": "HIGH",
        "reasons": [
            "Unusual transaction amount for this merchant",
            "Transaction originated from high-risk country",
            "Multiple transactions in short time period"
        ],
        "recommended_action": "BLOCK",
        "confidence": 0.92
    }
    
    # Example of bad output (generic placeholder)
    bad_output = {
        "value": 42,
        "status": "OK",
        "data": {"test": True}
    }
    
    async def test_semantic_validation():
        """Test the semantic validator"""
        # Note: This requires setting OPENAI_API_KEY or ANTHROPIC_API_KEY
        try:
            validator = SemanticValidator(llm_provider="openai")
            
            print("Testing GOOD output...")
            good_result = validator.validate_with_reasoning(example_system_description, good_output)
            print(f"Is reasonable: {good_result.is_reasonable}")
            print(f"Reasoning: {good_result.reasoning}")
            print(f"Issues: {good_result.issues}")
            print()
            
            print("Testing BAD output...")
            bad_result = validator.validate_with_reasoning(example_system_description, bad_output)
            print(f"Is reasonable: {bad_result.is_reasonable}")
            print(f"Reasoning: {bad_result.reasoning}")
            print(f"Issues: {bad_result.issues}")
            print(f"Suggestions: {bad_result.suggestions}")
            
        except Exception as e:
            print(f"Test failed: {e}")
            print("Make sure to set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
    
    # Run test if executed directly
    anyio.run(test_semantic_validation)