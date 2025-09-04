#!/usr/bin/env python3
"""
Reference implementation of a Store component.
This is the GOLDEN STANDARD for how components should be structured.
"""
from typing import Dict, Any, Optional, List
import asyncio
import json
from pathlib import Path
from autocoder_cc.components.composed_base import ComposedComponent


class TaskStore(ComposedComponent):
    """
    Minimal Store component that follows the actual expected interface.
    
    Key points:
    - Inherits from ComposedComponent
    - Implements setup(), process(), and cleanup() methods
    - Uses the actual expected patterns
    """
    
    def __init__(self, name: str = "task_store", config: Dict[str, Any] = None):
        """Initialize the store component"""
        # Call parent constructor with name and config
        super().__init__(name, config or {})
        
        # Initialize component-specific state
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._next_id = 1  # Use underscore to avoid conflicts with parent class
        
        # For components that need to handle items
        self.input_queue = asyncio.Queue()
        self.running = False
        
        # Store configuration
        self.storage_type = self.config.get('storage_type', 'memory')
        self.database_config = self.config.get('database', {})
        
        self.logger.info(f"TaskStore initialized with storage_type: {self.storage_type}")
    
    async def setup(self, harness_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Setup the component. Called by the harness during initialization.
        
        Args:
            harness_context: Optional context from the harness
        """
        self.logger.info(f"Setting up TaskStore with context: {harness_context}")
        
        # Initialize storage based on type
        if self.storage_type == 'memory':
            self.tasks = {}
            self._next_id = 1
        elif self.storage_type == 'file':
            # Initialize file storage
            storage_path = Path(self.config.get('storage_path', './data/tasks.json'))
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            if storage_path.exists():
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', {})
                    self._next_id = data.get('next_id', 1)
        # For other storage types (postgres, sqlite), we'd initialize connections here
        
        self.running = True
        self.logger.info("TaskStore setup complete")
    
    async def process(self) -> None:
        """
        Main processing loop. Called by the harness to start processing.
        This runs continuously until cleanup is called.
        """
        self.logger.info("TaskStore processing started")
        
        while self.running:
            try:
                # Wait for items with timeout to allow checking running state
                try:
                    item = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
                    result = await self.process_item(item)
                    
                    # If there's a callback or response queue, send result
                    if hasattr(item, 'response_callback'):
                        await item.response_callback(result)
                    
                except asyncio.TimeoutError:
                    # No item received, continue loop
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error processing item: {e}")
                if self.error_handler:
                    self.error_handler.handle(e, {"component": self.name})
    
    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single item. This is what actually handles the data.
        
        Args:
            item: The item to process
            
        Returns:
            Processing result
        """
        try:
            action = item.get('action', 'get')
            
            if action == 'create':
                task_data = item.get('data', {})
                task_id = str(self._next_id)
                self._next_id = self._next_id + 1
                self.tasks[task_id] = {
                    'id': task_id,
                    'data': task_data,
                    'created_at': item.get('timestamp', 'now')
                }
                
                # Emit metrics
                if self.metrics_collector and hasattr(self.metrics_collector, 'increment'):
                    self.metrics_collector.increment('tasks_created')
                
                return {
                    'status': 'success',
                    'action': 'created',
                    'id': task_id,
                    'data': self.tasks[task_id]
                }
                
            elif action == 'get':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    return {
                        'status': 'success',
                        'action': 'retrieved',
                        'data': self.tasks[task_id]
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'get',
                        'id': task_id
                    }
                    
            elif action == 'update':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    task_data = item.get('data', {})
                    self.tasks[task_id]['data'].update(task_data)
                    return {
                        'status': 'success',
                        'action': 'updated',
                        'id': task_id,
                        'data': self.tasks[task_id]
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'update',
                        'id': task_id
                    }
                    
            elif action == 'delete':
                task_id = item.get('id')
                if task_id and task_id in self.tasks:
                    deleted = self.tasks.pop(task_id)
                    
                    # Emit metrics
                    if self.metrics_collector and hasattr(self.metrics_collector, 'increment'):
                        self.metrics_collector.increment('tasks_deleted')
                    
                    return {
                        'status': 'success',
                        'action': 'deleted',
                        'id': task_id,
                        'data': deleted
                    }
                else:
                    return {
                        'status': 'not_found',
                        'action': 'delete',
                        'id': task_id
                    }
                    
            elif action == 'list':
                return {
                    'status': 'success',
                    'action': 'list',
                    'data': list(self.tasks.values()),
                    'count': len(self.tasks)
                }
                
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
                
        except Exception as e:
            import traceback
            self.logger.error(f"Error processing item: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def cleanup(self) -> None:
        """
        Cleanup the component. Called by the harness during shutdown.
        """
        self.logger.info("TaskStore cleanup started")
        self.running = False
        
        # Save state if using file storage
        if self.storage_type == 'file':
            storage_path = Path(self.config.get('storage_path', './data/tasks.json'))
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(storage_path, 'w') as f:
                json.dump({
                    'tasks': self.tasks,
                    'next_id': self._next_id
                }, f, indent=2)
            self.logger.info(f"Saved state to {storage_path}")
        
        # Clear in-memory data
        self.tasks.clear()
        
        self.logger.info("TaskStore cleanup complete")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Return health status of the component.
        """
        return {
            'healthy': self.running,
            'task_count': len(self.tasks),
            'next_id': self._next_id,
            'storage_type': self.storage_type
        }
    
    async def add_item(self, item: Dict[str, Any]) -> None:
        """
        Add an item to the processing queue.
        Used by other components to send data to this component.
        """
        await self.input_queue.put(item)