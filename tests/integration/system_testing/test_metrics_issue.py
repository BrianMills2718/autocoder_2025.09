#!/usr/bin/env python3
"""
Test script to reproduce the MetricsCollector issue
"""

def test_system_generator_imports():
    """Test the exact imports used by SystemGenerator"""
    print("Testing SystemGenerator imports...")
    
    # Import exactly as SystemGenerator does
    from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
    
    print("✅ Imports successful")
    
    # Create metrics collector
    structured_logger = get_logger("system_generator", component="SystemGenerator")
    metrics_collector = get_metrics_collector("system_generator")
    tracer = get_tracer("system_generator")
    
    print(f"✅ Created metrics collector: {type(metrics_collector)}")
    print(f"✅ Metrics collector component: {metrics_collector.component_name}")
    
    # Test the problematic method
    print("Testing record_system_generated method...")
    
    if hasattr(metrics_collector, 'record_system_generated'):
        print("✅ record_system_generated method exists")
        
        # Test calling it
        try:
            metrics_collector.record_system_generated()
            print("✅ record_system_generated method call successful")
        except Exception as e:
            print(f"❌ Error calling record_system_generated: {e}")
            return False
    else:
        print("❌ record_system_generated method NOT FOUND")
        print(f"Available methods: {[m for m in dir(metrics_collector) if not m.startswith('_')]}")
        return False
    
    return True

def test_direct_import():
    """Test importing MetricsCollector directly"""
    print("\nTesting direct MetricsCollector import...")
    
    from autocoder_cc.observability.metrics import MetricsCollector
    
    collector = MetricsCollector("test_component")
    print(f"✅ Direct import successful: {type(collector)}")
    
    if hasattr(collector, 'record_system_generated'):
        print("✅ record_system_generated method exists in direct import")
        try:
            collector.record_system_generated()
            print("✅ Direct method call successful")
        except Exception as e:
            print(f"❌ Error in direct method call: {e}")
            return False
    else:
        print("❌ record_system_generated method NOT FOUND in direct import")
        return False
    
    return True

def test_system_generator_creation():
    """Test creating SystemGenerator instance"""
    print("\nTesting SystemGenerator creation...")
    
    try:
        from pathlib import Path
        from blueprint_language.system_generator import SystemGenerator
        
        # Create temporary output directory
        output_dir = Path("/tmp/test_system_generator")
        output_dir.mkdir(exist_ok=True)
        
        # Create SystemGenerator instance
        generator = SystemGenerator(output_dir, verbose_logging=False)
        print("✅ SystemGenerator created successfully")
        
        # Check metrics collector
        print(f"✅ Generator metrics collector: {type(generator.metrics_collector)}")
        
        if hasattr(generator.metrics_collector, 'record_system_generated'):
            print("✅ record_system_generated available in generator")
        else:
            print("❌ record_system_generated NOT available in generator")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating SystemGenerator: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 MetricsCollector Investigation\n")
    
    success = True
    
    success &= test_system_generator_imports()
    success &= test_direct_import() 
    success &= test_system_generator_creation()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")