#!/usr/bin/env python3
"""
Verbose Logger for Autocoder System Generation

Provides comprehensive, detailed logging of all generation steps, code creation,
validation results, and system activities for full visibility into the process.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import traceback
from autocoder_cc.observability.structured_logging import get_logger


@dataclass
class GenerationStep:
    """A single step in the generation process"""
    step_id: str
    step_name: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, completed, failed
    details: Dict[str, Any] = None
    sub_steps: List['GenerationStep'] = None
    generated_files: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.sub_steps is None:
            self.sub_steps = []
        if self.generated_files is None:
            self.generated_files = []


class VerboseLogger:
    """
    Comprehensive logging system that tracks every detail of system generation.
    
    Features:
    - Hierarchical step tracking
    - Code generation logging with full source
    - File creation tracking
    - Performance metrics
    - Error context and stack traces
    - Real-time console output with progress indicators
    - Structured JSON output for analysis
    """
    
    def __init__(self, log_file: Path, console_level: str = "INFO", file_level: str = "DEBUG"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generation tracking
        self.generation_start_time = time.time()
        self.current_step_stack: List[GenerationStep] = []
        self.completed_steps: List[GenerationStep] = []
        self.file_contents: Dict[str, str] = {}  # Track all generated file contents
        
        # Setup structured logging
        self.setup_logging(console_level, file_level)
        
        # Log session start
        self.log_session_start()
    
    def setup_logging(self, console_level: str, file_level: str):
        """Setup comprehensive logging with both console and file output"""
        
        # Create structured logger (get_logger returns StructuredLogger)
        self.structured_logger = get_logger("VerboseAutocoder")
        
        # Create standard logger for file/console handling
        self.logger = logging.getLogger("VerboseAutocoder")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler with color formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper()))
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(getattr(logging, file_level.upper()))
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Create structured log file for JSON output
        self.structured_log_file = self.log_file.with_suffix('.json')
        
    def log_session_start(self):
        """Log the start of a generation session"""
        session_info = {
            "session_id": f"autocoder_{int(self.generation_start_time)}",
            "start_time": datetime.now().isoformat(),
            "python_version": sys.version,
            "working_directory": str(Path.cwd()),
            "environment": dict(os.environ)
        }
        
        self.logger.info("🚀 AUTOCODER VERBOSE GENERATION SESSION STARTED")
        self.logger.info(f"Session ID: {session_info['session_id']}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"Structured log: {self.structured_log_file}")
        
        # Write structured session info
        self._write_structured_log("session_start", session_info)
    
    def start_step(self, step_id: str, step_name: str, **details) -> GenerationStep:
        """Start a new generation step"""
        step = GenerationStep(
            step_id=step_id,
            step_name=step_name,
            start_time=time.time(),
            details=details
        )
        
        self.current_step_stack.append(step)
        
        # Log with indentation based on nesting level
        indent = "  " * (len(self.current_step_stack) - 1)
        self.logger.info(f"{indent}▶️  {step_name}")
        
        if details:
            for key, value in details.items():
                self.logger.debug(f"{indent}   📋 {key}: {value}")
        
        self._write_structured_log("step_start", {
            "step_id": step_id,
            "step_name": step_name,
            "start_time": step.start_time,
            "nesting_level": len(self.current_step_stack),
            "details": details
        })
        
        return step
    
    def complete_step(self, step_id: str, **completion_details):
        """Complete the current step"""
        if not self.current_step_stack:
            self.logger.error(f"❌ No active step to complete: {step_id}")
            return
        
        step = self.current_step_stack.pop()
        if step.step_id != step_id:
            self.logger.warning(f"⚠️  Step ID mismatch: expected {step.step_id}, got {step_id}")
        
        step.end_time = time.time()
        step.status = "completed"
        step.details.update(completion_details)
        
        duration = step.end_time - step.start_time
        indent = "  " * len(self.current_step_stack)
        
        self.logger.info(f"{indent}✅ {step.step_name} (⏱️ {duration:.2f}s)")
        
        # Log completion details
        if completion_details:
            for key, value in completion_details.items():
                self.logger.debug(f"{indent}   📊 {key}: {value}")
        
        self.completed_steps.append(step)
        
        self._write_structured_log("step_complete", {
            "step_id": step_id,
            "step_name": step.step_name,
            "duration": duration,
            "completion_details": completion_details
        })
    
    def fail_step(self, step_id: str, error: Exception, **failure_details):
        """Fail the current step with error details"""
        if not self.current_step_stack:
            self.logger.error(f"❌ No active step to fail: {step_id}")
            return
        
        step = self.current_step_stack.pop()
        if step.step_id != step_id:
            self.logger.warning(f"⚠️  Step ID mismatch: expected {step.step_id}, got {step_id}")
        
        step.end_time = time.time()
        step.status = "failed"
        step.error_message = str(error)
        step.details.update(failure_details)
        
        duration = step.end_time - step.start_time
        indent = "  " * len(self.current_step_stack)
        
        self.logger.error(f"{indent}❌ {step.step_name} FAILED (⏱️ {duration:.2f}s)")
        self.logger.error(f"{indent}   💥 Error: {error}")
        
        # Log full stack trace
        self.logger.debug(f"{indent}   📜 Stack trace:")
        for line in traceback.format_exception(type(error), error, error.__traceback__):
            self.logger.debug(f"{indent}      {line.rstrip()}")
        
        self.completed_steps.append(step)
        
        self._write_structured_log("step_failed", {
            "step_id": step_id,
            "step_name": step.step_name,
            "duration": duration,
            "error": str(error),
            "error_type": type(error).__name__,
            "stack_trace": traceback.format_exception(type(error), error, error.__traceback__),
            "failure_details": failure_details
        })
    
    def log_file_generated(self, file_path: Union[str, Path], content: str, **metadata):
        """Log a generated file with its full content"""
        file_path = str(file_path)
        
        # Store content for analysis
        self.file_contents[file_path] = content
        
        # Add to current step if active
        if self.current_step_stack:
            self.current_step_stack[-1].generated_files.append(file_path)
        
        indent = "  " * len(self.current_step_stack)
        content_size = len(content)
        line_count = content.count('\n')
        
        self.logger.info(f"{indent}📄 Generated: {file_path}")
        self.logger.info(f"{indent}   📏 Size: {content_size} chars, {line_count} lines")
        
        if metadata:
            for key, value in metadata.items():
                self.logger.debug(f"{indent}   🏷️  {key}: {value}")
        
        # Log content with line numbers (truncated for console, full in file)
        self.logger.debug(f"{indent}   📝 Content:")
        lines = content.split('\n')
        for i, line in enumerate(lines[:20], 1):  # First 20 lines for debug log
            self.logger.debug(f"{indent}      {i:3d}: {line}")
        
        if len(lines) > 20:
            self.logger.debug(f"{indent}      ... ({len(lines) - 20} more lines)")
        
        self._write_structured_log("file_generated", {
            "file_path": file_path,
            "content_size": content_size,
            "line_count": line_count,
            "metadata": metadata,
            "full_content": content  # Full content in structured log
        })
    
    def log_validation_result(self, validation_type: str, result: Dict[str, Any]):
        """Log validation results in detail"""
        indent = "  " * len(self.current_step_stack)
        
        if result.get("success", True):
            self.logger.info(f"{indent}✅ {validation_type}: PASSED")
        else:
            self.logger.error(f"{indent}❌ {validation_type}: FAILED")
        
        # Log validation details
        for key, value in result.items():
            if key == "errors" and isinstance(value, list):
                self.logger.error(f"{indent}   🚨 Errors ({len(value)}):")
                for i, error in enumerate(value, 1):
                    self.logger.error(f"{indent}      {i}. {error}")
            elif key == "warnings" and isinstance(value, list):
                self.logger.warning(f"{indent}   ⚠️  Warnings ({len(value)}):")
                for i, warning in enumerate(value, 1):
                    self.logger.warning(f"{indent}      {i}. {warning}")
            else:
                self.logger.debug(f"{indent}   📊 {key}: {value}")
        
        self._write_structured_log("validation_result", {
            "validation_type": validation_type,
            "result": result
        })
    
    def log_component_generation(self, component_name: str, component_type: str, 
                               generated_code: str, **details):
        """Log component generation with full code"""
        indent = "  " * len(self.current_step_stack)
        
        self.logger.info(f"{indent}🔧 Generating component: {component_name} ({component_type})")
        
        # Log generation details
        for key, value in details.items():
            self.logger.debug(f"{indent}   📋 {key}: {value}")
        
        # Log generated code
        self.logger.debug(f"{indent}   💻 Generated code:")
        lines = generated_code.split('\n')
        for i, line in enumerate(lines[:30], 1):  # First 30 lines
            self.logger.debug(f"{indent}      {i:3d}: {line}")
        
        if len(lines) > 30:
            self.logger.debug(f"{indent}      ... ({len(lines) - 30} more lines)")
        
        self._write_structured_log("component_generated", {
            "component_name": component_name,
            "component_type": component_type,
            "code_size": len(generated_code),
            "line_count": generated_code.count('\n'),
            "details": details,
            "full_code": generated_code
        })
    
    def log_llm_interaction(self, prompt: str, response: str, model: str, **metadata):
        """Log LLM interactions for debugging"""
        indent = "  " * len(self.current_step_stack)
        
        self.logger.info(f"{indent}🤖 LLM Interaction: {model}")
        self.logger.debug(f"{indent}   📤 Prompt ({len(prompt)} chars):")
        
        # Log prompt (first 500 chars)
        prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        for line in prompt_preview.split('\n'):
            self.logger.debug(f"{indent}      > {line}")
        
        self.logger.debug(f"{indent}   📥 Response ({len(response)} chars):")
        
        # Log response (first 500 chars)
        response_preview = response[:500] + "..." if len(response) > 500 else response
        for line in response_preview.split('\n'):
            self.logger.debug(f"{indent}      < {line}")
        
        self._write_structured_log("llm_interaction", {
            "model": model,
            "prompt_size": len(prompt),
            "response_size": len(response),
            "metadata": metadata,
            "full_prompt": prompt,
            "full_response": response
        })
    
    def log_performance_metric(self, metric_name: str, value: Union[int, float], unit: str = ""):
        """Log performance metrics"""
        indent = "  " * len(self.current_step_stack)
        
        self.logger.info(f"{indent}📊 {metric_name}: {value} {unit}")
        
        self._write_structured_log("performance_metric", {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": time.time()
        })
    
    def finalize_session(self):
        """Finalize the logging session and write summary"""
        total_duration = time.time() - self.generation_start_time
        
        # Complete any remaining steps
        while self.current_step_stack:
            step = self.current_step_stack.pop()
            step.end_time = time.time()
            step.status = "incomplete"
            self.completed_steps.append(step)
        
        # Generate summary
        total_steps = len(self.completed_steps)
        completed_steps = len([s for s in self.completed_steps if s.status == "completed"])
        failed_steps = len([s for s in self.completed_steps if s.status == "failed"])
        total_files = len(self.file_contents)
        
        self.logger.info("")
        self.logger.info("🏁 GENERATION SESSION COMPLETED")
        self.logger.info(f"⏱️  Total duration: {total_duration:.2f}s")
        self.logger.info(f"📊 Steps: {completed_steps} completed, {failed_steps} failed, {total_steps} total")
        self.logger.info(f"📄 Files generated: {total_files}")
        
        # Write final structured summary
        summary = {
            "session_summary": {
                "total_duration": total_duration,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "total_files_generated": total_files,
                "end_time": datetime.now().isoformat()
            },
            "all_steps": [self._step_to_dict(step) for step in self.completed_steps],
            "all_files": {path: {"size": len(content), "lines": content.count('\n')} 
                         for path, content in self.file_contents.items()}
        }
        
        # Write complete session log
        with open(self.structured_log_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"📋 Complete session log: {self.structured_log_file}")
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()
    
    def _write_structured_log(self, event_type: str, data: Dict[str, Any]):
        """Write structured log entry"""
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        
        # Append to structured log file
        with open(self.structured_log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + '\n')
    
    def _step_to_dict(self, step: GenerationStep) -> Dict[str, Any]:
        """Convert GenerationStep to dictionary"""
        step_dict = asdict(step)
        step_dict['duration'] = (step.end_time - step.start_time) if step.end_time else None
        return step_dict


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.COLORS['RESET']}"


# Context manager for easy step tracking
class GenerationStepContext:
    """Context manager for automatic step tracking"""
    
    def __init__(self, logger: VerboseLogger, step_id: str, step_name: str, **details):
        self.logger = logger
        self.step_id = step_id
        self.step_name = step_name
        self.details = details
        self.step = None
    
    def __enter__(self):
        self.step = self.logger.start_step(self.step_id, self.step_name, **self.details)
        return self.step
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.complete_step(self.step_id)
        else:
            self.logger.fail_step(self.step_id, exc_val)
        return False  # Don't suppress exceptions


def main():
    """Test the verbose logger"""
    logger = VerboseLogger(Path("./test_verbose_generation.log"))
    
    try:
        # Test step tracking
        with GenerationStepContext(logger, "test_generation", "Test Generation Process"):
            
            with GenerationStepContext(logger, "parse_blueprint", "Parse Blueprint", 
                                     blueprint_file="test.yaml"):
                time.sleep(0.1)  # Simulate work
            
            with GenerationStepContext(logger, "generate_scaffold", "Generate Scaffold"):
                logger.log_file_generated("./main.py", '''#!/usr/bin/env python3
"""Generated system main file"""
import anyio

async def main():
    print("Hello, world!")

if __name__ == "__main__":
    anyio.run(main)
''', component_count=5)
                time.sleep(0.2)
            
            with GenerationStepContext(logger, "generate_components", "Generate Components"):
                logger.log_component_generation("data_source", "Source", '''
class DataSource(Source):
    async def _generate_data(self):
        return {"value": 42}
''', input_schema={"type": "object"})
                time.sleep(0.1)
        
        logger.log_performance_metric("Total Components", 5, "components")
        logger.log_performance_metric("Generation Rate", 25.0, "components/second")
        
    except Exception as e:
        logger.logger.error(f"Test failed: {e}")
    
    finally:
        logger.finalize_session()


if __name__ == "__main__":
    main()