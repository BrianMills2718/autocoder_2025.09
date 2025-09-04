#!/usr/bin/env python3
"""
Generate demo traces and metrics for OpenTelemetry backend demonstration.
"""

import time
import asyncio
from datetime import datetime
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

from autocoder_cc.core.config import settings


def setup_tracing():
    """Setup OpenTelemetry tracing with Jaeger export"""
    resource = Resource.create({
        "service.name": "autocoder-demo",
        "service.version": "5.2.0",
        "environment": "demo"
    })
    
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer("autocoder.demo", "1.0.0")
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.JAEGER_AGENT_HOST,
        agent_port=settings.JAEGER_AGENT_PORT,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    return tracer


def generate_traces(tracer):
    """Generate sample traces"""
    print("🔍 Generating sample traces...")
    
    # Trace 1: Component processing pipeline
    with tracer.start_as_current_span("component_pipeline") as root_span:
        root_span.set_attribute("component.type", "source")
        root_span.set_attribute("pipeline.id", "demo-001")
        print(f"   📍 Generated trace: {format(root_span.get_span_context().trace_id, '032x')}")
        
        # Simulate data processing
        with tracer.start_as_current_span("data_generation") as gen_span:
            gen_span.set_attribute("records.count", 100)
            time.sleep(0.1)  # Simulate processing
        
        with tracer.start_as_current_span("data_transformation") as transform_span:
            transform_span.set_attribute("transformation.type", "enrichment")
            time.sleep(0.05)  # Simulate processing
        
        with tracer.start_as_current_span("data_storage") as store_span:
            store_span.set_attribute("storage.type", "postgresql")
            store_span.set_attribute("records.stored", 100)
            time.sleep(0.02)  # Simulate processing
    
    # Trace 2: API request handling
    with tracer.start_as_current_span("api_request") as api_span:
        api_span.set_attribute("http.method", "POST")
        api_span.set_attribute("http.route", "/api/v1/process")
        api_span.set_attribute("http.status_code", 200)
        print(f"   📍 Generated trace: {format(api_span.get_span_context().trace_id, '032x')}")
        
        with tracer.start_as_current_span("request_validation") as val_span:
            val_span.set_attribute("validation.result", "passed")
            time.sleep(0.01)
        
        with tracer.start_as_current_span("business_logic") as logic_span:
            logic_span.set_attribute("logic.complexity", "medium")
            time.sleep(0.08)
    
    # Force export
    trace.get_tracer_provider().force_flush(timeout_millis=5000)
    print("   ✅ Traces exported to Jaeger")


def main():
    """Main execution"""
    print("🚀 Starting OpenTelemetry demonstration data generation...")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Setup and generate traces
    tracer = setup_tracing()
    generate_traces(tracer)
    
    print("⏳ Waiting for data to be exported...")
    time.sleep(10)
    
    print("✅ Demo data generation complete!")
    print(f"🔍 Check Jaeger UI at: http://{settings.JAEGER_AGENT_HOST}:16686")
    print(f"📊 Check Prometheus UI at: {settings.get_prometheus_url()}")


if __name__ == "__main__":
    main()