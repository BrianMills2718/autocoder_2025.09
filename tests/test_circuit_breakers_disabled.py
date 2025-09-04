#!/usr/bin/env python3
"""Test circuit breakers are disabled by default"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autocoder_cc.validation.resilience_patterns import CircuitBreakerConfig, RetryConfig

def test_defaults_disabled():
    """Verify circuit breakers and retry are disabled by default"""
    
    # Test circuit breaker defaults
    cb_config = CircuitBreakerConfig()
    assert cb_config.enabled == False, "Circuit breaker should be disabled by default"
    assert cb_config.failure_threshold == 1, "Failure threshold should be 1 (fail fast)"
    
    # Test retry defaults
    retry_config = RetryConfig()
    assert retry_config.enabled == False, "Retry should be disabled by default"
    assert retry_config.max_attempts == 1, "Max attempts should be 1 (no retry)"
    assert retry_config.jitter == False, "Jitter should be disabled"
    
    print("✅ Circuit breakers disabled by default")
    print("✅ Retry disabled by default")
    return True

def test_llm_component_generator():
    """Test circuit breaker in LLM component generator"""
    
    filepath = "autocoder_cc/blueprint_language/llm_component_generator.py"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check circuit breaker is disabled
        assert "circuit_breaker_enabled = False" in content
        assert "circuit_breaker_threshold = 1" in content
        
        print("✅ LLM component generator circuit breaker disabled")
    
    return True

def test_llm_fallback_disabled():
    """Test LLM fallback is disabled"""
    
    filepath = "autocoder_cc/llm_providers/unified_llm_provider.py"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check fallback is disabled by default
        assert "get('enable_fallback', False)" in content
        
        print("✅ LLM fallback disabled by default")
    
    return True

if __name__ == "__main__":
    test_defaults_disabled()
    test_llm_component_generator()
    test_llm_fallback_disabled()
    print("\n✅ All circuit breaker tests passed")