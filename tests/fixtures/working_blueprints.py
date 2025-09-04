#!/usr/bin/env python3
"""
Working Blueprint Examples for Testing

This module contains working blueprint examples copied and adapted from 
customer_analytics.yaml and other working examples. These blueprints
are designed to work with the current system validation requirements.

These fixtures are intended for future E2E tests without mocking.
"""

# Simple Store-API system adapted from customer_analytics.yaml
SIMPLE_STORE_API_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: Simple Store-API system for testing
  autocoder_version: 5.2.0

system:
  name: simple_store_api
  description: Simple two-component system for integration testing
  version: 1.0.0
  
  components:
    - name: test_source
      type: Source
      description: Test data source component
      processing_mode: stream
      inputs: []
      outputs:
        - name: test_data
          schema: TestDataSchema
          description: Test data output
      resources:
        memory: 256
      observability:
        level: basic
        
    - name: test_store
      type: Store  
      description: Test data storage component
      processing_mode: stream
      inputs:
        - name: test_data
          schema: TestDataSchema
          description: Data to store
      outputs: []
      resources:
        memory: 512
        storage: 1
      observability:
        level: basic
        
  bindings:
    - from:
        component: test_source
        output: test_data
      to:
        component: test_store
        input: test_data

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas:
    TestDataSchema:
      type: object
      properties:
        id: 
          type: string
        data: 
          type: object
        timestamp: 
          type: string
"""

# Three-component pipeline adapted from customer_analytics.yaml
THREE_COMPONENT_PIPELINE_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: Three-component pipeline for testing
  autocoder_version: 5.2.0

system:
  name: three_component_pipeline
  description: Source -> Transformer -> Sink pipeline for testing
  version: 1.0.0
  
  components:
    - name: data_source
      type: Source
      description: Data ingestion source
      processing_mode: stream
      inputs: []
      outputs:
        - name: raw_data
          schema: RawDataSchema
          description: Raw data from source
      resources:
        memory: 256
      observability:
        level: basic
        
    - name: data_transformer
      type: Transformer
      description: Data transformation component
      processing_mode: stream
      inputs:
        - name: raw_data
          schema: RawDataSchema
          description: Raw data to transform
      outputs:
        - name: processed_data
          schema: ProcessedDataSchema
          description: Transformed data
      resources:
        memory: 512
      observability:
        level: basic
        
    - name: data_sink
      type: Sink
      description: Data output component
      processing_mode: stream
      inputs:
        - name: processed_data
          schema: ProcessedDataSchema
          description: Processed data to output
      outputs: []
      resources:
        memory: 256
      observability:
        level: basic
        
  bindings:
    - from:
        component: data_source
        output: raw_data
      to:
        component: data_transformer
        input: raw_data
        
    - from:
        component: data_transformer
        output: processed_data
      to:
        component: data_sink
        input: processed_data

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas:
    RawDataSchema:
      type: object
      properties:
        id: 
          type: string
        raw_content: 
          type: string
        timestamp: 
          type: string
          
    ProcessedDataSchema:
      type: object
      properties:
        id: 
          type: string
        processed_content: 
          type: object
        timestamp: 
          type: string
        processing_metadata:
          type: object
"""

# API endpoint system adapted from customer_analytics.yaml
API_ENDPOINT_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: API endpoint system for testing
  autocoder_version: 5.2.0

