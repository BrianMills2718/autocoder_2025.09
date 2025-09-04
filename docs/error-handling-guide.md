# Error Handling Guide

## Common Generated System Issues

### 1. Blueprint Parsing Errors

**Symptom**: System generation fails with schema validation errors

**Common Causes**:
- Invalid schema version format (use "1.0.0" not "1.0")
- Missing required fields in component definitions
- Invalid component types

**Solution**:
```bash
# Check blueprint syntax
python -c "
from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
parser = SystemBlueprintParser()
try:
    result = parser.parse_file('your-blueprint.yaml')
    print('✅ Blueprint valid')
except Exception as e:
    print(f'❌ Blueprint error: {e}')
"
```

### 2. Component Startup Failures

**Symptom**: Generated components fail to start with import errors

**Common Causes**:
- Missing dependencies in requirements.txt
- Incorrect import paths in generated code
- Port conflicts

**Debugging Steps**:
```bash
# Check component can be imported
cd generated_systems/your-system
python -c "from components.your_component import YourComponent; print('✅ Import works')"

# Check port availability
netstat -tulpn | grep :8080  # Check if port 8080 is in use

# Verify all dependencies installed
pip install -r requirements.txt
```

### 3. Database Connection Issues

**Symptom**: Store components fail with database connection errors

**Solutions**:
```python
# For SQLite stores
config:
  storage_type: "database"
  database_type: "sqlite"
  database_url: "sqlite:///./data.db"  # Relative path

# For PostgreSQL stores
config:
  storage_type: "database" 
  database_type: "postgresql"
  database_url: "postgresql://user:password@localhost:5432/dbname"
```

### 4. API Endpoint Not Responding

**Symptom**: HTTP requests to generated API return connection refused

**Debugging Checklist**:
1. Check if process is running: `ps aux | grep python`
2. Verify port binding: `netstat -tulpn | grep :8080`
3. Check logs for startup errors
4. Verify route registration in component code

**Common Fix**:
```python
# Ensure routes are set up in generated APIEndpoint
def setup_routes(self):
    @self.app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    # Add your routes here
```

### 5. Component Communication Failures

**Symptom**: Components start but don't communicate properly

**Debugging Process**:
1. Check stream connections are established
2. Verify component bindings match blueprint
3. Test individual components in isolation

```python
# Debug stream connectivity
component = YourComponent("test", {})
print(f"Receive streams: {component.receive_streams}")
print(f"Send streams: {component.send_streams}")
```

## Error Message Interpretation

### Blueprint Parser Messages

- `"Invalid schema version"` → Use semantic versioning (x.y.z)
- `"Unknown component type"` → Check component is registered
- `"Missing required field"` → Add required config parameters

### Component Runtime Messages

- `"ModuleNotFoundError"` → Check imports and dependencies
- `"Address already in use"` → Port conflict, change port number
- `"Connection refused"` → Service not running or wrong host/port

### Stream Communication Messages

- `"Stream not found"` → Check binding configuration
- `"No receiving component"` → Verify target component is running
- `"Serialization error"` → Check data format compatibility

## Testing Generated Systems

### Systematic Debugging Approach

1. **Smoke Test**: Test critical path first
```bash
# Test basic functionality
curl http://localhost:8080/health
```

2. **Component Isolation**: Test each component individually
```bash
python -c "
from components.store import Store
store = Store('test', {'storage_type': 'memory'})
print('✅ Store component works')
"
```

3. **Integration Test**: Test component communication
```bash
# Start system and test end-to-end workflow
python main.py &
curl -X POST http://localhost:8080/api/test -d '{"data": "test"}'
```

## Performance Debugging

### High Memory Usage
- Check for memory leaks in stream processing
- Monitor connection pool sizes
- Review data structure sizes

### High CPU Usage  
- Profile component processing logic
- Check for infinite loops in stream handlers
- Monitor concurrent request handling

### Slow Response Times
- Check database query performance
- Monitor network latency between components
- Review serialization/deserialization overhead

## Getting Help

### Diagnostic Information to Collect

1. **System Information**:
   - AutoCoder4_CC version
   - Python version
   - Operating system
   - Available memory/CPU

2. **Blueprint and Configuration**:
   - Complete blueprint YAML
   - Environment variables
   - Generated system structure

3. **Error Details**:
   - Complete error messages and stack traces
   - Reproduction steps
   - Expected vs actual behavior

### Reporting Issues

Include this information when reporting problems:
```bash
# Generate diagnostic report
python -c "
import sys, platform, psutil
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Memory: {psutil.virtual_memory().total // (1024**3)}GB')
print(f'CPU cores: {psutil.cpu_count()}')
"
```

---

**Last Updated**: 2025-08-03  
**Related**: [Testing Plan](testing-plan.md), [Developer Guide](developer-guide.md)