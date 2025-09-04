#!/usr/bin/env python3
"""
Intelligent Resource Allocation - P0.8-E2 Integration

Integrates intelligent resource prediction with the existing resource orchestrator.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json
from pathlib import Path

from .resource_prediction import (
    ResourcePredictor, SystemResourceProfile, PortRequirement, ResourceRequirement,
    PortType, ResourceType, get_resource_predictor
)
from .resource_orchestrator import ResourceOrchestrator
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint
from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer

logger = get_logger(__name__)


@dataclass
class IntelligentAllocationResult:
    """Result of intelligent resource allocation"""
    system_name: str
    resource_profile: SystemResourceProfile
    allocation_success: bool
    port_mappings: Dict[str, int] = field(default_factory=dict)
    resource_allocations: Dict[str, Any] = field(default_factory=dict)
    conflicts_resolved: List[str] = field(default_factory=list)
    optimization_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class IntelligentResourceAllocator:
    """Intelligent resource allocator that combines prediction with orchestration"""
    
    def __init__(self, resource_orchestrator: ResourceOrchestrator = None):
        self.resource_predictor = get_resource_predictor()
        self.resource_orchestrator = resource_orchestrator or ResourceOrchestrator()
        self.metrics_collector = get_metrics_collector("intelligent_allocator")
        self.tracer = get_tracer("intelligent_allocator")
        
        # Cache for allocation results
        self.allocation_cache: Dict[str, IntelligentAllocationResult] = {}
        
        # Integration settings
        self.enable_auto_optimization = True
        self.enable_conflict_resolution = True
        self.enable_fallback_allocation = True
    
    async def allocate_system_resources(self, 
                                      system_blueprint: ParsedSystemBlueprint,
                                      optimization_level: str = "balanced") -> IntelligentAllocationResult:
        """Intelligently allocate resources for a system"""
        with self.tracer.span("allocate_system_resources") as span_id:
            system_name = system_blueprint.system.name
            logger.info(f"Starting intelligent resource allocation for system: {system_name}")
            
            try:
                # Step 1: Predict resource requirements
                resource_profile = self.resource_predictor.predict_system_resources(system_blueprint)
                
                # Step 2: Apply optimization strategies
                if self.enable_auto_optimization:
                    resource_profile = await self._apply_optimization_strategies(
                        resource_profile, optimization_level
                    )
                
                # Step 3: Resolve conflicts
                conflicts_resolved = []
                if self.enable_conflict_resolution and resource_profile.resource_conflicts:
                    conflicts_resolved = await self._resolve_resource_conflicts(resource_profile)
                
                # Step 4: Integrate with existing resource orchestrator
                port_mappings, resource_allocations = await self._integrate_with_orchestrator(
                    system_blueprint, resource_profile
                )
                
                # Step 5: Validate allocation results
                warnings = self._validate_allocation_results(resource_profile, port_mappings)
                
                # Create allocation result
                result = IntelligentAllocationResult(
                    system_name=system_name,
                    resource_profile=resource_profile,
                    allocation_success=len(resource_profile.resource_conflicts) == 0,
                    port_mappings=port_mappings,
                    resource_allocations=resource_allocations,
                    conflicts_resolved=conflicts_resolved,
                    optimization_applied=resource_profile.optimization_recommendations,
                    warnings=warnings
                )
                
                # Cache the result
                self.allocation_cache[system_name] = result
                
                self.metrics_collector.record_business_event("intelligent_allocation_completed", 1)
                logger.info(f"Intelligent resource allocation completed for {system_name}")
                
                return result
                
            except Exception as e:
                logger.error(f"Intelligent resource allocation failed for {system_name}: {e}")
                self.metrics_collector.record_error("intelligent_allocation_failed")
                
                # Return failure result
                return IntelligentAllocationResult(
                    system_name=system_name,
                    resource_profile=SystemResourceProfile(
                        system_name=system_name,
                        total_components=len(system_blueprint.system.components),
                        estimated_memory_mb=0,
                        estimated_cpu_percent=0,
                        estimated_disk_mb=0,
                        estimated_network_mbps=0
                    ),
                    allocation_success=False,
                    warnings=[f"Allocation failed: {str(e)}"]
                )
    
    async def _apply_optimization_strategies(self, 
                                           resource_profile: SystemResourceProfile,
                                           optimization_level: str) -> SystemResourceProfile:
        """Apply optimization strategies based on the specified level"""
        optimizations_applied = []
        
        if optimization_level == "aggressive":
            # Aggressive optimization - maximize efficiency
            if resource_profile.estimated_memory_mb > 1024:
                # Reduce memory estimates with aggressive caching
                resource_profile.estimated_memory_mb = int(resource_profile.estimated_memory_mb * 0.8)
                optimizations_applied.append("Applied aggressive memory optimization (20% reduction)")
            
            # Consolidate ports where possible
            external_ports = [p for p in resource_profile.allocated_ports if p.external_access]
            if len(external_ports) > 2:
                optimizations_applied.append("Recommend reverse proxy for port consolidation")
        
        elif optimization_level == "balanced":
            # Balanced optimization - reasonable efficiency with safety margins
            if resource_profile.estimated_memory_mb > 2048:
                # Moderate memory optimization
                resource_profile.estimated_memory_mb = int(resource_profile.estimated_memory_mb * 0.9)
                optimizations_applied.append("Applied balanced memory optimization (10% reduction)")
        
        elif optimization_level == "conservative":
            # Conservative optimization - prioritize stability
            # Add safety margins
            resource_profile.estimated_memory_mb = int(resource_profile.estimated_memory_mb * 1.1)
            resource_profile.estimated_cpu_percent *= 1.1
            optimizations_applied.append("Applied conservative safety margins (10% increase)")
        
        # Add specific optimizations to the profile
        resource_profile.optimization_recommendations.extend(optimizations_applied)
        
        return resource_profile
    
    async def _resolve_resource_conflicts(self, resource_profile: SystemResourceProfile) -> List[str]:
        """Attempt to resolve resource conflicts"""
        resolved_conflicts = []
        
        for conflict in resource_profile.resource_conflicts:
            if "port" in conflict.lower():
                # Try to resolve port conflicts
                if await self._resolve_port_conflict(resource_profile):
                    resolved_conflicts.append(f"Resolved port conflict: {conflict}")
            
            elif "memory" in conflict.lower():
                # Try to resolve memory conflicts
                if await self._resolve_memory_conflict(resource_profile):
                    resolved_conflicts.append(f"Resolved memory conflict: {conflict}")
        
        # Remove resolved conflicts from the profile
        for resolved in resolved_conflicts:
            resource_profile.resource_conflicts = [
                c for c in resource_profile.resource_conflicts 
                if not any(resolved_keyword in c.lower() for resolved_keyword in resolved.lower().split())
            ]
        
        return resolved_conflicts
    
    async def _resolve_port_conflict(self, resource_profile: SystemResourceProfile) -> bool:
        """Try to resolve port conflicts by reallocating ports"""
        try:
            # Reallocate conflicting ports
            for allocated_port in resource_profile.allocated_ports:
                if allocated_port.port in [p.port for p in resource_profile.allocated_ports if p != allocated_port]:
                    # Found duplicate port - reallocate
                    new_port = self.resource_predictor.port_allocator.find_available_port(
                        allocated_port.port_type
                    )
                    if new_port:
                        allocated_port.port = new_port
                        logger.info(f"Reallocated port for {allocated_port.component_name} to {new_port}")
                        return True
            
            return False
        except Exception as e:
            logger.warning(f"Failed to resolve port conflict: {e}")
            return False
    
    async def _resolve_memory_conflict(self, resource_profile: SystemResourceProfile) -> bool:
        """Try to resolve memory conflicts by applying optimization"""
        try:
            # Apply memory optimization
            original_memory = resource_profile.estimated_memory_mb
            optimized_memory = int(original_memory * 0.85)  # 15% reduction
            
            resource_profile.estimated_memory_mb = optimized_memory
            resource_profile.optimization_recommendations.append(
                f"Applied memory optimization: reduced from {original_memory}MB to {optimized_memory}MB"
            )
            
            logger.info(f"Applied memory optimization for {resource_profile.system_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to resolve memory conflict: {e}")
            return False
    
    async def _integrate_with_orchestrator(self, 
                                         system_blueprint: ParsedSystemBlueprint,
                                         resource_profile: SystemResourceProfile) -> Tuple[Dict[str, int], Dict[str, Any]]:
        """Integrate predictions with the existing resource orchestrator"""
        port_mappings = {}
        resource_allocations = {}
        
        try:
            # Create port mappings for orchestrator
            for allocated_port in resource_profile.allocated_ports:
                key = f"{allocated_port.component_name}:{allocated_port.service_name}"
                port_mappings[key] = allocated_port.port
            
            # Create resource allocations
            resource_allocations = {
                "memory_mb": resource_profile.estimated_memory_mb,
                "cpu_percent": resource_profile.estimated_cpu_percent,
                "disk_mb": resource_profile.estimated_disk_mb,
                "network_mbps": resource_profile.estimated_network_mbps,
                "port_count": len(resource_profile.allocated_ports)
            }
            
            # Integrate with orchestrator's port management if available
            if hasattr(self.resource_orchestrator, 'allocate_ports'):
                try:
                    orchestrator_ports = await self.resource_orchestrator.allocate_ports(
                        system_blueprint.system.name,
                        len(resource_profile.allocated_ports)
                    )
                    
                    # Update port mappings with orchestrator results
                    for i, (key, predicted_port) in enumerate(port_mappings.items()):
                        if i < len(orchestrator_ports):
                            port_mappings[key] = orchestrator_ports[i]
                            
                except Exception as e:
                    logger.warning(f"Failed to integrate with orchestrator port allocation: {e}")
            
            return port_mappings, resource_allocations
            
        except Exception as e:
            logger.error(f"Failed to integrate with orchestrator: {e}")
            return port_mappings, resource_allocations
    
    def _validate_allocation_results(self, 
                                   resource_profile: SystemResourceProfile,
                                   port_mappings: Dict[str, int]) -> List[str]:
        """Validate the allocation results and generate warnings"""
        warnings = []
        
        # Check for remaining conflicts
        if resource_profile.resource_conflicts:
            warnings.append(f"Unresolved conflicts: {len(resource_profile.resource_conflicts)}")
        
        # Check port allocation completeness
        expected_ports = len(resource_profile.allocated_ports)
        actual_ports = len(port_mappings)
        
        if actual_ports < expected_ports:
            warnings.append(f"Port allocation incomplete: {actual_ports}/{expected_ports} ports allocated")
        
        # Check resource thresholds
        if resource_profile.estimated_memory_mb > 8192:
            warnings.append("High memory usage detected - consider optimization")
        
        if resource_profile.estimated_cpu_percent > 80:
            warnings.append("High CPU usage detected - consider load balancing")
        
        # Check for port range violations
        for port in port_mappings.values():
            if port < 1024:
                warnings.append(f"Privileged port allocated: {port} - may require elevated permissions")
            elif port > 65535:
                warnings.append(f"Invalid port number: {port}")
        
        return warnings
    
    def get_allocation_summary(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Get allocation summary for a system"""
        if system_name not in self.allocation_cache:
            return None
        
        result = self.allocation_cache[system_name]
        
        return {
            "system_name": result.system_name,
            "allocation_success": result.allocation_success,
            "resource_estimates": {
                "memory_mb": result.resource_profile.estimated_memory_mb,
                "cpu_percent": result.resource_profile.estimated_cpu_percent,
                "disk_mb": result.resource_profile.estimated_disk_mb,
                "network_mbps": result.resource_profile.estimated_network_mbps
            },
            "port_allocations": {
                "total_ports": len(result.port_mappings),
                "port_mappings": result.port_mappings
            },
            "optimization_status": {
                "optimizations_applied": len(result.optimization_applied),
                "conflicts_resolved": len(result.conflicts_resolved),
                "warnings": len(result.warnings)
            },
            "recommendations": result.resource_profile.optimization_recommendations
        }
    
    def optimize_existing_allocation(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Optimize an existing allocation"""
        if system_name not in self.allocation_cache:
            return None
        
        try:
            # Get current allocation
            current_result = self.allocation_cache[system_name]
            
            # Apply additional optimizations
            optimization_suggestions = self.resource_predictor.optimize_resource_allocation(system_name)
            
            # Update the cached result
            current_result.optimization_applied.extend(
                optimization_suggestions.get("optimization_suggestions", [])
            )
            
            self.allocation_cache[system_name] = current_result
            
            return {
                "system_name": system_name,
                "additional_optimizations": optimization_suggestions.get("optimization_suggestions", []),
                "total_optimizations": len(current_result.optimization_applied)
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize existing allocation for {system_name}: {e}")
            return None
    
    async def deallocate_system(self, system_name: str) -> bool:
        """Deallocate all resources for a system"""
        try:
            # Deallocate from resource predictor
            success = self.resource_predictor.deallocate_system_resources(system_name)
            
            # Remove from cache
            if system_name in self.allocation_cache:
                del self.allocation_cache[system_name]
            
            # Deallocate from orchestrator if available
            if hasattr(self.resource_orchestrator, 'deallocate_system_resources'):
                try:
                    await self.resource_orchestrator.deallocate_system_resources(system_name)
                except Exception as e:
                    logger.warning(f"Failed to deallocate from orchestrator: {e}")
            
            self.metrics_collector.record_business_event("intelligent_deallocation_completed", 1)
            logger.info(f"Successfully deallocated resources for system: {system_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deallocate system {system_name}: {e}")
            self.metrics_collector.record_error("intelligent_deallocation_failed")
            return False
    
    def get_global_allocation_status(self) -> Dict[str, Any]:
        """Get global allocation status across all systems"""
        predictor_status = self.resource_predictor.get_global_resource_usage()
        
        cached_systems = list(self.allocation_cache.keys())
        successful_allocations = sum(
            1 for result in self.allocation_cache.values() 
            if result.allocation_success
        )
        
        total_warnings = sum(
            len(result.warnings) for result in self.allocation_cache.values()
        )
        
        total_optimizations = sum(
            len(result.optimization_applied) for result in self.allocation_cache.values()
        )
        
        return {
            "predictor_status": predictor_status,
            "allocation_cache": {
                "total_systems": len(cached_systems),
                "successful_allocations": successful_allocations,
                "success_rate": successful_allocations / len(cached_systems) if cached_systems else 0,
                "total_warnings": total_warnings,
                "total_optimizations": total_optimizations
            },
            "active_systems": cached_systems,
            "intelligent_features": {
                "auto_optimization": self.enable_auto_optimization,
                "conflict_resolution": self.enable_conflict_resolution,
                "fallback_allocation": self.enable_fallback_allocation
            }
        }


# Global intelligent allocator instance
global_intelligent_allocator = IntelligentResourceAllocator()


def get_intelligent_allocator() -> IntelligentResourceAllocator:
    """Get the global intelligent resource allocator"""
    return global_intelligent_allocator


async def intelligently_allocate_system_resources(
    system_blueprint: ParsedSystemBlueprint,
    optimization_level: str = "balanced"
) -> IntelligentAllocationResult:
    """Convenience function for intelligent resource allocation"""
    return await global_intelligent_allocator.allocate_system_resources(
        system_blueprint, optimization_level
    )