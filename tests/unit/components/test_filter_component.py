#!/usr/bin/env python3
"""
Comprehensive test suite for Filter component
Tests all filtering functionality including conditions, actions, and transformations
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from autocoder_cc.components.filter import Filter


class TestFilterComponent:
    """Test suite for Filter component functionality"""
    
    def test_filter_initialization_basic(self):
        """Test Filter component initialization with basic configuration"""
        config = {
            "filter_conditions": [
                {"condition": "message.type == 'user'", "action": "pass"},
                {"condition": "message.type == 'spam'", "action": "block"}
            ],
            "filter_action": "pass",
            "default_action": "pass"
        }
        
        filter_comp = Filter("test_filter", config)
        
        assert filter_comp.filter_conditions == config["filter_conditions"]
        assert filter_comp.filter_action == "pass"
        assert filter_comp.default_action == "pass"
        assert filter_comp.condition_type == "expression"
        assert len(filter_comp.filter_conditions) == 2
    
    def test_filter_initialization_invalid_config(self):
        """Test Filter component fails fast with invalid configuration"""
        # No filter conditions
        with pytest.raises(ValueError, match="Filter must have filter_conditions configured"):
            Filter("test_filter", {})
        
        # Empty filter conditions
        with pytest.raises(ValueError, match="Filter must have filter_conditions configured"):
            Filter("test_filter", {"filter_conditions": []})
        
        # Invalid filter action
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'"}],
            "filter_action": "invalid"
        }
        with pytest.raises(ValueError, match="Invalid filter_action"):
            Filter("test_filter", config)
        
        # Invalid default action
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'"}],
            "default_action": "invalid"
        }
        with pytest.raises(ValueError, match="Invalid default_action"):
            Filter("test_filter", config)
    
    def test_filter_initialization_invalid_conditions(self):
        """Test Filter component validates condition structure"""
        # Condition not a dictionary
        config = {
            "filter_conditions": ["invalid_condition"]
        }
        with pytest.raises(ValueError, match="Filter condition 0 must be a dictionary"):
            Filter("test_filter", config)
        
        # Condition missing condition field
        config = {
            "filter_conditions": [{"action": "pass"}]
        }
        with pytest.raises(ValueError, match="Filter condition 0 missing 'condition' field"):
            Filter("test_filter", config)
        
        # Invalid action in condition
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "invalid"}]
        }
        with pytest.raises(ValueError, match="Invalid action in filter condition 0"):
            Filter("test_filter", config)
    
    def test_filter_initialization_transform_without_rules(self):
        """Test Filter component fails with transform action but no transformation rules"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "transform"}]
        }
        with pytest.raises(ValueError, match="transformation_rules required when filter_action is 'transform'"):
            Filter("test_filter", config)
    
    def test_filter_initialization_with_transformation_rules(self):
        """Test Filter component initializes with transformation rules"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "transform"}],
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        assert filter_comp.transformation_rules == config["transformation_rules"]
    
    @pytest.mark.asyncio
    async def test_filter_expression_condition_evaluation(self):
        """Test Filter expression condition evaluation"""
        config = {
            "filter_conditions": [
                {"condition": "message.type == 'user'", "action": "pass"},
                {"condition": "message.priority == 'high'", "action": "block"},
                {"condition": "message.count > 10", "action": "transform"}
            ],
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test message object with attributes
        class TestMessage:
            def __init__(self, type, priority, count):
                self.type = type
                self.priority = priority
                self.count = count
        
        # Test condition evaluation
        user_message = TestMessage("user", "normal", 5)
        assert await filter_comp.evaluate_filter("message.type == 'user'", user_message) == True
        assert await filter_comp.evaluate_filter("message.priority == 'high'", user_message) == False
        assert await filter_comp.evaluate_filter("message.count > 10", user_message) == False
        
        # Test high priority message
        priority_message = TestMessage("system", "high", 2)
        assert await filter_comp.evaluate_filter("message.type == 'user'", priority_message) == False
        assert await filter_comp.evaluate_filter("message.priority == 'high'", priority_message) == True
        assert await filter_comp.evaluate_filter("message.count > 10", priority_message) == False
    
    @pytest.mark.asyncio
    async def test_filter_dictionary_message_evaluation(self):
        """Test Filter expression condition evaluation with dictionary messages"""
        config = {
            "filter_conditions": [
                {"condition": "message['type'] == 'user'", "action": "pass"},
                {"condition": "message.get('priority') == 'high'", "action": "block"}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test dictionary message
        user_message = {"type": "user", "priority": "normal", "count": 5}
        assert await filter_comp.evaluate_filter("message['type'] == 'user'", user_message) == True
        assert await filter_comp.evaluate_filter("message.get('priority') == 'high'", user_message) == False
        
        # Test priority message
        priority_message = {"type": "system", "priority": "high", "count": 2}
        assert await filter_comp.evaluate_filter("message['type'] == 'user'", priority_message) == False
        assert await filter_comp.evaluate_filter("message.get('priority') == 'high'", priority_message) == True
    
    @pytest.mark.asyncio
    async def test_filter_regex_condition_evaluation(self):
        """Test Filter regex condition evaluation"""
        config = {
            "filter_conditions": [
                {"condition": r"user_\d+", "action": "pass"},
                {"condition": r"spam_.*", "action": "block"}
            ],
            "condition_type": "regex"
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test regex matching
        assert await filter_comp.evaluate_filter(r"user_\d+", "user_123") == True
        assert await filter_comp.evaluate_filter(r"user_\d+", "user_abc") == False
        assert await filter_comp.evaluate_filter(r"spam_.*", "spam_message") == True
        assert await filter_comp.evaluate_filter(r"spam_.*", "valid_message") == False
    
    @pytest.mark.asyncio
    async def test_filter_function_condition_evaluation(self):
        """Test Filter function condition evaluation"""
        config = {
            "filter_conditions": [
                {"condition": "is_dict", "action": "pass"},
                {"condition": "is_string", "action": "transform"},
                {"condition": "is_empty", "action": "block"}
            ],
            "condition_type": "function",
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test built-in function conditions
        assert await filter_comp.evaluate_filter("is_dict", {"key": "value"}) == True
        assert await filter_comp.evaluate_filter("is_dict", "string") == False
        assert await filter_comp.evaluate_filter("is_string", "hello") == True
        assert await filter_comp.evaluate_filter("is_string", 123) == False
        assert await filter_comp.evaluate_filter("is_empty", "") == True
        assert await filter_comp.evaluate_filter("is_empty", "data") == False
        assert await filter_comp.evaluate_filter("is_numeric", 123) == True
        assert await filter_comp.evaluate_filter("is_numeric", "abc") == False
        assert await filter_comp.evaluate_filter("is_list", [1, 2, 3]) == True
        assert await filter_comp.evaluate_filter("is_list", "string") == False
    
    @pytest.mark.asyncio
    async def test_filter_should_pass_logic(self):
        """Test Filter should_pass method logic"""
        config = {
            "filter_conditions": [
                {"condition": "message.type == 'user'", "action": "pass"},
                {"condition": "message.type == 'spam'", "action": "block"},
                {"condition": "message.priority == 'high'", "action": "transform"}
            ],
            "default_action": "pass",
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test message evaluation
        class TestMessage:
            def __init__(self, type, priority):
                self.type = type
                self.priority = priority
        
        # Test user message (should pass)
        user_message = TestMessage("user", "normal")
        should_pass, action, condition_data = await filter_comp.should_pass(user_message)
        assert should_pass == True
        assert action == "pass"
        assert condition_data is not None
        
        # Test spam message (should block)
        spam_message = TestMessage("spam", "normal")
        should_pass, action, condition_data = await filter_comp.should_pass(spam_message)
        assert should_pass == False
        assert action == "block"
        assert condition_data is not None
        
        # Test high priority message (should transform)
        priority_message = TestMessage("system", "high")
        should_pass, action, condition_data = await filter_comp.should_pass(priority_message)
        assert should_pass == False
        assert action == "transform"
        assert condition_data is not None
        
        # Test unknown message (should use default)
        unknown_message = TestMessage("unknown", "normal")
        should_pass, action, condition_data = await filter_comp.should_pass(unknown_message)
        assert should_pass == True
        assert action == "pass"
        assert condition_data is None
    
    @pytest.mark.asyncio
    async def test_filter_message_transformation(self):
        """Test Filter message transformation"""
        transformation_rules = [
            {"field": "processed", "operation": "set", "value": True},
            {"field": "processed_by", "operation": "set", "value": "filter"},
            {"field": "message", "operation": "append", "value": "_processed"}
        ]
        
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "transform"}],
            "transformation_rules": transformation_rules
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test dictionary message transformation
        message = {"type": "user", "message": "hello"}
        transformed = await filter_comp.transform_message(message)
        
        assert transformed["processed"] == True
        assert transformed["processed_by"] == "filter"
        assert transformed["message"] == "hello_processed"
        assert transformed["type"] == "user"  # Original field preserved
    
    @pytest.mark.asyncio
    async def test_filter_transformation_operations(self):
        """Test Filter transformation operations"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "transform"}],
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test set operation
        message = {"field": "old_value"}
        transformed = await filter_comp.transform_message(message, [
            {"field": "field", "operation": "set", "value": "new_value"}
        ])
        assert transformed["field"] == "new_value"
        
        # Test append operation
        message = {"field": "hello"}
        transformed = await filter_comp.transform_message(message, [
            {"field": "field", "operation": "append", "value": " world"}
        ])
        assert transformed["field"] == "hello world"
        
        # Test prepend operation
        message = {"field": "world"}
        transformed = await filter_comp.transform_message(message, [
            {"field": "field", "operation": "prepend", "value": "hello "}
        ])
        assert transformed["field"] == "hello world"
        
        # Test remove operation
        message = {"field1": "value1", "field2": "value2"}
        transformed = await filter_comp.transform_message(message, [
            {"field": "field1", "operation": "remove"}
        ])
        assert "field1" not in transformed
        assert transformed["field2"] == "value2"
        
        # Test replace operation
        message = {"field": "hello world"}
        transformed = await filter_comp.transform_message(message, [
            {"field": "field", "operation": "replace", "old_value": "world", "new_value": "universe"}
        ])
        assert transformed["field"] == "hello universe"
    
    @pytest.mark.asyncio
    async def test_filter_process_item_pass(self):
        """Test Filter process_item with pass action"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "pass"}],
            "default_action": "pass"
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test passing message
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        user_message = TestMessage("user")
        result = await filter_comp.process_item(user_message)
        
        assert result == user_message  # Should return original message
        assert filter_comp.get_filter_stats()["messages_passed"] == 1
        assert filter_comp.get_filter_stats()["total_messages"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_process_item_block(self):
        """Test Filter process_item with block action"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'spam'", "action": "block"}],
            "default_action": "pass"
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test blocking message
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        spam_message = TestMessage("spam")
        result = await filter_comp.process_item(spam_message)
        
        assert result is None  # Should return None for blocked messages
        assert filter_comp.get_filter_stats()["messages_blocked"] == 1
        assert filter_comp.get_filter_stats()["total_messages"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_process_item_transform(self):
        """Test Filter process_item with transform action"""
        config = {
            "filter_conditions": [{"condition": "message['type'] == 'user'", "action": "transform"}],
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test transforming message
        message = {"type": "user", "content": "hello"}
        result = await filter_comp.process_item(message)
        
        assert result is not None
        assert result["processed"] == True
        assert result["type"] == "user"
        assert result["content"] == "hello"
        assert filter_comp.get_filter_stats()["messages_transformed"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_process_item_route(self):
        """Test Filter process_item with route action"""
        config = {
            "filter_conditions": [
                {"condition": "message['priority'] == 'high'", "action": "route", "destination": "priority_queue"}
            ],
            "default_action": "pass"
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test routing message
        message = {"priority": "high", "content": "urgent"}
        result = await filter_comp.process_item(message)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["original_message"] == message
        assert result["destination"] == "priority_queue"
        assert result["filter_name"] == "test_filter"
        assert "routing_timestamp" in result
        assert filter_comp.get_filter_stats()["messages_routed"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_process_item_none_input(self):
        """Test Filter process_item with None input"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "pass"}]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # None input should be blocked
        result = await filter_comp.process_item(None)
        assert result is None
        assert filter_comp.get_filter_stats()["messages_blocked"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_statistics_tracking(self):
        """Test Filter statistics tracking"""
        config = {
            "filter_conditions": [
                {"condition": "message.type == 'user'", "action": "pass"},
                {"condition": "message.type == 'spam'", "action": "block"}
            ],
            "default_action": "pass"
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Process different message types
        class TestMessage:
            def __init__(self, type):
                self.type = type
        
        # Process user messages
        await filter_comp.process_item(TestMessage("user"))
        await filter_comp.process_item(TestMessage("user"))
        
        # Process spam message
        await filter_comp.process_item(TestMessage("spam"))
        
        # Process unknown message (default action)
        await filter_comp.process_item(TestMessage("unknown"))
        
        # Check statistics
        stats = filter_comp.get_filter_stats()
        assert stats["total_messages"] == 4
        assert stats["messages_passed"] == 3  # 2 user + 1 unknown
        assert stats["messages_blocked"] == 1  # 1 spam
        assert stats["conditions_matched"][0] == 2  # user condition matched 2 times
        assert stats["conditions_matched"][1] == 1  # spam condition matched 1 time
    
    @pytest.mark.asyncio
    async def test_filter_required_methods(self):
        """Test Filter required methods for component registry"""
        config = {
            "filter_conditions": [{"condition": "message.type == 'user'", "action": "pass"}]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Test class methods
        assert Filter.get_required_config_fields() == ["filter_conditions"]
        assert Filter.get_required_dependencies() == []
        
        # Test instance methods
        assert await filter_comp.is_ready() == True
        
        health_status = await filter_comp.health_check()
        assert health_status["status"] == "healthy"
        assert health_status["component"] == "Filter"
        assert health_status["name"] == "test_filter"
        assert health_status["filter_conditions"] == 1
        assert "statistics" in health_status
    
    @pytest.mark.asyncio
    async def test_filter_performance(self):
        """Test Filter performance under load"""
        config = {
            "filter_conditions": [
                {"condition": "message.type == 'user'", "action": "pass"},
                {"condition": "message.type == 'spam'", "action": "block"},
                {"condition": "message.priority == 'high'", "action": "transform"}
            ],
            "transformation_rules": [
                {"field": "processed", "operation": "set", "value": True}
            ]
        }
        
        filter_comp = Filter("test_filter", config)
        
        # Create test messages
        class TestMessage:
            def __init__(self, type, priority):
                self.type = type
                self.priority = priority
        
        messages = [
            TestMessage("user", "normal"),
            TestMessage("spam", "normal"),
            TestMessage("system", "high"),
            TestMessage("unknown", "normal")
        ] * 250  # 1000 messages total
        
        # Measure filtering performance
        import time
        start_time = time.time()
        
        for message in messages:
            await filter_comp.process_item(message)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 1.0  # Should process 1000 messages in < 1 second
        
        # Check statistics
        stats = filter_comp.get_filter_stats()
        assert stats["total_messages"] == 1000
        assert stats["filter_errors"] == 0
        
        # Calculate average processing time per message
        avg_processing_time = processing_time / 1000
        assert avg_processing_time < 0.001  # < 1ms per message