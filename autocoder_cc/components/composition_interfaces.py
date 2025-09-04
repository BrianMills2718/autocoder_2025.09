#!/usr/bin/env python3
"""
Composition Interface Specifications - P0.8-E1 Type Safety

Interface specifications for enhanced component composition patterns.
"""
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass

from .type_safety import InterfaceSpec, interface_registry
from .enhanced_composition import CompositionStrategy, CompositionPattern, ComponentDependency


def register_composition_interfaces():
    """Register interface specifications for composition components"""
    
    # BehaviorComposer interface
    behavior_composer_interface = InterfaceSpec(
        name="BehaviorComposer",
        methods={
            "register_behavior": {
                "parameters": {
                    "name": str,
                    "behavior": Callable,
                    "metadata": Optional[Dict]
                },
                "return_type": type(None)
            },
            "compose_behavior": {
                "parameters": {
                    "composition_spec": Dict[str, Any]
                },
                "return_type": Callable
            }
        },
        properties={
            "behaviors": dict,
            "composition_rules": list
        }
    )
    interface_registry.register_interface(behavior_composer_interface)
    
    # DependencyInjector interface
    dependency_injector_interface = InterfaceSpec(
        name="DependencyInjector",
        methods={
            "register_component": {
                "parameters": {
                    "name": str,
                    "component": Any,
                    "dependencies": Optional[List[str]]
                },
                "return_type": type(None)
            },
            "add_dependency": {
                "parameters": {
                    "dependency": ComponentDependency
                },
                "return_type": type(None)
            },
            "wire_components": {
                "parameters": {},
                "return_type": Dict[str, Any]
            }
        },
        properties={
            "components": dict,
            "dependencies": list,
            "injection_rules": dict
        }
    )
    interface_registry.register_interface(dependency_injector_interface)
    
    # PipelineComposer interface
    pipeline_composer_interface = InterfaceSpec(
        name="PipelineComposer",
        methods={
            "add_stage": {
                "parameters": {
                    "stage": Callable,
                    "input_type": Optional[type],
                    "output_type": Optional[type]
                },
                "return_type": type(None)
            },
            "execute": {
                "parameters": {
                    "input_data": Any
                },
                "return_type": Any
            },
            "get_performance_metrics": {
                "parameters": {},
                "return_type": Dict[str, Any]
            }
        },
        properties={
            "stages": list,
            "type_validators": list,
            "performance_metrics": dict
        }
    )
    interface_registry.register_interface(pipeline_composer_interface)
    
    # PerformanceAwareComposer interface
    performance_aware_composer_interface = InterfaceSpec(
        name="PerformanceAwareComposer",
        methods={
            "register_performance_profile": {
                "parameters": {
                    "component_name": str,
                    "metrics": Dict[str, Any]
                },
                "return_type": type(None)
            },
            "register_optimization_strategy": {
                "parameters": {
                    "strategy_name": str,
                    "strategy": Callable
                },
                "return_type": type(None)
            },
            "optimize_composition": {
                "parameters": {
                    "pattern": CompositionPattern
                },
                "return_type": CompositionPattern
            }
        },
        properties={
            "component_metrics": dict,
            "optimization_strategies": dict
        }
    )
    interface_registry.register_interface(performance_aware_composer_interface)
    
    # EnhancedCompositionEngine interface
    enhanced_composition_engine_interface = InterfaceSpec(
        name="EnhancedCompositionEngine",
        methods={
            "register_pattern": {
                "parameters": {
                    "pattern": CompositionPattern
                },
                "return_type": type(None)
            },
            "compose_system": {
                "parameters": {
                    "pattern_name": str,
                    "components": Dict[str, Any]
                },
                "return_type": Dict[str, Any]
            },
            "create_pipeline": {
                "parameters": {
                    "components": List[Any],
                    "type_safety": bool
                },
                "return_type": Any  # Should be PipelineComposer
            },
            "compose_behavior": {
                "parameters": {
                    "behavior_spec": Dict[str, Any]
                },
                "return_type": Callable
            }
        },
        properties={
            "behavior_composer": Any,
            "dependency_injector": Any,
            "performance_composer": Any,
            "patterns": dict
        }
    )
    interface_registry.register_interface(enhanced_composition_engine_interface)
    
    # CompositionPattern interface
    composition_pattern_interface = InterfaceSpec(
        name="CompositionPattern",
        properties={
            "name": str,
            "strategy": CompositionStrategy,
            "components": list,
            "dependencies": list,
            "config": dict,
            "performance_hints": dict
        }
    )
    interface_registry.register_interface(composition_pattern_interface)
    
    # ComponentDependency interface
    component_dependency_interface = InterfaceSpec(
        name="ComponentDependency",
        properties={
            "source_component": str,
            "target_component": str,
            "dependency_type": str,
            "config": dict,
            "optional": bool
        }
    )
    interface_registry.register_interface(component_dependency_interface)


# Register composition interfaces on module import
register_composition_interfaces()