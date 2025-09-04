"""
Context Builder

This module handles context-aware prompt building for enhanced LLM generation.
It analyzes system context, component relationships, and generates prompts that
consider the broader system architecture and requirements.

Key Features:
- System context awareness for component relationships
- Data flow analysis for upstream/downstream integration
- Quality guidance based on system requirements
- Enhanced prompting with architectural context
"""

from typing import Dict, Any, Optional, List
import json


class ContextBuilder:
    """
    Builds context-aware prompts for LLM generation
    
    Analyzes system-wide context to generate prompts that consider:
    - Component relationships and data flow
    - System requirements and constraints
    - Quality patterns from successful generations
    - Performance implications of component interactions
    """
    
    def __init__(self):
        self.component_flow_order = ['Source', 'Transformer', 'Store', 'APIEndpoint', 'Sink']
    
    def build_context_aware_prompt(
        self,
        component_type: str,
        component_name: str,
        component_description: str,
        component_config: Dict[str, Any],
        class_name: str,
        system_context: Optional[Dict[str, Any]] = None,
        base_prompt_builder=None,
        blueprint: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build enhanced context-aware prompt with system relationships and quality guidance
        
        Args:
            component_type: Type of component to generate
            component_name: Name of the component
            component_description: Description of component functionality
            component_config: Component configuration
            class_name: Generated class name
            system_context: System-wide context information
            base_prompt_builder: Function to build base component prompt
            blueprint: System blueprint containing component connections and data flow
            
        Returns:
            Enhanced context-aware prompt string
        """
        
        # Build system context awareness
        system_awareness = ""
        if system_context:
            system_awareness = self._build_system_context_section(
                system_context, component_name, component_type
            )
        
        # Get base component prompt
        if base_prompt_builder:
            base_prompt = base_prompt_builder(
                component_type, component_name, component_description, component_config, class_name, blueprint
            )
        else:
            base_prompt = self._build_fallback_prompt(
                component_type, component_name, component_description, component_config, class_name
            )
        
        # Enhanced prompt with system awareness
        enhanced_prompt = f"""
{system_awareness}

ENHANCED GENERATION CONTEXT:
- Generate components with awareness of system-wide architecture
- Optimize for integration patterns and data flow requirements
- Follow quality patterns from successful system generations
- Consider performance implications of component interactions

{base_prompt}

CONTEXT-AWARE REQUIREMENTS:
- Design component to integrate seamlessly with system pipeline
- Follow data transformation patterns appropriate for position in pipeline
- Implement error handling that considers downstream component dependencies
- Use logging and metrics that align with system-wide observability strategy
"""
        return enhanced_prompt
    
    def _build_system_context_section(self, system_context: Dict[str, Any], 
                                     current_component: str, component_type: str) -> str:
        """
        Build system context awareness section for enhanced prompting
        
        Args:
            system_context: System-wide context information
            current_component: Name of the current component being generated
            component_type: Type of the current component
            
        Returns:
            System context awareness section
        """
        context_section = "\n=== SYSTEM CONTEXT AWARENESS ===\n"
        
        # Add component relationships
        if 'components' in system_context:
            components = system_context['components']
            context_section += f"\nSYSTEM COMPONENTS ({len(components)} total):\n"
            
            upstream_components = []
            downstream_components = []
            
            for comp in components:
                if comp['name'] != current_component:
                    comp_info = f"- {comp['name']} ({comp['type']}): {comp.get('description', 'No description')}"
                    context_section += comp_info + "\n"
                    
                    # Determine data flow relationships
                    if self._is_upstream_component(comp['type'], component_type):
                        upstream_components.append(comp)
                    elif self._is_downstream_component(comp['type'], component_type):
                        downstream_components.append(comp)
            
            # Add data flow context
            if upstream_components:
                context_section += f"\nUPSTREAM COMPONENTS (data sources for {current_component}):\n"
                for comp in upstream_components:
                    context_section += f"- {comp['name']} ({comp['type']}) -> expects data integration\n"
            
            if downstream_components:
                context_section += f"\nDOWNSTREAM COMPONENTS (data consumers from {current_component}):\n"
                for comp in downstream_components:
                    context_section += f"- {comp['name']} ({comp['type']}) -> will process your output\n"
        
        # Add system requirements
        if 'system_requirements' in system_context:
            req = system_context['system_requirements']
            context_section += f"\nSYSTEM REQUIREMENTS:\n"
            context_section += f"- Message Volume: {req.get('message_volume', 'Unknown')} messages/sec\n"
            context_section += f"- Max Latency: {req.get('max_latency', 'Unknown')} ms\n"
            context_section += f"- Durability Required: {req.get('durability_required', False)}\n"
            context_section += f"- Consistency Required: {req.get('consistency_required', False)}\n"
        
        # Add quality guidance
        context_section += f"\nQUALITY OPTIMIZATION GUIDANCE:\n"
        context_section += f"- Implement robust error handling for system-wide reliability\n"
        context_section += f"- Use structured logging with correlation IDs for distributed tracing\n"
        context_section += f"- Include metrics that support system-wide performance monitoring\n"
        context_section += f"- Design for horizontal scaling if system requirements indicate high throughput\n"
        
        context_section += "\n=== END SYSTEM CONTEXT ===\n"
        return context_section
    
    def _is_upstream_component(self, source_type: str, target_type: str) -> bool:
        """
        Determine if source component is upstream from target in typical data flow
        
        Args:
            source_type: Type of the source component
            target_type: Type of the target component
            
        Returns:
            True if source is upstream from target
        """
        try:
            source_idx = self.component_flow_order.index(source_type)
            target_idx = self.component_flow_order.index(target_type)
            return source_idx < target_idx
        except ValueError:
            return False
    
    def _is_downstream_component(self, source_type: str, target_type: str) -> bool:
        """
        Determine if source component is downstream from target in typical data flow
        
        Args:
            source_type: Type of the source component
            target_type: Type of the target component
            
        Returns:
            True if source is downstream from target
        """
        return self._is_upstream_component(target_type, source_type)
    
    def _build_fallback_prompt(self, component_type: str, component_name: str,
                              component_description: str, component_config: Dict[str, Any],
                              class_name: str) -> str:
        """
        Build fallback prompt when no base prompt builder is provided
        
        Args:
            component_type: Type of component
            component_name: Name of component
            component_description: Description of functionality
            component_config: Component configuration
            class_name: Generated class name
            
        Returns:
            Basic fallback prompt
        """
        return f"""
Generate a complete {component_type} component:

Component Details:
- Name: {component_name}
- Class Name: {class_name}
- Description: {component_description}
- Configuration: {json.dumps(component_config, indent=2)}

Requirements:
- Inherit from ComposedComponent
- Implement process_item method with real business logic
- Include proper error handling and logging
- No placeholder patterns or TODO comments
"""
    
    def analyze_system_complexity(self, system_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze system complexity to guide generation strategies
        
        Args:
            system_context: System-wide context information
            
        Returns:
            Analysis of system complexity factors
        """
        analysis = {
            'complexity_score': 0,
            'factors': [],
            'recommendations': []
        }
        
        if 'components' in system_context:
            component_count = len(system_context['components'])
            analysis['complexity_score'] += min(component_count * 0.1, 1.0)
            analysis['factors'].append(f"Component count: {component_count}")
            
            # Analyze component type diversity
            component_types = set(comp['type'] for comp in system_context['components'])
            type_diversity = len(component_types)
            analysis['complexity_score'] += min(type_diversity * 0.15, 1.0)
            analysis['factors'].append(f"Component type diversity: {type_diversity}")
        
        if 'system_requirements' in system_context:
            req = system_context['system_requirements']
            
            # High throughput increases complexity
            if req.get('message_volume', 0) > 1000:
                analysis['complexity_score'] += 0.3
                analysis['factors'].append("High throughput requirements")
            
            # Low latency increases complexity
            if req.get('max_latency', float('inf')) < 100:
                analysis['complexity_score'] += 0.2
                analysis['factors'].append("Low latency requirements")
            
            # Durability and consistency add complexity
            if req.get('durability_required'):
                analysis['complexity_score'] += 0.1
                analysis['factors'].append("Durability requirements")
            
            if req.get('consistency_required'):
                analysis['complexity_score'] += 0.1
                analysis['factors'].append("Consistency requirements")
        
        # Generate recommendations based on complexity
        if analysis['complexity_score'] > 0.7:
            analysis['recommendations'].extend([
                "Use simplified prompts to avoid confusion",
                "Focus on core functionality first",
                "Implement comprehensive error handling",
                "Add extensive logging for debugging"
            ])
        elif analysis['complexity_score'] > 0.4:
            analysis['recommendations'].extend([
                "Balance functionality with maintainability",
                "Include performance monitoring",
                "Design for scalability"
            ])
        else:
            analysis['recommendations'].extend([
                "Focus on business logic implementation",
                "Ensure proper integration patterns"
            ])
        
        return analysis
    
    def build_integration_guidance(self, component_type: str, 
                                  system_context: Dict[str, Any]) -> str:
        """
        Build integration guidance based on system context
        
        Args:
            component_type: Type of component being generated
            system_context: System-wide context information
            
        Returns:
            Integration guidance string
        """
        if not system_context or 'components' not in system_context:
            return "Standard integration patterns apply."
        
        guidance_parts = []
        components = system_context['components']
        
        # Find related components
        upstream_types = []
        downstream_types = []
        
        for comp in components:
            if self._is_upstream_component(comp['type'], component_type):
                upstream_types.append(comp['type'])
            elif self._is_downstream_component(comp['type'], component_type):
                downstream_types.append(comp['type'])
        
        # Build guidance based on relationships
        if upstream_types:
            guidance_parts.append(f"UPSTREAM INTEGRATION: Expect data from {', '.join(set(upstream_types))}")
            guidance_parts.append("- Design input validation for upstream data formats")
            guidance_parts.append("- Handle potential data quality issues gracefully")
        
        if downstream_types:
            guidance_parts.append(f"DOWNSTREAM INTEGRATION: Output will be consumed by {', '.join(set(downstream_types))}")
            guidance_parts.append("- Ensure output format matches downstream expectations")
            guidance_parts.append("- Include metadata for downstream processing decisions")
        
        # Add system-specific guidance
        if 'system_requirements' in system_context:
            req = system_context['system_requirements']
            if req.get('message_volume', 0) > 100:
                guidance_parts.append("HIGH THROUGHPUT: Optimize for performance and memory usage")
            if req.get('max_latency', float('inf')) < 1000:
                guidance_parts.append("LOW LATENCY: Minimize processing time and blocking operations")
        
        return "\n".join(guidance_parts) if guidance_parts else "Standard integration patterns apply."
    
    def enhance_prompt_with_examples(self, base_prompt: str, component_type: str,
                                   successful_patterns: Optional[List[str]] = None) -> str:
        """
        Enhance prompt with examples from successful generations
        
        Args:
            base_prompt: Base prompt to enhance
            component_type: Type of component
            successful_patterns: List of successful patterns to include
            
        Returns:
            Enhanced prompt with examples
        """
        if not successful_patterns:
            successful_patterns = self._get_default_successful_patterns(component_type)
        
        example_section = "\n\nSUCCESSFUL PATTERNS TO FOLLOW:\n"
        for i, pattern in enumerate(successful_patterns, 1):
            example_section += f"{i}. {pattern}\n"
        
        return base_prompt + example_section
    
    def _get_default_successful_patterns(self, component_type: str) -> List[str]:
        """Get default successful patterns for component types"""
        patterns = {
            "Source": [
                "Generate realistic data with proper timestamps and IDs",
                "Use configuration to control data generation parameters",
                "Include error handling for data generation failures",
                "Implement proper rate limiting and batch sizing"
            ],
            "Transformer": [
                "Preserve input data structure while adding transformations",
                "Handle edge cases and invalid input gracefully",
                "Use meaningful transformation logic based on business requirements",
                "Include validation for transformed data quality"
            ],
            "Sink": [
                "Implement proper output formatting and validation",
                "Handle output destination failures gracefully",
                "Include confirmation and metadata in responses",
                "Use appropriate async patterns for I/O operations"
            ],
            "Store": [
                "Use proper async database operations",
                "Implement connection pooling and retry logic",
                "Include data validation before persistence",
                "Handle database-specific error scenarios"
            ],
            "APIEndpoint": [
                "Return structured responses with proper status codes",
                "Implement request validation and sanitization",
                "Include proper error responses and documentation",
                "Use async patterns for handling concurrent requests"
            ]
        }
        
        return patterns.get(component_type, [
            "Implement real business logic with meaningful data processing",
            "Include comprehensive error handling and logging",
            "Use proper async patterns throughout",
            "Validate all inputs and outputs"
        ])