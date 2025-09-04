#!/usr/bin/env python3
"""
Test that port detection correctly finds ports in main.py
"""
import tempfile
import os
from pathlib import Path
import re

# Create a test main.py with custom port
test_main_py = '''#!/usr/bin/env python3
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9090,
        log_level="info"
    )
'''

# Test the port detection regex
port_match = re.search(r'port=(\d+)', test_main_py)
if port_match:
    port = int(port_match.group(1))
    print(f"✅ Successfully detected port {port} from main.py")
else:
    print("❌ Failed to detect port from main.py")

# Test component port detection
test_component = '''
class MyComponent:
    def __init__(self, config):
        self.port = config.get("port", 8080)
'''

port_match = re.search(r'config\.get\("port",\s*(\d+)\)', test_component)
if port_match:
    port = int(port_match.group(1))
    print(f"✅ Successfully detected port {port} from component config")
else:
    print("❌ Failed to detect port from component")