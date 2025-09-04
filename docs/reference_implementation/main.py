#!/usr/bin/env python3
"""
Reference implementation main entry point.
This is the GOLDEN STANDARD for system orchestration.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import components
from reference_implementation.components.task_store import TaskStore
from reference_implementation.components.task_api import TaskAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TodoSystem:
    """
    Main system orchestrator that follows the actual expected patterns.
    
    Key points:
    - Manages component lifecycle
    - Handles bindings between components
    - Provides graceful shutdown
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the system"""
        self.config = self.load_config(config_path)
        self.components: Dict[str, Any] = {}
        self.tasks: List[asyncio.Task] = []
        self.running = False
        
        logger.info(f"TodoSystem initialized with config: {self.config['system']}")
    
    def load_config(self, config_path: str = None) -> dict:
        """Load system configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                'system': {
                    'name': 'todo_system',
                    'version': '1.0.0',
                    'description': 'Reference implementation of a todo system'
                },
                'components': {
                    'task_store': {
                        'type': 'Store',
                        'config': {
                            'storage_type': 'memory'
                        }
                    },
                    'task_api': {
                        'type': 'APIEndpoint',
                        'config': {
                            'port': 8080,
                            'host': '0.0.0.0'
                        }
                    }
                },
                'bindings': [
                    {
                        'source': 'task_api',
                        'target': 'task_store',
                        'protocol': 'direct'
                    }
                ]
            }
    
    async def initialize(self):
        """Initialize all components and bindings"""
        logger.info("Initializing Todo System...")
        
        # Create components
        components_config = self.config.get('components', {})
        
        # Create store component
        if 'task_store' in components_config:
            store_config = components_config['task_store']['config']
            self.components['task_store'] = TaskStore('task_store', store_config)
            logger.info("Created task_store component")
        
        # Create API component
        if 'task_api' in components_config:
            api_config = components_config['task_api']['config']
            self.components['task_api'] = TaskAPI('task_api', api_config)
            logger.info("Created task_api component")
        
        # Process bindings
        bindings = self.config.get('bindings', [])
        for binding in bindings:
            source = binding['source']
            target = binding['target']
            protocol = binding['protocol']
            
            if protocol == 'direct':
                # Direct binding - source component gets reference to target
                if source in self.components and target in self.components:
                    source_comp = self.components[source]
                    target_comp = self.components[target]
                    
                    # Use set method if available
                    if hasattr(source_comp, f'set_{target}_component'):
                        getattr(source_comp, f'set_{target}_component')(target_comp)
                    elif hasattr(source_comp, 'set_store_component') and 'store' in target:
                        source_comp.set_store_component(target_comp)
                    else:
                        # Generic binding
                        setattr(source_comp, f'{target}_component', target_comp)
                    
                    logger.info(f"Bound {source} -> {target} via {protocol}")
        
        # Setup all components with context
        harness_context = {
            'components': self.components,
            'config': self.config
        }
        
        for name, component in self.components.items():
            logger.info(f"Setting up component: {name}")
            await component.setup(harness_context)
        
        self.running = True
        logger.info("Todo System initialized successfully")
    
    async def run(self):
        """Run the system"""
        logger.info("Starting Todo System...")
        
        # Start all components' process methods
        for name, component in self.components.items():
            logger.info(f"Starting component: {name}")
            task = asyncio.create_task(component.process())
            self.tasks.append(task)
        
        logger.info(f"System running with {len(self.tasks)} components")
        
        # Wait for shutdown signal
        try:
            while self.running:
                # Check component health periodically
                await asyncio.sleep(10)
                await self.check_health()
        except asyncio.CancelledError:
            logger.info("System run cancelled")
    
    async def check_health(self):
        """Check health of all components"""
        for name, component in self.components.items():
            if hasattr(component, 'get_health_status'):
                health = component.get_health_status()
                if not health.get('healthy', False):
                    logger.warning(f"Component {name} is unhealthy: {health}")
            else:
                logger.debug(f"Component {name} has no health check")
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("Shutting down Todo System...")
        self.running = False
        
        # Cancel all component tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Cleanup all components
        for name, component in self.components.items():
            logger.info(f"Cleaning up component: {name}")
            try:
                await component.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")
        
        logger.info("Todo System shutdown complete")


async def main():
    """Main entry point"""
    # Create system
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    system = TodoSystem(config_path)
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(system.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Initialize system
        await system.initialize()
        
        # Run system
        await system.run()
        
    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure cleanup
        await system.shutdown()


if __name__ == "__main__":
    # Run the system
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)