from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from autocoder_cc.validation.config_requirement import ConfigRequirement
from autocoder_cc.validation.pipeline_context import PipelineContext, ValidationError

class HealingStrategy(ABC):
    """Base class for healing strategies"""
    
    @abstractmethod
    def can_heal(self, error: ValidationError, requirement: Optional[ConfigRequirement]) -> bool:
        """Check if this strategy can heal the given error"""
        pass
    
    @abstractmethod
    def heal(
        self,
        error: ValidationError,
        requirement: Optional[ConfigRequirement],
        context: PipelineContext
    ) -> Any:
        """Attempt to heal the error and return the healed value"""
        pass

class DefaultValueStrategy(HealingStrategy):
    """Use default values from requirements - FASTEST, NO LLM"""
    
    def can_heal(self, error: ValidationError, requirement: Optional[ConfigRequirement]) -> bool:
        return (
            error.error_type == "missing" and
            requirement and
            requirement.default is not None
        )
    
    def heal(
        self,
        error: ValidationError,
        requirement: Optional[ConfigRequirement],
        context: PipelineContext
    ) -> Any:
        default_value = requirement.default
        
        # Check for resource conflicts before returning default
        if self._has_conflict(error.field, default_value, context):
            # Return None to indicate this strategy cannot heal (trigger next strategy)
            return None
        
        return default_value
    
    def _has_conflict(self, field: str, value: Any, context: PipelineContext) -> bool:
        """Check if the value conflicts with already used resources"""
        if not hasattr(context, 'used_resources') or not context.used_resources:
            return False
        
        # Check port conflicts
        if field in ['port', 'server_port', 'listen_port', 'bind_port']:
            if value in context.used_resources.get('ports', set()):
                return True
        
        # Check database URL conflicts
        if field in ['database_url', 'db_url', 'connection_string', 'postgres_url', 'mysql_url']:
            if value in context.used_resources.get('database_urls', set()):
                return True
        
        # Check file path conflicts
        if field in ['file_path', 'output_path', 'log_path', 'data_file', 'output_file']:
            if value in context.used_resources.get('file_paths', set()):
                return True
        
        # Check API path conflicts
        if field in ['base_path', 'api_path', 'endpoint', 'route']:
            if value in context.used_resources.get('api_paths', set()):
                return True
        
        # Check queue/topic name conflicts
        if field in ['queue_name', 'queue', 'topic_name', 'topic', 'channel']:
            queue_names = context.used_resources.get('queue_names', set())
            topic_names = context.used_resources.get('topic_names', set())
            if value in queue_names or value in topic_names:
                return True
        
        return False

class ExampleBasedStrategy(HealingStrategy):
    """Use examples from requirements - FAST, NO LLM"""
    
    def can_heal(self, error: ValidationError, requirement: Optional[ConfigRequirement]) -> bool:
        return (
            error.error_type == "missing" and
            requirement and
            requirement.example is not None
        )
    
    def heal(
        self,
        error: ValidationError,
        requirement: Optional[ConfigRequirement],
        context: PipelineContext
    ) -> Any:
        # Parse example and return appropriate value
        import json
        try:
            example_value = json.loads(requirement.example)
        except:
            example_value = requirement.example
        
        # Check for resource conflicts before returning example
        if self._has_conflict(error.field, example_value, context):
            # Return None to indicate this strategy cannot heal (trigger next strategy)
            return None
        
        return example_value
    
    def _has_conflict(self, field: str, value: Any, context: PipelineContext) -> bool:
        """Check if the value conflicts with already used resources"""
        if not hasattr(context, 'used_resources') or not context.used_resources:
            return False
        
        # Check port conflicts
        if field in ['port', 'server_port', 'listen_port', 'bind_port']:
            if value in context.used_resources.get('ports', set()):
                return True
        
        # Check database URL conflicts
        if field in ['database_url', 'db_url', 'connection_string', 'postgres_url', 'mysql_url']:
            if value in context.used_resources.get('database_urls', set()):
                return True
        
        # Check file path conflicts
        if field in ['file_path', 'output_path', 'log_path', 'data_file', 'output_file']:
            if value in context.used_resources.get('file_paths', set()):
                return True
        
        # Check API path conflicts
        if field in ['base_path', 'api_path', 'endpoint', 'route']:
            if value in context.used_resources.get('api_paths', set()):
                return True
        
        # Check queue/topic name conflicts
        if field in ['queue_name', 'queue', 'topic_name', 'topic', 'channel']:
            queue_names = context.used_resources.get('queue_names', set())
            topic_names = context.used_resources.get('topic_names', set())
            if value in queue_names or value in topic_names:
                return True
        
        return False

class ContextBasedStrategy(HealingStrategy):
    """Infer values from pipeline context - MODERATE, NO LLM"""
    
    def can_heal(self, error: ValidationError, requirement: Optional[ConfigRequirement]) -> bool:
        # Can heal if we can infer from context
        return error.error_type == "missing" and self._can_infer_from_context(error, requirement)
    
    def heal(
        self,
        error: ValidationError,
        requirement: Optional[ConfigRequirement],
        context: PipelineContext
    ) -> Any:
        # Infer based on component relationships
        if requirement and requirement.semantic_type == "CONNECTION_URL":
            # Infer from upstream components
            if context.upstream_components:
                return f"pipe://{context.upstream_components[0]['name']}"
        
        # Add more inference logic based on semantic types
        # If we can't infer, raise an exception or return a sentinel value
        raise ValueError(f"Cannot infer value for {error.field}")
    
    def _can_infer_from_context(self, error: ValidationError, requirement: Optional[ConfigRequirement]) -> bool:
        return requirement and requirement.semantic_type in ["CONNECTION_URL", "NETWORK_PORT"]