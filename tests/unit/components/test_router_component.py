#!/usr/bin/env python3
"""
Comprehensive test suite for Router component
Tests all routing functionality including expression, regex, and function conditions
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from autocoder_cc.components.router import Router


class TestRouterComponent:
    """Test suite for Router component functionality"""
    
    def test_router_initialization_with_routing_rules(self):
        """Test Router component initialization with valid routing rules"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"},
                {"condition": "message.type == 'order'", "destination": "order_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        assert router.routing_rules == config["routing_rules"]
        assert router.default_route == config["default_route"]
        assert router.condition_type == "expression"
        assert len(router.routing_rules) == 2
    
    def test_router_initialization_with_default_route_only(self):
        """Test Router component initialization with only default route"""
        config = {
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        assert router.routing_rules == []
        assert router.default_route == config["default_route"]
        assert router.condition_type == "expression"
    
    def test_router_initialization_with_routing_rules_only(self):
        """Test Router component initialization with only routing rules"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ]
        }
        
        router = Router("test_router", config)
        
        assert router.routing_rules == config["routing_rules"]
        assert router.default_route is None
        assert router.condition_type == "expression"
    
    def test_router_initialization_invalid_config(self):
        """Test Router component fails fast with invalid configuration"""
        # No routing rules and no default route
        with pytest.raises(ValueError, match="Router must have either routing_rules or default_route"):
            Router("test_router", {})
        
        # Empty routing rules and no default route
        with pytest.raises(ValueError, match="Router must have either routing_rules or default_route"):
            Router("test_router", {"routing_rules": []})
    
    def test_router_initialization_invalid_rule_structure(self):
        """Test Router component fails fast with invalid rule structure"""
        # Rule not a dictionary
        config = {
            "routing_rules": ["invalid_rule"]
        }
        with pytest.raises(ValueError, match="Routing rule 0 must be a dictionary"):
            Router("test_router", config)
        
        # Rule missing condition
        config = {
            "routing_rules": [{"destination": "user_processor"}]
        }
        with pytest.raises(ValueError, match="Routing rule 0 missing 'condition' field"):
            Router("test_router", config)
        
        # Rule missing destination
        config = {
            "routing_rules": [{"condition": "message.type == 'user'"}]
        }
        with pytest.raises(ValueError, match="Routing rule 0 missing 'destination' field"):
            Router("test_router", config)
    
    def test_router_initialization_invalid_condition_syntax(self):
        """Test Router component validates condition syntax"""
        # Empty condition
        config = {
            "routing_rules": [{"condition": "", "destination": "user_processor"}]
        }
        with pytest.raises(ValueError, match="Empty condition in rule 0"):
            Router("test_router", config)
        
        # Invalid regex pattern
        config = {
            "routing_rules": [{"condition": "[invalid_regex", "destination": "user_processor"}],
            "condition_type": "regex"
        }
        with pytest.raises(ValueError, match="Invalid regex pattern in rule 0"):
            Router("test_router", config)
        
        # Invalid function name
        config = {
            "routing_rules": [{"condition": "123_invalid_function", "destination": "user_processor"}],
            "condition_type": "function"
        }
        with pytest.raises(ValueError, match="Invalid function name in rule 0"):
            Router("test_router", config)
    
    @pytest.mark.asyncio
    async def test_router_expression_condition_evaluation(self):
        """Test Router expression condition evaluation"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"},
                {"condition": "message.priority == 'high'", "destination": "priority_processor"},
                {"condition": "message.count > 10", "destination": "bulk_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test message object with attributes
        class TestMessage:
            def __init__(self, type, priority, count):
                self.type = type
                self.priority = priority
                self.count = count
        
        # Test condition matching
        user_message = TestMessage("user", "normal", 5)
        assert await router.evaluate_condition("message.type == 'user'", user_message) == True
        assert await router.evaluate_condition("message.priority == 'high'", user_message) == False
        assert await router.evaluate_condition("message.count > 10", user_message) == False
        
        # Test high priority message
        priority_message = TestMessage("system", "high", 2)
        assert await router.evaluate_condition("message.type == 'user'", priority_message) == False
        assert await router.evaluate_condition("message.priority == 'high'", priority_message) == True
        assert await router.evaluate_condition("message.count > 10", priority_message) == False
        
        # Test bulk message
        bulk_message = TestMessage("data", "normal", 15)
        assert await router.evaluate_condition("message.type == 'user'", bulk_message) == False
        assert await router.evaluate_condition("message.priority == 'high'", bulk_message) == False
        assert await router.evaluate_condition("message.count > 10", bulk_message) == True
    
    @pytest.mark.asyncio
    async def test_router_dictionary_message_evaluation(self):
        """Test Router expression condition evaluation with dictionary messages"""
        config = {
            "routing_rules": [
                {"condition": "message['type'] == 'user'", "destination": "user_processor"},
                {"condition": "message.get('priority') == 'high'", "destination": "priority_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test dictionary message
        user_message = {"type": "user", "priority": "normal", "count": 5}
        assert await router.evaluate_condition("message['type'] == 'user'", user_message) == True
        assert await router.evaluate_condition("message.get('priority') == 'high'", user_message) == False
        
        # Test priority message
        priority_message = {"type": "system", "priority": "high", "count": 2}
        assert await router.evaluate_condition("message['type'] == 'user'", priority_message) == False
        assert await router.evaluate_condition("message.get('priority') == 'high'", priority_message) == True
    
    @pytest.mark.asyncio
    async def test_router_regex_condition_evaluation(self):
        """Test Router regex condition evaluation"""
        config = {
            "routing_rules": [
                {"condition": r"user_\d+", "destination": "user_processor"},
                {"condition": r"order_[A-Z]+", "destination": "order_processor"}
            ],
            "default_route": "default_processor",
            "condition_type": "regex"
        }
        
        router = Router("test_router", config)
        
        # Test regex matching
        assert await router.evaluate_condition(r"user_\d+", "user_123") == True
        assert await router.evaluate_condition(r"user_\d+", "user_abc") == False
        assert await router.evaluate_condition(r"order_[A-Z]+", "order_ABC") == True
        assert await router.evaluate_condition(r"order_[A-Z]+", "order_123") == False
    
    @pytest.mark.asyncio
    async def test_router_function_condition_evaluation(self):
        """Test Router function condition evaluation"""
        config = {
            "routing_rules": [
                {"condition": "is_dict", "destination": "dict_processor"},
                {"condition": "is_string", "destination": "string_processor"},
                {"condition": "is_empty", "destination": "empty_processor"}
            ],
            "default_route": "default_processor",
            "condition_type": "function"
        }
        
        router = Router("test_router", config)
        
        # Test built-in function conditions
        assert await router.evaluate_condition("is_dict", {"key": "value"}) == True
        assert await router.evaluate_condition("is_dict", "string") == False
        assert await router.evaluate_condition("is_string", "hello") == True
        assert await router.evaluate_condition("is_string", 123) == False
        assert await router.evaluate_condition("is_empty", "") == True
        assert await router.evaluate_condition("is_empty", "data") == False
    
    @pytest.mark.asyncio
    async def test_router_custom_function_condition_evaluation(self):
        """Test Router custom function condition evaluation"""
        def is_large_number(message):
            return isinstance(message, (int, float)) and message > 100
        
        config = {
            "routing_rules": [
                {"condition": "is_large_number", "destination": "large_processor"}
            ],
            "default_route": "default_processor",
            "condition_type": "function",
            "custom_functions": {
                "is_large_number": is_large_number
            }
        }
        
        router = Router("test_router", config)
        
        # Test custom function condition
        assert await router.evaluate_condition("is_large_number", 150) == True
        assert await router.evaluate_condition("is_large_number", 50) == False
        assert await router.evaluate_condition("is_large_number", "string") == False
    
    @pytest.mark.asyncio
    async def test_router_message_routing(self):
        """Test Router message routing logic"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"},
                {"condition": "message.type == 'order'", "destination": "order_processor"},
                {"condition": "message.priority == 'high'", "destination": "priority_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test message routing
        class TestMessage:
            def __init__(self, type, priority):
                self.type = type
                self.priority = priority
        
        # Test user message routing
        user_message = TestMessage("user", "normal")
        destination = await router.route_message(user_message)
        assert destination == "user_processor"
        
        # Test order message routing
        order_message = TestMessage("order", "normal")
        destination = await router.route_message(order_message)
        assert destination == "order_processor"
        
        # Test high priority message routing (should match before type)
        priority_message = TestMessage("system", "high")
        destination = await router.route_message(priority_message)
        assert destination == "priority_processor"
        
        # Test default route
        unknown_message = TestMessage("unknown", "normal")
        destination = await router.route_message(unknown_message)
        assert destination == "default_processor"
    
    @pytest.mark.asyncio
    async def test_router_message_routing_no_default(self):
        """Test Router message routing without default route"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ]
        }
        
        router = Router("test_router", config)
        
        # Test matching message
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        user_message = TestMessage("user")
        destination = await router.route_message(user_message)
        assert destination == "user_processor"
        
        # Test non-matching message (should raise error)
        unknown_message = TestMessage("unknown")
        with pytest.raises(ValueError, match="No routing rule matched and no default route configured"):
            await router.route_message(unknown_message)
    
    @pytest.mark.asyncio
    async def test_router_process_item(self):
        """Test Router process_item method"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test item processing
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        user_message = TestMessage("user")
        result = await router.process_item(user_message)
        
        # Check result structure
        assert isinstance(result, dict)
        assert result["original_message"] == user_message
        assert result["destination"] == "user_processor"
        assert result["router_name"] == "test_router"
        assert "routing_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_router_process_item_invalid_input(self):
        """Test Router process_item with invalid input"""
        config = {
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test None input
        with pytest.raises(ValueError, match="Cannot route None item"):
            await router.process_item(None)
    
    @pytest.mark.asyncio
    async def test_router_routing_statistics(self):
        """Test Router routing statistics collection"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"},
                {"condition": "message.type == 'order'", "destination": "order_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Process multiple messages
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        # Process user messages
        await router.process_item(TestMessage("user"))
        await router.process_item(TestMessage("user"))
        
        # Process order message
        await router.process_item(TestMessage("order"))
        
        # Process unknown message (default route)
        await router.process_item(TestMessage("unknown"))
        
        # Check statistics
        stats = router.get_routing_stats()
        assert stats["total_messages"] == 4
        assert stats["rules_matched"][0] == 2  # user rule matched 2 times
        assert stats["rules_matched"][1] == 1  # order rule matched 1 time
        assert stats["default_route_used"] == 1
        assert stats["routing_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_router_routing_statistics_reset(self):
        """Test Router routing statistics reset"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Process some messages
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        await router.process_item(TestMessage("user"))
        await router.process_item(TestMessage("unknown"))
        
        # Check initial statistics
        stats = router.get_routing_stats()
        assert stats["total_messages"] == 2
        assert stats["rules_matched"][0] == 1
        assert stats["default_route_used"] == 1
        
        # Reset statistics
        router.reset_routing_stats()
        
        # Check reset statistics
        stats = router.get_routing_stats()
        assert stats["total_messages"] == 0
        assert stats["rules_matched"][0] == 0
        assert stats["default_route_used"] == 0
        assert stats["routing_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_router_error_handling(self):
        """Test Router error handling during condition evaluation"""
        config = {
            "routing_rules": [
                {"condition": "message.nonexistent_field == 'value'", "destination": "processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test with message that doesn't have the field
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        test_message = TestMessage("user")
        
        # Should use default route when condition evaluation fails
        destination = await router.route_message(test_message)
        assert destination == "default_processor"
        
        # Statistics should show no rule matches
        stats = router.get_routing_stats()
        assert stats["rules_matched"][0] == 0
        assert stats["default_route_used"] == 1
    
    @pytest.mark.asyncio
    async def test_router_performance(self):
        """Test Router performance under load"""
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"},
                {"condition": "message.type == 'order'", "destination": "order_processor"},
                {"condition": "message.priority == 'high'", "destination": "priority_processor"}
            ],
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Create test messages
        class TestMessage:
            def __init__(self, type, priority):
                self.type = type
                self.priority = priority
        
        messages = [
            TestMessage("user", "normal"),
            TestMessage("order", "normal"),
            TestMessage("system", "high"),
            TestMessage("unknown", "normal")
        ] * 250  # 1000 messages total
        
        # Measure routing performance
        import time
        start_time = time.time()
        
        for message in messages:
            await router.process_item(message)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 1.0  # Should process 1000 messages in < 1 second
        assert router.get_routing_stats()["total_messages"] == 1000
        assert router.get_routing_stats()["routing_errors"] == 0
        
        # Calculate average processing time per message
        avg_processing_time = processing_time / 1000
        assert avg_processing_time < 0.001  # < 1ms per message
    
    @pytest.mark.asyncio
    async def test_router_required_methods(self):
        """Test Router required methods for component registry"""
        config = {
            "default_route": "default_processor"
        }
        
        router = Router("test_router", config)
        
        # Test class methods
        assert Router.get_required_config_fields() == []
        assert Router.get_required_dependencies() == []
        
        # Test instance methods
        assert await router.is_ready() == True
        
        health_status = await router.health_check()
        assert health_status["status"] == "healthy"
        assert health_status["component"] == "Router"
        assert health_status["name"] == "test_router"
        assert "routing_rules" in health_status
        assert "statistics" in health_status
    
    @pytest.mark.asyncio
    async def test_router_readiness_check(self):
        """Test Router readiness check"""
        # Router with rules should be ready
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ]
        }
        router = Router("test_router", config)
        assert await router.is_ready() == True
        
        # Router with default route should be ready
        config = {
            "default_route": "default_processor"
        }
        router = Router("test_router", config)
        assert await router.is_ready() == True
        
        # Router with both should be ready
        config = {
            "routing_rules": [
                {"condition": "message.type == 'user'", "destination": "user_processor"}
            ],
            "default_route": "default_processor"
        }
        router = Router("test_router", config)
        assert await router.is_ready() == True