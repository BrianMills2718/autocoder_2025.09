"""Port connection validation system."""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from autocoder_cc.observability import get_logger
from autocoder_cc.blueprint_language.validation_result_types import ValidationResult, ValidationSeverity

@dataclass
class Port:
    """Port specification."""
    name: str
    data_type: str
    protocol: str = "async"
    rate: Optional[int] = None  # messages per second
    schema: Optional[Dict[str, Any]] = None

@dataclass
class TraceStep:
    """Single step in message trace."""
    component: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str] = None
    duration_ms: float = 0.0

@dataclass 
class TraceResult:
    """Result of message tracing."""
    steps: List[TraceStep]
    success: bool
    total_duration_ms: float
    dropped_at: Optional[str] = None
    error_at: Optional[str] = None

class PortConnectionValidator:
    """Validate port connections and data flow."""
    
    def __init__(self):
        self.logger = get_logger("PortConnectionValidator")
    
    def validate_connection(self, source_port: Port, target_port: Port) -> ValidationResult:
        """Validate port connection compatibility.
        
        Args:
            source_port: Source port specification
            target_port: Target port specification
            
        Returns:
            ValidationResult with compatibility assessment
        """
        result = ValidationResult(success=True)
        
        # Check data type compatibility
        if not self._types_compatible(source_port.data_type, target_port.data_type):
            result.add_failure(
                f"Incompatible data types: {source_port.data_type} -> {target_port.data_type}",
                ValidationSeverity.ERROR,
                f"{source_port.name} -> {target_port.name}"
            )
        
        # Check protocol compatibility
        if source_port.protocol != target_port.protocol:
            result.add_failure(
                f"Protocol mismatch: {source_port.protocol} != {target_port.protocol}",
                ValidationSeverity.ERROR,
                f"{source_port.name} -> {target_port.name}"
            )
        
        # Check rate compatibility
        if source_port.rate and target_port.rate:
            if not self._rates_compatible(source_port.rate, target_port.rate):
                result.add_failure(
                    f"Rate mismatch may cause backpressure: {source_port.rate} > {target_port.rate}",
                    ValidationSeverity.WARNING,
                    f"{source_port.name} -> {target_port.name}"
                )
        
        # Check schema compatibility
        if source_port.schema and target_port.schema:
            schema_compat = self._schemas_compatible(source_port.schema, target_port.schema)
            if not schema_compat:
                result.add_failure(
                    "Schema incompatibility detected",
                    ValidationSeverity.ERROR,
                    f"{source_port.name} -> {target_port.name}"
                )
        
        return result
    
    def _types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if data types are compatible."""
        # Exact match
        if source_type == target_type:
            return True
        
        # Any type is compatible with everything
        if source_type == 'Any' or target_type == 'Any':
            return True
        
        # Dict/Object compatibility
        if source_type in ['Dict', 'dict', 'object'] and target_type in ['Dict', 'dict', 'object']:
            return True
        
        # List/Array compatibility
        if source_type in ['List', 'list', 'array'] and target_type in ['List', 'list', 'array']:
            return True
        
        return False
    
    def _rates_compatible(self, source_rate: int, target_rate: int) -> bool:
        """Check if message rates are compatible."""
        # Target should be able to handle source rate
        return target_rate >= source_rate
    
    def _schemas_compatible(self, source_schema: Dict, target_schema: Dict) -> bool:
        """Check if schemas are compatible."""
        # Check required fields
        source_required = set(source_schema.get('required', []))
        target_required = set(target_schema.get('required', []))
        
        # Target shouldn't require fields that source doesn't provide
        if not target_required.issubset(source_required):
            return False
        
        # Check property types match
        source_props = source_schema.get('properties', {})
        target_props = target_schema.get('properties', {})
        
        for prop, target_type in target_props.items():
            if prop in source_props:
                if source_props[prop].get('type') != target_type.get('type'):
                    return False
        
        return True
    
    async def test_connection(self, source_component: Any, target_component: Any, 
                            test_data: Dict[str, Any]) -> bool:
        """Test actual data flow between components.
        
        Args:
            source_component: Source component instance
            target_component: Target component instance
            test_data: Test message to send
            
        Returns:
            True if connection works
        """
        try:
            # Connect ports
            connected = await source_component.output_port.connect(target_component.input_port)
            if not connected:
                self.logger.error("Failed to connect ports")
                return False
            
            # Send test message
            sent = await source_component.output_port.send(test_data)
            if sent == 0:
                self.logger.error("Failed to send test message")
                return False
            
            # Wait briefly for processing
            await asyncio.sleep(0.1)
            
            # Check if message was received
            # This assumes target component has a way to check received messages
            if hasattr(target_component, 'last_received'):
                return target_component.last_received is not None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

class DataFlowTracer:
    """Trace data flow through component pipeline."""
    
    def __init__(self):
        self.logger = get_logger("DataFlowTracer")
    
    async def trace_message_flow(self, message: Dict[str, Any], 
                                pipeline: List[Any]) -> TraceResult:
        """Trace message through component pipeline.
        
        Args:
            message: Initial message to trace
            pipeline: List of components in order
            
        Returns:
            TraceResult with flow details
        """
        trace = TraceResult(steps=[], success=True, total_duration_ms=0)
        current_data = message
        
        for component in pipeline:
            import time
            start_time = time.perf_counter()
            
            step = TraceStep(
                component=component.name,
                input_data=current_data.copy() if current_data else {},
                output_data=None
            )
            
            try:
                # Process message through component
                if hasattr(component, 'process'):
                    current_data = await component.process(current_data)
                elif hasattr(component, 'transform'):
                    current_data = await component.transform(current_data)
                else:
                    raise AttributeError(f"Component {component.name} has no process/transform method")
                
                # Check if message was dropped
                if current_data is None:
                    trace.dropped_at = component.name
                    step.output_data = None
                    trace.success = False
                    self.logger.info(f"Message dropped at {component.name}")
                else:
                    step.output_data = current_data.copy() if isinstance(current_data, dict) else current_data
                    
            except Exception as e:
                step.error = str(e)
                trace.error_at = component.name
                trace.success = False
                self.logger.error(f"Error at {component.name}: {e}")
                
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            step.duration_ms = duration_ms
            trace.total_duration_ms += duration_ms
            
            trace.steps.append(step)
            
            # Stop if message was dropped or error occurred
            if current_data is None or step.error:
                break
        
        return trace
    
    def validate_trace(self, trace: TraceResult, expected_path: List[str]) -> ValidationResult:
        """Validate trace matches expected path.
        
        Args:
            trace: Trace result to validate
            expected_path: Expected component path
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(success=True)
        
        # Check all expected components were reached
        actual_path = [step.component for step in trace.steps]
        
        if actual_path != expected_path:
            result.add_failure(
                f"Path mismatch. Expected: {expected_path}, Actual: {actual_path}",
                ValidationSeverity.ERROR
            )
        
        # Check for drops
        if trace.dropped_at:
            result.add_failure(
                f"Message dropped at {trace.dropped_at}",
                ValidationSeverity.ERROR
            )
        
        # Check for errors
        if trace.error_at:
            error_step = next(s for s in trace.steps if s.component == trace.error_at)
            result.add_failure(
                f"Error at {trace.error_at}: {error_step.error}",
                ValidationSeverity.ERROR
            )
        
        # Check performance
        if trace.total_duration_ms > 1000:
            result.add_failure(
                f"Slow processing: {trace.total_duration_ms:.2f}ms > 1000ms",
                ValidationSeverity.WARNING
            )
        
        return result