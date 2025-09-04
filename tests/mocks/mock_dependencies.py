"""Mock dependencies for component validation testing"""

class MockMetricsCollector:
    def increment(self, *args, **kwargs): pass
    def increment_counter(self, *args, **kwargs): pass
    def set_gauge(self, *args, **kwargs): pass
    def record_histogram(self, *args, **kwargs): pass

class MockTracer:
    def start_span(self, *args, **kwargs):
        return MockSpan()

class MockSpan:
    def set_attribute(self, *args, **kwargs): pass
    def set_status(self, *args, **kwargs): pass
    def end(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

class MockLogger:
    def debug(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass

def setup_mock_environment():
    """Set up minimal mock environment for testing"""
    import sys
    
    # Create mock observability module if not present
    if 'observability' not in sys.modules:
        class MockComposedComponent:
            def __init__(self, name, config=None):
                self.name = name
                self.config = config or {}
                self.metrics_collector = MockMetricsCollector()
                self.tracer = MockTracer()
                self.logger = MockLogger()
            
            async def setup(self):
                """Mock setup method"""
                pass
            
            async def cleanup(self):
                """Mock cleanup method"""
                pass
            
            def get_health_status(self):
                """Mock health status"""
                return {"status": "healthy", "component": self.name}
            
            def handle_error(self, error, context=""):
                return {"status": "error", "message": str(error)}
        
        class MockSpanStatus:
            OK = "OK"
            ERROR = "ERROR"
            UNSET = "UNSET"
        
        mock_obs = type(sys)('observability')
        mock_obs.ComposedComponent = MockComposedComponent
        mock_obs.SpanStatus = MockSpanStatus
        sys.modules['observability'] = mock_obs
    
    # Create mock communication module if not present  
    if 'communication' not in sys.modules:
        class MockMessageEnvelope:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        
        class MockComponentCommunicator:
            async def send_to_component(self, source, target, data, port="input"):
                return {"status": "success", "message": "Mock response"}
        
        mock_comm = type(sys)('communication')
        mock_comm.MessageEnvelope = MockMessageEnvelope
        mock_comm.ComponentCommunicator = MockComponentCommunicator
        sys.modules['communication'] = mock_comm