system:
  name: api_endpoint_system
  description: Simple API endpoint system for testing
  version: 1.0.0
  
  components:
    - name: test_api
      type: APIEndpoint
      description: REST API for testing
      processing_mode: stream
      inputs: []
      outputs: []
      resources:
        ports:
          - port: 8080
            protocol: HTTP
            public: true
        memory: 512
      observability:
        level: detailed
        
  bindings: []

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas: {}
"""

# Store with configuration adapted from customer_analytics.yaml
CONFIGURABLE_STORE_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: Configurable store system for testing
  autocoder_version: 5.2.0

system:
  name: configurable_store_system
  description: Store with comprehensive configuration for testing
  version: 1.0.0
  
  components:
    - name: configurable_store
      type: Store
      description: Highly configurable store component
      processing_mode: stream
      inputs:
        - name: store_requests
          schema: StoreRequestSchema
          description: Store operation requests
      outputs:
        - name: store_responses
          schema: StoreResponseSchema
          description: Store operation responses
      resources:
        memory: 1024
        storage: 5
      observability:
        level: detailed
        
  bindings: []

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas:
    StoreRequestSchema:
      type: object
      properties:
        operation: 
          type: string
          enum: [create, read, update, delete]
        entity_id: 
          type: string
        data: 
          type: object
        timestamp: 
          type: string
          
    StoreResponseSchema:
      type: object
      properties:
        success: 
          type: boolean
        entity_id: 
          type: string
        data: 
          type: object
        message: 
          type: string
        timestamp: 
          type: string
"""

# Minimal working blueprint for basic testing
MINIMAL_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: Minimal working blueprint
  autocoder_version: 5.2.0

system:
  name: minimal_system
  description: Minimal system for basic testing
  version: 1.0.0
  
  components:
    - name: minimal_component
      type: Store
      description: Minimal component for testing
      processing_mode: stream
      inputs: []
      outputs: []
      resources:
        memory: 256
      observability:
        level: basic
        
  bindings: []

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas: {}
"""

# Error handling system for testing failure scenarios
ERROR_HANDLING_BLUEPRINT = """
metadata:
  version: 1.0.0
  author: Test Suite
  description: System with error handling configuration
  autocoder_version: 5.2.0

system:
  name: error_handling_system
  description: System designed to test error handling patterns
  version: 1.0.0
  
  components:
    - name: robust_store
      type: Store
      description: Store with comprehensive error handling
      processing_mode: stream
      inputs:
        - name: error_test_data
          schema: ErrorTestSchema
          description: Data for error testing
      outputs:
        - name: processed_data
          schema: ProcessedDataSchema
          description: Successfully processed data
      resources:
        memory: 512
        storage: 2
      observability:
        level: detailed
        
  bindings: []

  runtime:
    environment: test
    scaling: manual
    health_check: enabled
    
  schemas:
    ErrorTestSchema:
      type: object
      properties:
        test_type: 
          type: string
          enum: [success, failure, timeout]
        data: 
          type: object
        force_error: 
          type: boolean
          
    ProcessedDataSchema:
      type: object
      properties:
        success: 
          type: boolean
        data: 
          type: object
        error_message: 
          type: string
"""

# All available blueprints for easy access
AVAILABLE_BLUEPRINTS = {
    "simple_store_api": SIMPLE_STORE_API_BLUEPRINT,
    "three_component_pipeline": THREE_COMPONENT_PIPELINE_BLUEPRINT,
    "api_endpoint": API_ENDPOINT_BLUEPRINT,
    "configurable_store": CONFIGURABLE_STORE_BLUEPRINT,
    "minimal": MINIMAL_BLUEPRINT,
    "error_handling": ERROR_HANDLING_BLUEPRINT,
}


def get_blueprint(name: str) -> str:
    """
    Get a blueprint by name.
    
    Args:
        name: Blueprint name from AVAILABLE_BLUEPRINTS keys
        
    Returns:
        Blueprint YAML string
        
    Raises:
        KeyError: If blueprint name not found
    """
    if name not in AVAILABLE_BLUEPRINTS:
        available = ", ".join(AVAILABLE_BLUEPRINTS.keys())
        raise KeyError(f"Blueprint '{name}' not found. Available: {available}")
    
    return AVAILABLE_BLUEPRINTS[name]


def list_blueprints() -> list:
    """List all available blueprint names."""
    return list(AVAILABLE_BLUEPRINTS.keys())