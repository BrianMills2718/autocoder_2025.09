"""
OpenTelemetry Configuration and Logging Suppression
"""
import logging
import os

def configure_otel_logging():
    """Configure OpenTelemetry logging to suppress export warnings in development"""
    # Only show warnings in production
    if os.getenv("ENVIRONMENT", "development") != "production":
        # Suppress OpenTelemetry export warnings
        logging.getLogger("opentelemetry.exporter.otlp.proto.grpc.exporter").setLevel(logging.ERROR)
        logging.getLogger("opentelemetry.exporter.otlp.proto.grpc.trace_exporter").setLevel(logging.ERROR)
        logging.getLogger("opentelemetry.exporter.jaeger").setLevel(logging.ERROR)
        logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.ERROR)
        logging.getLogger("opentelemetry.instrumentation").setLevel(logging.ERROR)
        
        # Also suppress grpc warnings
        logging.getLogger("grpc").setLevel(logging.ERROR)
        logging.getLogger("grpc._channel").setLevel(logging.ERROR)