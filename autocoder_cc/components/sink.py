#!/usr/bin/env python3
"""
Sink component for Autocoder V5.2 System-First Architecture
"""
import anyio
from typing import Dict, Any, Optional, List
from .composed_base import ComposedComponent
from autocoder_cc.error_handling import ConsistentErrorHandler, handle_errors
from autocoder_cc.validation.config_requirement import ConfigRequirement, ConfigType


class Sink(ComposedComponent):
    """
    Sink components output data to external systems using anyio streams.
    Examples: API publishers, message queue producers, notification senders
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "Sink"
        self.collected_data = []
        
        # Note: ConsistentErrorHandler already initialized in ComposedComponent

    @classmethod
    def get_config_requirements(cls) -> List[ConfigRequirement]:
        """Define configuration requirements for Sink component"""
        return [
            ConfigRequirement(
                name="output_destination",
                type="str",
                description="Destination for output data",
                required=True,
                semantic_type=ConfigType.STORAGE_URL,
                example="s3://bucket/output/ or file:///data/output/"
            ),
            ConfigRequirement(
                name="output_format",
                type="str",
                description="Format for output data",
                required=False,
                default="json",
                options=["json", "csv", "parquet", "avro"],
                semantic_type=ConfigType.STRING
            ),
            ConfigRequirement(
                name="batch_write",
                type="bool",
                description="Whether to batch writes for efficiency",
                required=False,
                default=False,
                semantic_type=ConfigType.BOOLEAN
            )
        ]

    
    @handle_errors(component_name="Sink", operation="process")
    async def process(self) -> None:
        """Collect data from input streams and output to external systems."""
        try:
            # Process all available input streams (not just 'input')
            if self.receive_streams:
                async with anyio.create_task_group() as tg:
                    for stream_name, stream in self.receive_streams.items():
                        tg.start_soon(self._process_stream, stream_name, stream)
            else:
                self.logger.warning("No input stream configured")
                
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "operation": "main_process_loop"},
                operation="process"
            )
            self.record_error(str(e))
            raise
    
    async def _process_stream(self, stream_name: str, stream):
        """Process a single input stream using the shared base class method"""
        try:
            await self._process_stream_with_handler(stream_name, stream, self._output_data)
        except Exception as e:
            await self.error_handler.handle_exception(
                e,
                context={"component": self.name, "stream": stream_name, "operation": "process_stream"},
                operation="stream_processing"
            )
            raise
                
    async def _output_data(self, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Default data output implementation for base Sink components.
        Generated components should override this with actual output logic.
        """
        # Check if this is a generated component that should have overridden this method
        class_name = self.__class__.__name__
        if class_name.startswith('Generated'):
            # Generated component - provide working default implementation
            self.logger.info(f"Generated component {class_name} using default file sink")
            
            # Provide working default output for generated components
            output_config = self.config.get("output", {})
            output_type = output_config.get("type", "file")
            
            if output_type == "file":
                # File output implementation
                import json
                import os
                from datetime import datetime
                
                output_dir = output_config.get("directory", "./output")
                os.makedirs(output_dir, exist_ok=True)
                
                filename = output_config.get("filename", f"{self.name}_output.json")
                filepath = os.path.join(output_dir, filename)
                
                # Append data to file with timestamp
                output_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "component": self.name,
                    "data": data
                }
                
                with open(filepath, "a") as f:
                    f.write(json.dumps(output_record) + "\n")
                
                self.logger.info(f"Data written to {filepath}")
                
            elif output_type == "console":
                # Console output implementation
                import json
                print(f"[{self.name}] {json.dumps(data, indent=2)}")
                self.logger.info("Data written to console")
                
            elif output_type == "memory":
                # Memory collection implementation
                if not hasattr(self, "_collected_data"):
                    self._collected_data = []
                self._collected_data.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                })
                self.logger.info(f"Data collected in memory ({len(self._collected_data)} items)")
                
            else:
                # Default: log the data
                self.logger.info(f"Sink output: {data}")
            
            return True
        else:
            # This is a base Sink being used directly - provide logging/collection functionality
            self.logger.info(f"Sink {self.name} collecting data: {inputs}")
            
            # Store data for inspection/debugging
            self.collected_data.append({
                "timestamp": anyio.current_time(),
                "data": inputs,
                "sink_name": self.name
            })
            
            # Limit stored data to prevent memory issues
            if len(self.collected_data) > 1000:
                self.collected_data = self.collected_data[-500:]  # Keep last 500 items
            
            # Apply any configured output processing
            if hasattr(self, 'config') and self.config:
                output_config = self.config.get('output', {})
                if output_config.get('log_level') == 'debug':
                    self.logger.debug(f"Sink {self.name} detailed data: {inputs}")
                if output_config.get('print_to_console'):
                    print(f"[{self.name}] {inputs}")
            
            # Return None since this is a terminal sink (no further output streams)
            return None
    
    @classmethod
    def get_required_config_fields(cls) -> List[ConfigRequirement]:
        """Get list of required configuration fields with full specifications"""
        return [
            ConfigRequirement(
                name="output_destination",
                type="str",
                description="Where to write output data",
                required=True,
                semantic_type=ConfigType.STORAGE_URL,
                example="s3://my-bucket/output/"
            ),
            ConfigRequirement(
                name="output_format",
                type="str",
                description="Format for output data",
                required=False,
                default="json",
                options=["json", "csv", "parquet", "avro", "protobuf", "xml", "plain"],
                depends_on={"output_destination": ["file://", "s3://", "gs://", "hdfs://"]}
            ),
            ConfigRequirement(
                name="batch_size",
                type="int",
                description="Number of records to batch before writing",
                required=False,
                default=100,
                validator=lambda x: x > 0 and x <= 10000
            ),
            ConfigRequirement(
                name="compression",
                type="str",
                description="Compression format for output files",
                required=False,
                default="none",
                options=["none", "gzip", "snappy", "lz4", "zstd"],
                depends_on={"output_format": ["json", "csv", "parquet"]}
            ),
            ConfigRequirement(
                name="partition_by",
                type="list",
                description="Fields to partition data by (for file/object storage)",
                required=False,
                default=[],
                depends_on={"output_destination": ["s3://", "gs://", "hdfs://", "file://"]},
                example=["date", "region"]
            ),
            ConfigRequirement(
                name="schema",
                type="dict",
                description="Schema for data validation and serialization",
                required=False,
                depends_on={"output_format": ["avro", "protobuf", "parquet"]},
                example={"type": "record", "fields": [{"name": "id", "type": "string"}]}
            ),
            ConfigRequirement(
                name="flush_interval",
                type="float",
                description="Interval in seconds to flush buffered data",
                required=False,
                default=10.0,
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="max_file_size",
                type="int",
                description="Maximum size in bytes for output files (triggers rotation)",
                required=False,
                default=1073741824,  # 1GB
                depends_on={"output_destination": ["file://", "s3://", "gs://", "hdfs://"]},
                validator=lambda x: x > 0
            ),
            ConfigRequirement(
                name="authentication",
                type="dict",
                description="Authentication credentials for output destination",
                required=False,
                depends_on={"output_destination": ["s3://", "gs://", "postgres://", "mysql://"]},
                environment_specific=True,
                example={"access_key": "xxx", "secret_key": "yyy"}
            ),
            ConfigRequirement(
                name="retry_config",
                type="dict",
                description="Retry configuration for failed writes",
                required=False,
                default={"max_retries": 3, "backoff_factor": 2, "max_wait": 60},
                example={"max_retries": 5, "backoff_factor": 1.5}
            ),
            ConfigRequirement(
                name="error_handling",
                type="str",
                description="How to handle write errors",
                required=False,
                default="retry",
                options=["retry", "skip", "fail", "dlq"]  # dlq = dead letter queue
            ),
            ConfigRequirement(
                name="dlq_destination",
                type="str",
                description="Dead letter queue destination for failed records",
                required=False,
                depends_on={"error_handling": "dlq"},
                semantic_type=ConfigType.STORAGE_URL,
                example="s3://my-bucket/dlq/"
            ),
            ConfigRequirement(
                name="deduplication",
                type="dict",
                description="Deduplication configuration",
                required=False,
                example={"enabled": True, "key_fields": ["id"], "window_size": 1000}
            ),
            ConfigRequirement(
                name="monitoring",
                type="dict",
                description="Monitoring and alerting configuration",
                required=False,
                default={"metrics_enabled": True, "alert_on_failure": False},
                example={"metrics_enabled": True, "alert_email": "ops@example.com"}
            )
        ]