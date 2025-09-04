#!/usr/bin/env python3
"""
Generation Logger - Enhanced observability for component generation pipeline

This module provides comprehensive logging for the entire component generation
process, capturing:
- LLM prompts and responses
- Template inputs and outputs
- Validation errors with context
- File write operations
- Performance metrics

Author: Claude (Anthropic)
Date: 2025-08-10
"""
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog
import traceback

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


@dataclass
class GenerationEvent:
    """Represents an event in the generation pipeline"""
    timestamp: str
    session_id: str
    component_name: str
    stage: str
    event_type: str  # 'start', 'end', 'error'
    duration_ms: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    traceback: Optional[str] = None


class GenerationLogger:
    """
    Enhanced logger for component generation pipeline.
    
    Provides structured logging with session tracking, performance metrics,
    and detailed error context.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the generation logger.
        
        Args:
            log_dir: Directory to write detailed logs (optional)
        """
        self.logger = structlog.get_logger(__name__)
        self.session_id = str(uuid.uuid4())
        self.log_dir = log_dir or Path("generation_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session log file for detailed capture
        self.session_file = self.log_dir / f"session_{self.session_id}.json"
        self.events: List[GenerationEvent] = []
        
        # Performance tracking
        self.stage_timers: Dict[str, float] = {}
        
        self.logger.info(
            "generation_logger_initialized",
            session_id=self.session_id,
            log_dir=str(self.log_dir)
        )
    
    def start_stage(self, stage: str, component_name: str, **kwargs):
        """
        Mark the start of a generation stage.
        
        Args:
            stage: Name of the stage (e.g., 'llm_prompt', 'template_render')
            component_name: Name of the component being generated
            **kwargs: Additional data to log
        """
        timer_key = f"{component_name}:{stage}"
        self.stage_timers[timer_key] = time.time()
        
        event = GenerationEvent(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            component_name=component_name,
            stage=stage,
            event_type="start",
            data=kwargs
        )
        
        self.events.append(event)
        self.logger.info(
            f"stage_started:{stage}",
            session_id=self.session_id,
            component=component_name,
            stage=stage,
            **kwargs
        )
        
        # Write to session file immediately
        self._append_to_session_file(event)
    
    def end_stage(self, stage: str, component_name: str, **kwargs):
        """
        Mark the end of a generation stage with timing.
        
        Args:
            stage: Name of the stage
            component_name: Name of the component
            **kwargs: Additional data to log (e.g., results)
        """
        timer_key = f"{component_name}:{stage}"
        duration_ms = None
        
        if timer_key in self.stage_timers:
            duration_ms = (time.time() - self.stage_timers[timer_key]) * 1000
            del self.stage_timers[timer_key]
        
        event = GenerationEvent(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            component_name=component_name,
            stage=stage,
            event_type="end",
            duration_ms=duration_ms,
            data=kwargs
        )
        
        self.events.append(event)
        self.logger.info(
            f"stage_completed:{stage}",
            session_id=self.session_id,
            component=component_name,
            stage=stage,
            duration_ms=duration_ms,
            **kwargs
        )
        
        self._append_to_session_file(event)
    
    def log_error(self, stage: str, component_name: str, error: Exception, **kwargs):
        """
        Log an error with full context and traceback.
        
        Args:
            stage: Stage where error occurred
            component_name: Component being generated
            error: The exception that occurred
            **kwargs: Additional context
        """
        timer_key = f"{component_name}:{stage}"
        duration_ms = None
        
        if timer_key in self.stage_timers:
            duration_ms = (time.time() - self.stage_timers[timer_key]) * 1000
            del self.stage_timers[timer_key]
        
        event = GenerationEvent(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            component_name=component_name,
            stage=stage,
            event_type="error",
            duration_ms=duration_ms,
            error=str(error),
            traceback=traceback.format_exc(),
            data=kwargs
        )
        
        self.events.append(event)
        self.logger.error(
            f"stage_error:{stage}",
            session_id=self.session_id,
            component=component_name,
            stage=stage,
            error=str(error),
            error_type=type(error).__name__,
            duration_ms=duration_ms,
            traceback=traceback.format_exc(),
            **kwargs
        )
        
        self._append_to_session_file(event)
    
    def log_llm_interaction(self, 
                           component_name: str,
                           prompt: str,
                           response: str,
                           model: str,
                           tokens_in: Optional[int] = None,
                           tokens_out: Optional[int] = None,
                           **metadata):
        """
        Log a complete LLM interaction with prompt and response.
        
        Args:
            component_name: Component being generated
            prompt: The prompt sent to LLM
            response: The response received
            model: Model name/version used
            tokens_in: Input token count
            tokens_out: Output token count
            **metadata: Additional metadata
        """
        # Truncate for console logging but save full in file
        truncated_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
        truncated_response = response[:500] + "..." if len(response) > 500 else response
        
        self.logger.info(
            "llm_interaction",
            session_id=self.session_id,
            component=component_name,
            model=model,
            prompt_preview=truncated_prompt,
            response_preview=truncated_response,
            prompt_length=len(prompt),
            response_length=len(response),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            **metadata
        )
        
        # Save full interaction to dedicated file
        interaction_file = self.log_dir / f"llm_{self.session_id}_{component_name}.json"
        interaction_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "component": component_name,
            "model": model,
            "prompt": prompt,
            "response": response,
            "tokens": {"input": tokens_in, "output": tokens_out},
            "metadata": metadata
        }
        
        with open(interaction_file, 'w') as f:
            json.dump(interaction_data, f, indent=2)
    
    def log_template_render(self,
                          component_name: str,
                          template_name: str,
                          input_data: Dict[str, Any],
                          output: str,
                          **metadata):
        """
        Log template rendering operation.
        
        Args:
            component_name: Component being generated
            template_name: Name of the template used
            input_data: Variables passed to template
            output: Rendered template output
            **metadata: Additional metadata
        """
        self.logger.info(
            "template_render",
            session_id=self.session_id,
            component=component_name,
            template=template_name,
            input_keys=list(input_data.keys()),
            output_length=len(output),
            output_preview=output[:200] + "..." if len(output) > 200 else output,
            **metadata
        )
        
        # Save full template data
        template_file = self.log_dir / f"template_{self.session_id}_{component_name}.json"
        template_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "component": component_name,
            "template": template_name,
            "input": input_data,
            "output": output,
            "metadata": metadata
        }
        
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
    
    def log_validation_error(self,
                           component_name: str,
                           error_type: str,
                           error_message: str,
                           line_number: Optional[int] = None,
                           code_context: Optional[str] = None,
                           **metadata):
        """
        Log a validation error with context.
        
        Args:
            component_name: Component that failed validation
            error_type: Type of validation error
            error_message: Detailed error message
            line_number: Line number where error occurred
            code_context: Code snippet around error
            **metadata: Additional metadata
        """
        self.logger.error(
            "validation_error",
            session_id=self.session_id,
            component=component_name,
            error_type=error_type,
            error_message=error_message,
            line_number=line_number,
            code_context=code_context,
            **metadata
        )
        
        # Save validation error details
        error_file = self.log_dir / f"validation_error_{self.session_id}_{component_name}.json"
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "component": component_name,
            "error_type": error_type,
            "error_message": error_message,
            "line_number": line_number,
            "code_context": code_context,
            "metadata": metadata
        }
        
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)
    
    def log_file_write(self,
                      component_name: str,
                      file_path: str,
                      content: str,
                      **metadata):
        """
        Log file write operation.
        
        Args:
            component_name: Component being written
            file_path: Path where file is written
            content: Content being written
            **metadata: Additional metadata
        """
        self.logger.info(
            "file_write",
            session_id=self.session_id,
            component=component_name,
            file_path=file_path,
            content_length=len(content),
            content_preview=content[:200] + "..." if len(content) > 200 else content,
            **metadata
        )
        
        # Save file write record
        write_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "component": component_name,
            "file_path": file_path,
            "content_length": len(content),
            "metadata": metadata
        }
        
        writes_file = self.log_dir / f"file_writes_{self.session_id}.jsonl"
        with open(writes_file, 'a') as f:
            f.write(json.dumps(write_record) + '\n')
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the generation session.
        
        Returns:
            Summary statistics and key events
        """
        summary = {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "components_generated": len(set(e.component_name for e in self.events)),
            "errors": [e for e in self.events if e.event_type == "error"],
            "total_duration_ms": sum(e.duration_ms for e in self.events if e.duration_ms),
            "stages": {}
        }
        
        # Aggregate by stage
        for event in self.events:
            if event.stage not in summary["stages"]:
                summary["stages"][event.stage] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "errors": 0
                }
            
            summary["stages"][event.stage]["count"] += 1
            if event.duration_ms:
                summary["stages"][event.stage]["total_duration_ms"] += event.duration_ms
            if event.event_type == "error":
                summary["stages"][event.stage]["errors"] += 1
        
        return summary
    
    def _append_to_session_file(self, event: GenerationEvent):
        """Append event to session file."""
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')


def observable(stage_name: str, capture_args: bool = True, capture_result: bool = True):
    """
    Decorator to make functions observable with automatic logging.
    
    Args:
        stage_name: Name of the stage for logging
        capture_args: Whether to capture function arguments
        capture_result: Whether to capture function result
    
    Usage:
        @observable("llm_generation")
        def generate_component(self, name, spec):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Get or create logger
            if not hasattr(self, '_generation_logger'):
                self._generation_logger = GenerationLogger()
            
            logger = self._generation_logger
            component_name = kwargs.get('component_name', 'unknown')
            
            # Log start
            log_data = {}
            if capture_args:
                log_data['args'] = str(args)[:500]  # Truncate
                log_data['kwargs'] = str(kwargs)[:500]
            
            logger.start_stage(stage_name, component_name, **log_data)
            
            try:
                # Execute function
                result = await func(self, *args, **kwargs)
                
                # Log success
                end_data = {}
                if capture_result and result:
                    if isinstance(result, str):
                        end_data['result_preview'] = result[:500]
                    else:
                        end_data['result_type'] = type(result).__name__
                
                logger.end_stage(stage_name, component_name, **end_data)
                return result
                
            except Exception as e:
                # Log error
                logger.log_error(stage_name, component_name, e)
                raise
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Get or create logger
            if not hasattr(self, '_generation_logger'):
                self._generation_logger = GenerationLogger()
            
            logger = self._generation_logger
            component_name = kwargs.get('component_name', 'unknown')
            
            # Log start
            log_data = {}
            if capture_args:
                log_data['args'] = str(args)[:500]
                log_data['kwargs'] = str(kwargs)[:500]
            
            logger.start_stage(stage_name, component_name, **log_data)
            
            try:
                # Execute function
                result = func(self, *args, **kwargs)
                
                # Log success
                end_data = {}
                if capture_result and result:
                    if isinstance(result, str):
                        end_data['result_preview'] = result[:500]
                    else:
                        end_data['result_type'] = type(result).__name__
                
                logger.end_stage(stage_name, component_name, **end_data)
                return result
                
            except Exception as e:
                # Log error
                logger.log_error(stage_name, component_name, e)
                raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Singleton instance for easy import
_default_logger = None

def get_generation_logger() -> GenerationLogger:
    """Get the default generation logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = GenerationLogger()
    return _default_logger