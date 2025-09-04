#!/usr/bin/env python3
"""
Fix for component communication - adds set_registry and send_to_component methods
This should be integrated into ComposedComponent base class
"""

from typing import Any, Dict, Optional


class ComponentCommunicationMixin:
    """Mixin to add communication capabilities to components"""
    
    def __init__(self):
        self.registry: Optional[Any] = None
        self.communicator: Optional[Any] = None
    
    def set_registry(self, registry: Any):
        """Set the component registry for inter-component communication"""
        self.registry = registry
        
    def send_to_component(self, target_name: str, message: Dict[str, Any]):
        """Send a message to another component via the registry"""
        if not self.registry:
            raise RuntimeError(f"Component {getattr(self, 'name', 'unknown')} has no registry set")
        
        target = self.registry.get_component(target_name)
        if not target:
            raise ValueError(f"Component {target_name} not found in registry")
        
        # If target has process_item, use that
        if hasattr(target, 'process_item'):
            import asyncio
            if asyncio.iscoroutinefunction(target.process_item):
                # Need to handle async
                return asyncio.create_task(target.process_item(message))
            else:
                return target.process_item(message)
        else:
            # Just store the message for now
            if hasattr(target, 'received_messages'):
                target.received_messages.append(message)
            else:
                target.received_messages = [message]
                
    def receive_message(self, message: Dict[str, Any]):
        """Receive a message from another component"""
        # Default implementation - store for retrieval
        if not hasattr(self, 'received_messages'):
            self.received_messages = []
        self.received_messages.append(message)


def patch_composed_component():
    """Patch ComposedComponent to add communication methods"""
    from autocoder_cc.components.composed_base import ComposedComponent
    
    # Add the methods dynamically
    original_init = ComposedComponent.__init__
    
    def new_init(self, name: str, config: Dict[str, Any] = None):
        original_init(self, name, config)
        # Add communication attributes
        self.registry = None
        self.communicator = None
        self.received_messages = []
    
    ComposedComponent.__init__ = new_init
    ComposedComponent.set_registry = ComponentCommunicationMixin.set_registry
    ComposedComponent.send_to_component = ComponentCommunicationMixin.send_to_component
    ComposedComponent.receive_message = ComponentCommunicationMixin.receive_message
    
    return ComposedComponent


def patch_store_component():
    """Specifically patch Store component for compatibility"""
    try:
        from autocoder_cc.components.store import Store
        
        # Add methods if they don't exist
        if not hasattr(Store, 'set_registry'):
            Store.set_registry = ComponentCommunicationMixin.set_registry
        if not hasattr(Store, 'send_to_component'):
            Store.send_to_component = ComponentCommunicationMixin.send_to_component
        if not hasattr(Store, 'receive_message'):
            Store.receive_message = ComponentCommunicationMixin.receive_message
            
        # Ensure attributes are initialized
        original_init = Store.__init__
        def new_init(self, name: str, config: Dict[str, Any] = None):
            original_init(self, name, config)
            if not hasattr(self, 'registry'):
                self.registry = None
            if not hasattr(self, 'communicator'):
                self.communicator = None
            if not hasattr(self, 'received_messages'):
                self.received_messages = []
        
        Store.__init__ = new_init
        return Store
    except ImportError:
        return None


# Auto-patch when imported
if __name__ != "__main__":
    patch_composed_component()
    patch_store_component()