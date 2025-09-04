import google.generativeai as genai
import time
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel
from .base_provider import LLMProviderInterface, LLMRequest, LLMResponse, LLMProviderError, LLMProviderUnavailableError, LLMProviderRateLimitError

class GeminiProvider(LLMProviderInterface):
    """Google Gemini provider implementation"""
    
    # Cost per 1M tokens (input/output) - Gemini Flash 2.5 pricing
    MODEL_COSTS = {
        "gemini-2.5-flash": (0.075, 0.30),  # $0.075 input, $0.30 output per 1M tokens
        "gemini-1.5-flash": (0.075, 0.30),
        "gemini-1.5-pro": (1.25, 5.00)
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("gemini", config)
        # Try multiple possible API key sources
        self.api_key = (
            config.get("api_key") or
            config.get("google_api_key") or
            os.getenv("GOOGLE_AI_STUDIO_KEY") or
            os.getenv("GEMINI_API_KEY")
        )
        self.default_model = config.get("default_model", "gemini-2.5-flash")
        self.timeout = config.get("timeout", 30)  # Default 30 second timeout
        
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GOOGLE_AI_STUDIO_KEY environment variable or provide api_key in config.")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.default_model)
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API"""
        start_time = time.time()
        model_name = request.model_override or self.default_model
        
        try:
            # Combine system and user prompts for Gemini
            combined_prompt = f"{request.system_prompt}\n\nUser Request: {request.user_prompt}"
            
            # Generate response (run sync method in thread pool)
            def generate_sync():
                # Check if structured output is requested
                if hasattr(request, 'response_schema') and request.response_schema:
                    # Clean the schema to remove unsupported properties
                    schema = request.response_schema
                    if hasattr(schema, 'model_json_schema'):
                        json_schema = schema.model_json_schema()
                        # Remove additionalProperties recursively
                        def clean_schema(obj):
                            if isinstance(obj, dict):
                                # Remove additionalProperties
                                obj.pop('additionalProperties', None)
                                # Recursively clean nested objects
                                for key, value in obj.items():
                                    if isinstance(value, (dict, list)):
                                        clean_schema(value)
                            elif isinstance(obj, list):
                                for item in obj:
                                    clean_schema(item)
                        
                        clean_schema(json_schema)
                        schema = json_schema
                    
                    # Use Gemini API with structured output configuration
                    if model_name != self.default_model:
                        model = genai.GenerativeModel(model_name)
                    else:
                        model = self.client
                    
                    generation_config = genai.types.GenerationConfig(
                        max_output_tokens=request.max_tokens or 4096,
                        temperature=request.temperature,
                        response_mime_type="application/json",
                        response_schema=schema
                    )
                    
                    response = model.generate_content(
                        combined_prompt,
                        generation_config=generation_config
                    )
                    return response, True  # Flag to indicate structured output
                else:
                    # Use old API for regular generation
                    if model_name != self.default_model:
                        model = genai.GenerativeModel(model_name)
                    else:
                        model = self.client
                    
                    generation_config = genai.types.GenerationConfig(
                        max_output_tokens=request.max_tokens or 4096,
                        temperature=request.temperature
                    )
                    
                    response = model.generate_content(
                        combined_prompt,
                        generation_config=generation_config
                    )
                    return response, False  # Flag to indicate regular output
            
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, generate_sync),
                timeout=self.timeout
            )
            response, is_structured = result
            response_time = time.time() - start_time
            
            # Handle response based on type
            if is_structured:
                # For structured output using new API
                response_text = self._extract_structured_response_new(response)
            else:
                # For regular output using old API
                # VALIDATE RESPONSE BEFORE PROCESSING
                is_valid, validation_result = self.validate_response(response)
                if not is_valid:
                    raise LLMProviderError(f"Invalid Gemini response: {validation_result}")
                
                # Use validated text content
                response_text = validation_result
            
            # ROBUST token estimation with comprehensive error handling
            tokens_used = self.safe_token_estimation(combined_prompt, response)
            cost = self.estimate_cost(tokens_used, model_name)
            
            # Update statistics
            self.total_tokens += tokens_used
            self.total_cost += cost
            self.request_count += 1
            
            return LLMResponse(
                content=response_text,
                provider="gemini",
                model=model_name,
                tokens_used=tokens_used,
                cost_usd=cost,
                response_time=response_time,
                metadata={
                    "finish_reason": "stop",
                    "estimated_tokens": True
                }
            )
            
        except asyncio.TimeoutError:
            raise LLMProviderError(f"Gemini request timed out after {self.timeout} seconds")
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                raise LLMProviderRateLimitError(f"Gemini rate limit: {e}")
            elif "api" in error_str or "service" in error_str:
                raise LLMProviderUnavailableError(f"Gemini API error: {e}")
            else:
                raise LLMProviderError(f"Gemini error: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get available Gemini models"""
        return list(self.MODEL_COSTS.keys())
    
    def _extract_structured_response_new(self, response) -> str:
        """Extract structured response from new Gemini API"""
        try:
            # According to the docs, structured responses have a .parsed attribute
            if hasattr(response, 'parsed') and response.parsed is not None:
                
                # The parsed attribute might be a dict or Pydantic model
                if hasattr(response.parsed, 'model_dump_json'):
                    # It's a Pydantic model
                    return response.parsed.model_dump_json()
                elif hasattr(response.parsed, 'json'):
                    # It's a Pydantic model with older API
                    return response.parsed.json()
                elif isinstance(response.parsed, dict):
                    # It's already a dict - convert to JSON
                    import json
                    return json.dumps(response.parsed)
                else:
                    # Try other methods
                    import json
                    if hasattr(response.parsed, 'dict'):
                        return json.dumps(response.parsed.dict())
                    else:
                        # Last resort - try to serialize as-is
                        return json.dumps(response.parsed, default=str)
            
            # Fallback - try to get text and parse as JSON
            if hasattr(response, 'text') and response.text:
                # Validate it's proper JSON
                json.loads(response.text)
                return response.text
            
            raise LLMProviderError("No structured data found in new Gemini API response")
            
        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Invalid JSON in structured response: {e}")
        except Exception as e:
            raise LLMProviderError(f"Error extracting structured response from new API: {e}")
    
    def _extract_structured_response(self, response) -> str:
        """Extract structured response from Gemini response"""
        try:
            # Debug logging
            print(f"DEBUG: Response type: {type(response)}")
            print(f"DEBUG: Response attributes: {dir(response)}")
            
            # First try to get the parsed attribute (Pydantic model)
            if hasattr(response, 'parsed') and response.parsed:
                print(f"DEBUG: Found parsed attribute, type: {type(response.parsed)}")
                # Convert Pydantic model to JSON string
                if hasattr(response.parsed, 'model_dump_json'):
                    return response.parsed.model_dump_json()
                elif hasattr(response.parsed, 'json'):
                    return response.parsed.json()
                else:
                    # Fallback to dict conversion
                    import json
                    return json.dumps(response.parsed.dict() if hasattr(response.parsed, 'dict') else vars(response.parsed))
            
            # If no parsed attribute, try to get the text and validate it's JSON
            if hasattr(response, 'text') and response.text:
                print(f"DEBUG: Using response.text, length: {len(response.text)}")
                # Validate it's proper JSON
                json.loads(response.text)  # This will raise if not valid JSON
                return response.text
            
            # Try candidates approach
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            combined_text = " ".join(text_parts)
                            print(f"DEBUG: Combined text from parts: {combined_text[:200]}...")
                            # Validate it's proper JSON
                            json.loads(combined_text)
                            return combined_text
            
            # Last resort - check if response has _result attribute (internal Gemini structure)
            if hasattr(response, '_result') and hasattr(response._result, 'candidates'):
                print("DEBUG: Trying _result.candidates approach")
                candidates = response._result.candidates
                if candidates and len(candidates) > 0:
                    candidate = candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            part = parts[0]
                            if hasattr(part, 'text'):
                                text = part.text
                                print(f"DEBUG: Got text from _result: {text[:200]}...")
                                # Check if it's JSON
                                try:
                                    json.loads(text)
                                    return text
                                except json.JSONDecodeError:
                                    # Maybe it's wrapped in markdown?
                                    if "```json" in text:
                                        # Extract JSON from markdown
                                        json_start = text.find("```json") + 7
                                        json_end = text.find("```", json_start)
                                        if json_end > json_start:
                                            json_text = text[json_start:json_end].strip()
                                            json.loads(json_text)  # Validate
                                            return json_text
                                    raise
            
            raise LLMProviderError("No structured data found in Gemini response")
            
        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Invalid JSON in structured response: {e}")
        except Exception as e:
            raise LLMProviderError(f"Error extracting structured response: {e}")
    
    def validate_response(self, response) -> tuple[bool, str]:
        """Validate Gemini response before processing"""
        
        if not response:
            return False, "Response is None or empty"
        
        # Check for text content - BE CAREFUL about accessing response.text
        # It can throw "list index out of range" if parts list is empty
        has_text = False
        text_content = ""
        finish_reason = None
        
        try:
            # First, check if we have candidates with parts
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check finish reason for filtering/safety issues
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    # Finish reason codes:
                    # 1 = STOP (normal completion)
                    # 2 = MAX_TOKENS (hit token limit)
                    # 3 = SAFETY (filtered for safety)
                    # 4 = RECITATION (filtered for recitation)
                    # 5 = OTHER (other reason)
                    
                    if finish_reason == 3:
                        return False, "Content was filtered for safety reasons"
                    elif finish_reason == 4:
                        return False, "Content was filtered for recitation/copyright reasons"
                    elif finish_reason == 5:
                        return False, "Content generation failed for other reasons"
                
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        # Safely extract text from parts
                        parts_text = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts_text.append(part.text)
                        if parts_text:
                            text_content = " ".join(parts_text)
                            has_text = True
                    else:
                        # Parts list is empty - this is why we get "list index out of range"
                        if finish_reason == 2:
                            return False, "No content generated - hit maximum token limit"
                        else:
                            return False, f"No content parts generated (finish_reason: {finish_reason})"
            
            # Fallback: try response.text only if parts extraction didn't work
            if not has_text:
                try:
                    if hasattr(response, 'text') and response.text:
                        text_content = response.text
                        has_text = True
                except IndexError:
                    # This is the "list index out of range" error - ignore it
                    pass
                    
        except Exception as e:
            return False, f"Error extracting text from response: {e}"
        
        if not has_text:
            reason_msg = f" (finish_reason: {finish_reason})" if finish_reason is not None else ""
            return False, f"No text content found in response{reason_msg}. Response type: {type(response)}, attributes: {dir(response)}"
        
        if len(text_content.strip()) == 0:
            return False, "Response text is empty or whitespace only"
        
        return True, text_content

    def safe_token_estimation(self, combined_prompt: str, response) -> int:
        """Safely estimate tokens from Gemini response with fallback methods"""
        try:
            # Method 1: Try standard text splitting
            prompt_tokens = len(combined_prompt.split()) if combined_prompt else 0
            
            # Safely extract response text - USE SAME LOGIC AS validate_response
            response_text = ""
            
            try:
                # First, check if we have candidates with parts
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Safely extract text from parts
                            parts_text = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    parts_text.append(part.text)
                            if parts_text:
                                response_text = " ".join(parts_text)
                
                # Fallback: try response.text only if parts extraction didn't work
                if not response_text:
                    try:
                        if hasattr(response, 'text') and response.text:
                            response_text = str(response.text)
                    except IndexError:
                        # This is the "list index out of range" error - ignore it
                        pass
                        
            except Exception:
                # If anything fails, leave response_text empty
                pass
            
            if response_text:
                response_tokens = len(response_text.split())
            else:
                # Fallback: estimate based on character count
                char_count = len(str(response)) if response else 0
                response_tokens = max(char_count // 4, 1)  # Rough estimate: 4 chars per token
            
            total_tokens = prompt_tokens + response_tokens
            
            # Log the estimation method used
            if hasattr(self, 'logger'):
                self.logger.debug(f"Token estimation: prompt={prompt_tokens}, response={response_tokens}, total={total_tokens}")
            
            return total_tokens
            
        except Exception as e:
            # Ultimate fallback: use character-based estimation
            if hasattr(self, 'logger'):
                self.logger.warning(f"Token estimation failed, using fallback: {e}")
            
            prompt_chars = len(combined_prompt) if combined_prompt else 0
            response_chars = len(str(response)) if response else 0
            
            # Conservative estimate: 3 characters per token
            estimated_tokens = max((prompt_chars + response_chars) // 3, 1)
            
            return estimated_tokens

    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for Gemini request"""
        if model not in self.MODEL_COSTS:
            return 0.0
        
        # Assume 70% input, 30% output tokens
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost, output_cost = self.MODEL_COSTS[model]
        
        return (input_tokens * input_cost / 1000000) + (output_tokens * output_cost / 1000000)
    
    async def health_check(self) -> bool:
        """Check Gemini API health using robust validation"""
        try:
            # Simple generation test with timeout (run sync method in thread pool)
            def health_check_sync():
                model = genai.GenerativeModel(self.default_model)
                response = model.generate_content("Hello")
                
                # Use the same robust validation logic as the main generate method
                is_valid, validation_result = self.validate_response(response)
                return is_valid
            
            # Add timeout to prevent hanging
            try:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, health_check_sync),
                    timeout=5.0  # 5 second timeout for health checks
                )
                return result
            except asyncio.TimeoutError:
                # Use logger instead of print for consistency
                if hasattr(self, 'logger'):
                    self.logger.debug("Gemini health check timed out after 5 seconds")
                else:
                    import logging
                    logging.debug("Gemini health check timed out after 5 seconds")
                return False
        except Exception as e:
            # Log the specific error for debugging
            if hasattr(self, 'logger'):
                self.logger.debug(f"Gemini health check failed: {e}")
            else:
                import logging
                logging.debug(f"Gemini health check failed: {e}")
            return False