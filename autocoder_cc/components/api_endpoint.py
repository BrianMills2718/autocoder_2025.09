#!/usr/bin/env python3
"""
APIEndpoint component for Autocoder V5.2 System-First Architecture
"""
import anyio
from typing import Dict, Any, Optional, List
from .composed_base import ComposedComponent
from autocoder_cc.generators.config import generator_settings
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.capabilities.input_sanitizer import InputSanitizer, InputSanitizationError
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


# ComponentGenerationError removed - all components now have working implementations


class APIEndpoint(ComposedComponent):
    """
    APIEndpoint components expose HTTP/WebSocket endpoints using anyio TaskGroup.
    Examples: REST APIs, GraphQL endpoints, WebSocket servers
    
    Key features:
    - Non-blocking server startup within anyio TaskGroup
    - Stream-based input/output for inter-component communication
    - Harness shutdown event handling
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "APIEndpoint"
        self.server = None
        self.port = config.get('port') if config else None
        if self.port is None:
            raise ValueError(f"APIEndpoint {name} requires 'port' in configuration - no default port assigned")
        self.host = config.get('host', '0.0.0.0') if config else '0.0.0.0'
        self._server_task = None
        
        # Setup consistent error handling
        self.error_handler = ConsistentErrorHandler(self.name)
        
        # Setup input sanitization for enhanced security
        self.input_sanitizer = InputSanitizer(strict_mode=True)

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for APIEndpoint component"""
        return [
            ConfigRequirement(
                name="endpoint_path",
                type="str",
                description="API endpoint path",
                required=True,
                semantic_type=ConfigType.STRING,
                example="/api/v1/data"
            ),
            ConfigRequirement(
                name="http_methods",
                type="list",
                description="Allowed HTTP methods",
                required=False,
                default=["GET", "POST"],
                semantic_type=ConfigType.LIST
            ),
            ConfigRequirement(
                name="port",
                type="int",
                description="Port to listen on",
                required=False,
                default=8080,
                semantic_type=ConfigType.NETWORK_PORT,
                validator=lambda x: 1024 <= x <= 65535
            )
        ]

    
    @handle_errors(component_name="APIEndpoint", operation="setup")
    async def setup(self, harness_context=None):
        """Setup the API endpoint - start server in background"""
        try:
            await super().setup(harness_context)
            await self._start_component()
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "server_setup", "port": self.port},
                operation="setup"
            )
            raise
    
    @handle_errors(component_name="APIEndpoint", operation="cleanup")
    async def cleanup(self):
        """Cleanup the API endpoint - stop server"""
        try:
            await self._stop_component()
            await super().cleanup()
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "server_cleanup"},
                operation="cleanup"
            )
            # Don't re-raise during cleanup to avoid masking original errors
            self.logger.error(f"Cleanup error (ignored): {e}")
    
    async def _start_component(self):
        """Start API server in non-blocking mode"""
        await self._start_server()
    
    async def _stop_component(self):
        """Stop API server"""
        await self._stop_server()
    
    @handle_errors(component_name="APIEndpoint", operation="process")
    async def process(self) -> None:
        """Handle server and stream processing using anyio structured concurrency."""
        try:
            # Start the server with proper error handling
            if self.server:
                self.logger.info(f"Server started on {getattr(self, 'host', '0.0.0.0')}:{getattr(self, 'port', generator_settings.api_port)}")
                
                # Set up server for graceful shutdown before starting
                self.server.should_exit = False
                
                await self.server.serve()
            else:
                # If no server, just wait for cancellation
                await anyio.sleep_forever()
                    
        except anyio.get_cancelled_exc_class():
            # Normal shutdown via cancellation
            self.logger.info("APIEndpoint process cancelled, shutting down")
            # Ensure server is properly shut down
            if self.server and hasattr(self.server, 'should_exit'):
                self.server.should_exit = True
            raise
        except Exception as e:
            # Handle various cancellation-related exceptions gracefully
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["cancelled", "taskgroup", "shutdown", "sigterm", "sigint"]):
                self.logger.info(f"API endpoint shutdown during system shutdown: {e}")
            else:
                await self.error_handler.handle_exception(
                    e,
                    context={"component": self.name, "server_running": self.server is not None},
                    operation="server_processing"
                )
            
            # Still ensure proper server shutdown
            if self.server and hasattr(self.server, 'should_exit'):
                self.server.should_exit = True
            
    async def _run_server_with_shutdown(self):
        """Run uvicorn server with proper shutdown handling for anyio cancellation"""
        try:
            await self.server.serve()
        except anyio.get_cancelled_exc_class():
            # Handle anyio cancellation properly
            self.logger.info("Server cancelled, initiating shutdown")
            if hasattr(self.server, 'should_exit'):
                self.server.should_exit = True
            # Note: Don't call _stop_server() here as it may cause conflicts
            # The server will shut down naturally when should_exit is set
            raise
        except KeyboardInterrupt:
            # Handle KeyboardInterrupt from signal handlers
            self.logger.info("Server received KeyboardInterrupt, shutting down")
            if hasattr(self.server, 'should_exit'):
                self.server.should_exit = True
            raise
    
    async def _handle_inbound_stream_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle inbound data from other components (optional override).
        
        While most API endpoints primarily generate data outbound from HTTP requests,
        some API endpoints may need to process incoming data from other components
        in the pipeline, such as:
        
        - Storing data for later retrieval via GET endpoints
        - Processing background data and exposing it via real-time APIs
        - Forwarding processed data to downstream systems
        - Aggregating data from multiple sources for API responses
        
        Default implementation is passthrough. Override this method only if your
        API endpoint needs to process inbound stream data.
        
        Args:
            data: Data received from connected input streams
            
        Returns:
            Optional processed data to send to output streams, or None to ignore
        """
        return data  # Default passthrough behavior
    
    def validate_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize incoming request data.
        
        This method provides comprehensive input validation for API endpoints,
        protecting against injection attacks and malformed data.
        
        Args:
            request_data: Raw request data from API endpoint
            
        Returns:
            Sanitized and validated request data
            
        Raises:
            InputSanitizationError: If critical security violations are detected
        """
        try:
            sanitized_data = self.input_sanitizer.validate_request_data(request_data)
            
            # Log validation summary for monitoring
            summary = self.input_sanitizer.get_violation_summary()
            if summary["total_violations"] > 0:
                self.logger.warning(
                    f"Input validation found {summary['total_violations']} issues: "
                    f"{summary['critical_count']} critical, {summary['by_severity']}"
                )
            
            return sanitized_data
            
        except InputSanitizationError as e:
            # Log detailed violation information
            self.logger.error(f"Critical input validation failure: {e}")
            for violation in e.violations:
                self.logger.error(
                    f"  - {violation.field_name}: {violation.description} "
                    f"(severity: {violation.severity.value})"
                )
            
            # Re-raise for component to handle
            raise
    
    def sanitize_json_request(self, json_body: str) -> Dict[str, Any]:
        """
        Parse and sanitize JSON request body.
        
        Args:
            json_body: Raw JSON string from request
            
        Returns:
            Parsed and sanitized JSON data
            
        Raises:
            InputSanitizationError: If JSON is invalid or contains security violations
        """
        from autocoder_cc.capabilities.input_sanitizer import validate_json_request
        return validate_json_request(json_body)
    
    def validate_query_parameters(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize URL query parameters.
        
        Args:
            query_params: Dictionary of query parameters
            
        Returns:
            Sanitized query parameters
        """
        # Query parameters need special handling for URL encoding
        from autocoder_cc.capabilities.input_sanitizer import SanitizationType
        
        return self.input_sanitizer.sanitize_input(
            query_params,
            "query_params",
            [
                SanitizationType.LENGTH_LIMIT,
                SanitizationType.URL_ENCODE,
                SanitizationType.XSS_PREVENTION,
                SanitizationType.SQL_ESCAPE
            ]
        )
    
    def validate_path_parameters(self, path_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize URL path parameters.
        
        Args:
            path_params: Dictionary of path parameters
            
        Returns:
            Sanitized path parameters
        """
        # Path parameters should be checked for path traversal attacks
        sanitized = self.input_sanitizer.sanitize_input(path_params, "path_params")
        
        # Additional path traversal check
        for param_name, param_value in sanitized.items():
            if isinstance(param_value, str):
                self.input_sanitizer._check_path_traversal(param_value, f"path_params.{param_name}")
        
        return sanitized
    
    async def _start_server(self):
        """
        API server startup - fails immediately if component is not properly implemented.
        """
        # Check if this is a generated component that should have overridden this method
        class_name = self.__class__.__name__
        if class_name.startswith('Generated'):
            # Generated components must override _start_server - no lazy implementations allowed
            raise RuntimeError(f"Generated component {class_name} must implement proper _start_server method - no default implementations provided. Component generation failed to provide specific API routes.")
        else:
            # Base APIEndpoint must not be used directly - component must be properly generated
            raise RuntimeError(f"APIEndpoint {self.name} cannot be started - base APIEndpoint requires proper component generation, no fallback allowed")
    
    async def _stop_server(self):
        """
        API server shutdown - fails fast if server is not properly initialized.
        """
        # Check if server is properly initialized
        if hasattr(self, 'server') and self.server:
            # Stop the server
            if hasattr(self.server, 'stop'):
                await self.server.stop()
            elif hasattr(self.server, 'should_exit'):
                self.server.should_exit = True
            self.logger.info(f"Server stopped for {self.name}")
        else:
            # Check if this is a generated component that should have overridden this method
            class_name = self.__class__.__name__
            if class_name.startswith('Generated'):
                # This is a generated component that failed to implement _stop_server
                self.logger.error(f"Generated component {class_name} missing _stop_server implementation")
                self.record_error("Component generation incomplete: _stop_server not implemented")
                # FAIL-FAST: Generated components must implement _stop_server
                raise NotImplementedError(
                    f"Generated component {class_name} must implement _stop_server method. "
                    f"Component generation is incomplete and cannot proceed."
                )
            else:
                # Base APIEndpoint should not be used directly - no graceful handling
                raise RuntimeError(f"No server instance found for {self.name} - component was not properly initialized or is being used incorrectly")