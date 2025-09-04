# Model Component (Stream-Based Implementation)

## Overview
Machine learning inference component with async model loading and multi-stream processing capabilities.

## Implementation Details
**Base Class**: `ComposedComponent` (from `autocoder_cc.components.composed_base`)  
**File**: `autocoder_cc/components/model.py`  
**Communication**: Uses `receive_streams` and `send_streams` dictionaries  

## Configuration Schema
```yaml
- name: "ml_inference"
  type: "Model"
  config:
    model_type: "passthrough"      # Model type identifier
    transform: "uppercase"         # Optional: data transformation
    model_config: {}              # Model-specific configuration
    add_timestamp: true           # Add processing timestamp
    add_metadata: {}              # Additional metadata to include
```

## Key Features

### Async Model Loading
- **Setup Phase**: Models loaded during component initialization
- **State Tracking**: `model_loaded` boolean tracks loading status
- **Error Handling**: Loading failures prevent component startup

### Multi-Stream Processing
- **Concurrent Streams**: Processes multiple input streams simultaneously using `anyio`
- **Stream Independence**: Each stream processed in separate task
- **Error Isolation**: Stream failures don't affect other streams

### Generated Component Support
- **Base Implementation**: Provides working default for direct usage
- **Generated Override**: Detects generated components and provides enhanced defaults
- **Configuration-Driven**: Supports various transformations via config

## Model Types and Transformations

### Default Passthrough Model
For direct usage of Model component:
```json
{
  "model_output": {"original": "data"},
  "model_name": "ml_inference",
  "model_type": "passthrough",
  "processed_at": "2025-08-03T10:15:30",
  "status": "processed"
}
```

### Generated Component Enhanced Output
For generated Model components:
```json
{
  "predictions": "processed_data",
  "model": "ml_inference",
  "model_type": "classification",
  "confidence": 1.0,
  "processed_at": 1691234567.89,
  "component_class": "GeneratedClassifier"
}
```

### Available Transformations
| Transform Type | Input | Output |
|---|---|---|
| `uppercase` | `"hello"` | `"HELLO"` |
| `count` | `["a","b","c"]` | Adds `item_count: 3` |
| `echo` | `{"data": "test"}` | Adds `echo: {"data": "test"}` |

## Blueprint Examples

### Basic ML Inference Pipeline
```yaml
system:
  name: "ml_pipeline"
  components:
    - name: "data_source"
      type: "Source"
    - name: "ml_model"
      type: "Model"
      config:
        model_type: "classifier"
        transform: "uppercase"
    - name: "result_sink"
      type: "Sink"
      
  bindings:
    - from_component: "data_source"
      to_component: "ml_model"
      stream_name: "input"
    - from_component: "ml_model"
      to_component: "result_sink"
      stream_name: "output"
```

### Multi-Stream ML Processing
```yaml
system:
  name: "multi_stream_ml"
  components:
    - name: "training_data"
      type: "Source"
    - name: "test_data"
      type: "Source"
    - name: "ml_processor"
      type: "Model"
      config:
        model_type: "multi_input"
        add_timestamp: true
    - name: "predictions_sink"
      type: "Sink"
      
  bindings:
    - from_component: "training_data"
      to_component: "ml_processor"
      stream_name: "training"
    - from_component: "test_data"
      to_component: "ml_processor"
      stream_name: "testing"
    - from_component: "ml_processor"
      to_component: "predictions_sink"
      stream_name: "output"
```

### Model with Custom Configuration
```yaml
system:
  name: "configured_model"
  components:
    - name: "enhanced_model"
      type: "Model"
      config:
        model_type: "neural_network"
        model_config:
          layers: 3
          activation: "relu"
          learning_rate: 0.001
        transform: "count"
        add_metadata:
          version: "1.0"
          environment: "production"
      
  bindings:
    - from_component: "data_input"
      to_component: "enhanced_model"
      stream_name: "input"
```

## Advanced Usage

### Custom Model Loading
Override `_load_model()` method in generated components:
```python
async def _load_model(self):
    """Custom model loading logic"""
    model_path = self.config.get('model_path')
    self.model = await load_tensorflow_model(model_path)
    self.model_loaded = True
```

### Custom Inference Logic
Override `_run_inference()` method for actual ML processing:
```python
async def _run_inference(self, inputs):
    """Custom inference implementation"""
    predictions = self.model.predict(inputs['data'])
    return {
        "predictions": predictions.tolist(),
        "confidence": float(np.max(predictions)),
        "model": self.name
    }
```

## Performance Characteristics
- **Model Loading**: One-time cost during component setup
- **Inference Timing**: Automatically tracked and logged in milliseconds
- **Multi-Stream**: Concurrent processing with `anyio` task groups
- **Memory Usage**: Depends on loaded model size and batch processing

## Error Handling
- **Model Loading Failures**: Component fails to start if model cannot load
- **Inference Errors**: Individual inference failures logged with context
- **Stream Errors**: Processing continues on other streams if one fails
- **Comprehensive Logging**: All errors include component name, operation, and context

## Common Issues
**Problem**: Model not loading  
**Solution**: Check `model_loaded` status and review setup logs

**Problem**: "Model not loaded" error during inference  
**Solution**: Ensure `_load_model()` completes successfully and sets `model_loaded = True`

**Problem**: Multi-stream processing not working  
**Solution**: Verify all expected stream names are present in `receive_streams`

## Implementation Notes
- Inherits from `ComposedComponent` for observability integration
- Uses `ConsistentErrorHandler` for comprehensive error management
- Supports both direct usage and generated component patterns
- All processing includes timing information for performance monitoring
- Generated components automatically detected via class name prefix

---
**Last Updated**: 2025-08-03  
**Implementation Status**: ✅ Fully implemented and tested  
**Blueprint Format**: Stream-based (uses `bindings`)  