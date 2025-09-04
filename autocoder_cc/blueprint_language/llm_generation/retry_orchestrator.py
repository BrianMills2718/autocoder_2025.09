"""
Retry Orchestrator

This module handles retry logic with progressive prompt improvement for LLM generation.
When generation attempts fail, it analyzes the failure reasons and improves prompts
for subsequent attempts.

Key Features:
- Error classification for appropriate retry strategies
- Progressive prompt improvement based on failure types
- Validation feedback integration
- Adaptive delay calculations based on error types
"""

import time
import random
import re
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional


class ErrorType(Enum):
    """Types of errors that can occur during LLM generation"""
    API_ERROR = "api_error"           # Network, rate limits, timeouts
    VALIDATION_ERROR = "validation_error"  # Content validation failures
    SYNTAX_ERROR = "syntax_error"     # Invalid Python syntax
    PATTERN_ERROR = "pattern_error"   # Missing required patterns


@dataclass
class RetryStrategy:
    """Strategy for handling different types of errors during LLM generation"""
    max_retries: int
    base_delay: float
    backoff_multiplier: float
    max_delay: float
    
    def get_delay(self, attempt: int, error_type: ErrorType) -> float:
        """Calculate delay for given attempt and error type"""
        if error_type == ErrorType.VALIDATION_ERROR:
            # Shorter delays for content validation errors since they're not network-related
            base = min(self.base_delay * 0.5, 1.0)
        else:
            # Standard delays for API errors
            base = self.base_delay
            
        delay = base * (self.backoff_multiplier ** attempt)
        jitter = random.uniform(0, 0.1 * delay)
        
        return min(delay + jitter, self.max_delay)
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if we should retry based on error type and attempt count"""
        if attempt >= self.max_retries:
            return False
            
        # Always retry validation errors since they can be fixed with better prompts
        if error_type == ErrorType.VALIDATION_ERROR:
            return True
            
        # Retry API errors with standard logic
        if error_type == ErrorType.API_ERROR:
            return True
            
        # Retry syntax errors - might be fixable
        if error_type == ErrorType.SYNTAX_ERROR:
            return True
            
        # Retry pattern errors - fixable with better prompts
        if error_type == ErrorType.PATTERN_ERROR:
            return True
            
        return False


class RetryOrchestrator:
    """
    Orchestrates retry logic with progressive prompt improvement
    
    Analyzes generation failures and applies appropriate retry strategies:
    - Classifies error types for targeted retry approaches
    - Builds adaptive prompts with validation feedback
    - Manages delay calculations and retry decisions
    - Formats validation feedback for prompt improvement
    """
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.retry_strategy = RetryStrategy(
            max_retries=max_retries,
            base_delay=base_delay,
            backoff_multiplier=2.0,
            max_delay=30.0
        )
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error to determine appropriate retry strategy"""
        error_msg = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Check for syntax errors - highest priority for quick fixes
        if ("syntax" in error_msg or "syntaxerror" in error_msg or "invalid syntax" in error_msg or
            "unbalanced parenthesis" in error_msg or "unmatched" in error_msg or
            "unexpected eof" in error_msg or "indentation" in error_msg or
            "position" in error_msg and "error" in error_msg or
            "compilation failed" in error_msg or "compile" in error_msg):
            return ErrorType.SYNTAX_ERROR
        
        # Check for pattern validation errors - need structural changes
        if ("missing required" in error_msg or 
            "composedcomponent" in error_msg or 
            "deprecated pattern" in error_msg or
            "process_item" in error_msg or
            "must inherit" in error_msg or
            "class name" in error_msg):
            return ErrorType.PATTERN_ERROR
        
        # Check for placeholder validation errors - need logic implementation
        if ("placeholder" in error_msg or 
            "notimplementederror" in error_msg or 
            "todo" in error_msg or
            "forbidden pattern" in error_msg or
            "dummy" in error_msg or
            "mock" in error_msg or
            "test data" in error_msg):
            return ErrorType.VALIDATION_ERROR
        
        # Check for API-specific errors
        if ("timeout" in error_msg or "timed out" in error_msg or
            "connection" in error_msg or "network" in error_msg or
            "api" in error_type_name or "http" in error_msg or
            "rate limit" in error_msg or "quota" in error_msg or
            "internal server error" in error_msg or "500" in error_msg or
            "502" in error_msg or "503" in error_msg or "504" in error_msg or
            "network error" in error_msg or "connection error" in error_msg or
            "connection refused" in error_msg or "connection timeout" in error_msg or
            "ssl error" in error_msg or "tls error" in error_msg):
            return ErrorType.API_ERROR
        
        # Default to validation error for unknown errors
        return ErrorType.VALIDATION_ERROR
    
    def build_adaptive_prompt(self, base_prompt: str, validation_feedback: str, 
                             attempt: int, o3_reasoning_prefix: str = "") -> str:
        """
        Build adaptive prompt that includes validation feedback from previous attempts with o3 optimization
        
        Args:
            base_prompt: The original prompt
            validation_feedback: Feedback from previous validation failures
            attempt: Current attempt number
            o3_reasoning_prefix: Optional O3-specific reasoning prefix
            
        Returns:
            Enhanced prompt with validation feedback
        """
        
        if attempt == 0 or not validation_feedback:
            return base_prompt
        
        # Use o3-specific reasoning for retry attempts
        reasoning_retry = o3_reasoning_prefix
            
        # Analyze validation feedback to provide more specific guidance
        specific_fixes = []
        if "syntax" in validation_feedback.lower() or "syntaxerror" in validation_feedback.lower():
            specific_fixes.append("- SYNTAX ERROR DETECTED: Check all parentheses, brackets, and quotes are balanced")
            specific_fixes.append("- Ensure all regex patterns have escaped parentheses: use \\) not )")
            specific_fixes.append("- Verify proper indentation (4 spaces per level)")
            specific_fixes.append("- Example: Change re.compile(r'pattern)') to re.compile(r'pattern\\)')")
        if "unbalanced parenthesis" in validation_feedback.lower():
            specific_fixes.append("- UNBALANCED PARENTHESIS: Count all ( and ) to ensure they match")
            specific_fixes.append("- Check regex patterns - they often have unescaped parentheses")
            specific_fixes.append("- Look for missing closing parentheses in function calls")
            specific_fixes.append("- Example: if re.search(r'pattern)', text) should be if re.search(r'pattern\\)', text)")
        if "notimplementederror" in validation_feedback.lower():
            specific_fixes.append("- FORBIDDEN PATTERN: Remove ALL raise NotImplementedError statements")
            specific_fixes.append("- Replace with real implementation logic")
            specific_fixes.append("- Example: Instead of 'raise NotImplementedError', return actual data like {'result': 'processed'}")
        if "placeholder" in validation_feedback.lower() or "dummy" in validation_feedback.lower():
            specific_fixes.append("- PLACEHOLDER DETECTED: Remove all dummy/test values")
            specific_fixes.append("- Implement real business logic with meaningful data")
            specific_fixes.append("- Example: Instead of {'test': True}, return {'users': [actual_user_data]}")
        
        fixes_text = "\n".join(specific_fixes) if specific_fixes else ""
        
        # Add specific validation feedback to prompt
        adaptive_section = f"""

{reasoning_retry}CRITICAL: Previous attempt failed validation. You MUST fix these specific issues:

{validation_feedback}

SPECIFIC FIXES REQUIRED:
{fixes_text}

VALIDATION REQUIREMENTS:
- NO placeholder code (e.g., return {{"value": 42}}, pass, NotImplementedError)
- NO empty methods or classes  
- ALL methods must have real business logic implementation
- NO TODO comments or placeholder text in code
- CODE must be syntactically correct and complete

Please generate a corrected implementation that addresses ALL validation errors above.

Examples of correct business logic:
- For Sources: Generate real data like {{"id": str(uuid.uuid4()), "timestamp": time.time(), "data": {{...}}}}
- For Transformers: Apply actual transformations like data filtering, calculations, format conversion
- For Models: Implement real inference logic with confidence scores
- For Stores: Persist data to storage with proper error handling
- For APIEndpoints: Return real data structures like {{"users": [users_list], "status": "success"}}

CRITICAL SYNTAX REQUIREMENTS:
- ALWAYS use proper parentheses matching: ( ) must be balanced
- NEVER use placeholder returns like return {{"value": 42}}
- ALWAYS implement real business logic in methods
- ENSURE all function definitions end with proper indentation
- CHECK that all imports are valid and used correctly

FINAL VALIDATION BEFORE RESPONDING:
1. Count all opening parentheses ( - must equal closing parentheses )
2. Count all opening brackets [ - must equal closing brackets ]
3. Count all opening braces {{ - must equal closing braces }}
4. Verify all strings have matching quotes
5. Check all regex patterns have escaped closing parentheses \\)
6. Ensure 4-space indentation is consistent throughout
7. Confirm all imports are at the top and used in the code
"""
        
        return base_prompt + adaptive_section
    
    def format_validation_feedback(self, validation_result) -> str:
        """
        Format validation errors into clear, actionable feedback for LLM retry
        
        Args:
            validation_result: Validation error or result object
            
        Returns:
            Formatted feedback string
        """
        
        feedback_parts = []
        
        # Handle string error messages (most common case)
        if isinstance(validation_result, str):
            return validation_result
        
        # Handle exception objects
        if isinstance(validation_result, Exception):
            return str(validation_result)
        
        # Handle structured validation result objects
        if hasattr(validation_result, 'placeholder_errors'):
            for error in validation_result.placeholder_errors:
                feedback_parts.append(f"- PLACEHOLDER DETECTED: {error.description} at line {error.line}")
        
        # Syntax errors
        if hasattr(validation_result, 'syntax_errors'):
            for error in validation_result.syntax_errors:
                feedback_parts.append(f"- SYNTAX ERROR: {error.message} at line {error.line}")
        
        # AST validation errors
        if hasattr(validation_result, 'ast_errors'):
            for error in validation_result.ast_errors:
                feedback_parts.append(f"- CODE STRUCTURE ERROR: {error.description}")
        
        # Method implementation errors
        if hasattr(validation_result, 'method_errors'):
            for error in validation_result.method_errors:
                feedback_parts.append(f"- MISSING IMPLEMENTATION: {error.method_name} - {error.description}")
        
        return "\n".join(feedback_parts) if feedback_parts else "Unknown validation error"
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """
        Determine if retry should be attempted
        
        Args:
            error_type: Type of error that occurred
            attempt: Current attempt number
            
        Returns:
            True if retry should be attempted
        """
        return self.retry_strategy.should_retry(error_type, attempt)
    
    def get_retry_delay(self, attempt: int, error_type: ErrorType) -> float:
        """
        Calculate appropriate delay before retry
        
        Args:
            attempt: Current attempt number
            error_type: Type of error that occurred
            
        Returns:
            Delay in seconds before next retry
        """
        return self.retry_strategy.get_delay(attempt, error_type)
    
    def get_progressive_prompt_improvement(self, attempt: int, component_type: str, 
                                         context: Dict[str, Any], o3_prompt_engine) -> str:
        """
        Get progressively improved prompts based on attempt number
        
        Args:
            attempt: Current attempt number (0-based)
            component_type: Type of component being generated
            context: Context information for generation
            o3_prompt_engine: O3 prompt engine instance for specialized prompts
            
        Returns:
            Improved prompt for current attempt
        """
        if hasattr(o3_prompt_engine, 'get_progressive_prompt'):
            return o3_prompt_engine.get_progressive_prompt(attempt, component_type, context)
        else:
            # Fallback for non-O3 prompt engines
            if attempt <= 1:
                return f"Generate a complete {component_type} component with configuration: {context}"
            else:
                return f"FINAL ATTEMPT: Generate working {component_type} with real business logic. Config: {context}"
    
    def analyze_failure_patterns(self, error_history: list) -> Dict[str, Any]:
        """
        Analyze patterns in generation failures to improve retry strategies
        
        Args:
            error_history: List of previous errors
            
        Returns:
            Analysis of failure patterns
        """
        if not error_history:
            return {"pattern": "no_failures", "recommendations": []}
        
        error_types = [self.classify_error(error) for error in error_history]
        
        # Count error types
        type_counts = {}
        for error_type in error_types:
            type_counts[error_type.value] = type_counts.get(error_type.value, 0) + 1
        
        # Find most common error type
        most_common = max(type_counts.keys(), key=lambda k: type_counts[k])
        
        recommendations = []
        if most_common == ErrorType.SYNTAX_ERROR.value:
            recommendations.append("Focus on syntax validation in prompts")
            recommendations.append("Add explicit syntax checking examples")
        elif most_common == ErrorType.VALIDATION_ERROR.value:
            recommendations.append("Strengthen anti-placeholder prompting")
            recommendations.append("Add more specific business logic examples")
        elif most_common == ErrorType.API_ERROR.value:
            recommendations.append("Consider switching to fallback provider")
            recommendations.append("Increase retry delays for API stability")
        
        return {
            "pattern": most_common,
            "error_counts": type_counts,
            "total_attempts": len(error_history),
            "recommendations": recommendations
        }