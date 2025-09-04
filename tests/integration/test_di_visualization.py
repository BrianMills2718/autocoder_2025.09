#!/usr/bin/env python3
"""
Test script to verify DI container functionality and generate visualization
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from autocoder_cc.core.dependency_container import EnhancedDependencyContainer
from autocoder_cc.core.dependency_graph import DependencyGraphVisualizer


def test_di_container():
    """Test basic DI container functionality"""
    print("Testing Enhanced Dependency Container...")
    
    # Create container
    container = EnhancedDependencyContainer()
    
    # Define test interfaces
    class ILogger:
        def log(self, msg: str): pass
    
    class IDatabase:
        def connect(self): pass
    
    class IService:
        def process(self): pass
    
    # Define implementations
    class ConsoleLogger(ILogger):
        def log(self, msg: str):
            print(f"[LOG] {msg}")
    
    class PostgresDatabase(IDatabase):
        def __init__(self, logger: ILogger):
            self.logger = logger
            
        def connect(self):
            self.logger.log("Connecting to PostgreSQL")
            return "Connected"
    
    class DataService(IService):
        def __init__(self, database: IDatabase, logger: ILogger):
            self.database = database
            self.logger = logger
            
        def process(self):
            conn = self.database.connect()
            self.logger.log(f"Processing with {conn}")
            return "Processed"
    
    # Register dependencies
    print("\n1. Registering dependencies...")
    container.register_singleton(ILogger, ConsoleLogger)
    container.register_singleton(IDatabase, PostgresDatabase)
    container.register_transient(IService, DataService)
    
    # Resolve and test
    print("\n2. Resolving dependencies...")
    service = container.resolve(IService)
    result = service.process()
    print(f"Result: {result}")
    
    # Check statistics
    print("\n3. Container statistics:")
    stats = container.get_statistics()
    print(f"- Total registrations: {stats['registrations']['total']}")
    print(f"- Singletons: {stats['registrations']['by_lifecycle']['singleton']}")
    print(f"- Transients: {stats['registrations']['by_lifecycle']['transient']}")
    
    # Validate registrations
    print("\n4. Validating registrations...")
    errors = container.validate_registrations()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("✓ All registrations valid")
    
    # Generate dependency graph
    print("\n5. Generating dependency graph...")
    visualizer = DependencyGraphVisualizer(container)
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    results = visualizer.analyze_and_visualize(
        output_dir=output_dir,
        formats=["dot", "report"]  # Skip PNG to avoid matplotlib issues
    )
    
    print(f"✓ Graph analysis saved to {output_dir}")
    print(f"  - DOT file: {results.get('dot_path')}")
    print(f"  - Report: {results.get('report_path')}")
    
    # Print summary
    print("\n6. Registration summary:")
    print(container.export_registration_summary())
    
    print("\n✅ DI Container test completed successfully!")
    return True


if __name__ == "__main__":
    try:
        test_di_container()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)