#!/usr/bin/env python3
"""
Centralized Prompt Loader for Template Management

This module provides utilities for loading and composing prompts from the centralized
prompts/ directory. It addresses Root Cause #1 (contradictory instructions) by
centralizing all prompt templates and enabling consistent prompt composition.

Key Features:
- Template composition from multiple files
- Variable substitution with validation
- Environment-specific prompt loading
- Prompt debugging and validation utilities
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    """Template with metadata for composition"""
    name: str
    content: str
    variables: List[str]
    dependencies: List[str] = None

class PromptLoader:
    """
    Centralized prompt loading and composition system
    
    Loads prompt templates from the prompts/ directory and provides
    utilities for composing them with variable substitution.
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize with prompts directory"""
        if prompts_dir is None:
            # Default to project root prompts/ directory
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = project_root / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._template_cache = {}
        self._ensure_prompts_directory()
    
    def _ensure_prompts_directory(self):
        """Ensure prompts directory exists"""
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}. "
                f"Please ensure centralized prompts are set up."
            )
    
    def load_template(self, template_path: str) -> PromptTemplate:
        """
        Load a single template file
        
        Args:
            template_path: Relative path from prompts/ directory
            
        Returns:
            PromptTemplate with content and metadata
        """
        cache_key = template_path
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        full_path = self.prompts_dir / template_path
        if not full_path.exists():
            raise FileNotFoundError(f"Template not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract template variables (e.g., {component_type}, {reasoning_prefix})
        variables = re.findall(r'\{([^}]+)\}', content)
        
        template = PromptTemplate(
            name=template_path,
            content=content,
            variables=list(set(variables))  # Remove duplicates
        )
        
        self._template_cache[cache_key] = template
        return template
    
    def compose_prompt(self, template_paths: List[str], variables: Dict[str, Any] = None) -> str:
        """
        Compose multiple templates into a single prompt
        
        Args:
            template_paths: List of template file paths to compose
            variables: Dictionary of variables for substitution
            
        Returns:
            Composed prompt string with variables substituted
        """
        variables = variables or {}
        composed_content = []
        
        for template_path in template_paths:
            template = self.load_template(template_path)
            
            # Validate that all required variables are provided
            missing_vars = set(template.variables) - set(variables.keys())
            if missing_vars:
                raise ValueError(
                    f"Missing variables for template {template_path}: {missing_vars}"
                )
            
            composed_content.append(template.content)
        
        # Join templates with newlines
        full_content = "\n\n".join(composed_content)
        
        # Substitute variables
        try:
            return full_content.format(**variables)
        except KeyError as e:
            raise ValueError(f"Template variable substitution failed: {e}")
    
    def load_component_system_prompt(self, component_type: str, reasoning_prefix: str = "") -> str:
        """
        Load system prompt for component generation
        
        This replaces the get_system_prompt method in PromptEngine
        with centralized template composition.
        """
        # Load system prompt with variables
        system_template = self.load_template("component_generation/system_prompt.txt")
        system_content = system_template.content.format(
            component_type=component_type,
            reasoning_prefix=reasoning_prefix
        )
        
        # Load import instructions (no variables needed)
        import_template = self.load_template("component_generation/import_instructions.txt")
        
        # Combine templates
        return f"{system_content}\n\n{import_template.content}"
    
    def load_component_requirements(self, component_type: str) -> str:
        """
        Load component-specific requirements
        
        Args:
            component_type: Component type (Source, Store, APIEndpoint, etc.)
            
        Returns:
            Component-specific requirements text
        """
        # Try component-specific requirements first
        specific_template = f"component_generation/{component_type.lower()}_requirements.txt"
        
        templates_to_load = ["component_generation/base_requirements.txt"]
        
        # Add specific requirements if they exist
        specific_path = self.prompts_dir / specific_template
        if specific_path.exists():
            templates_to_load.append(specific_template)
        
        # Always add communication patterns
        templates_to_load.append("component_generation/communication_patterns.txt")
        
        return self.compose_prompt(templates_to_load, {"component_type": component_type})
    
    def load_self_healing_imports(self) -> Dict[str, str]:
        """
        Load project-specific import mappings for self-healing
        
        This addresses Root Cause #7 by providing centralized import mappings
        that the self-healing system can use to fix missing imports.
        
        Returns:
            Dictionary mapping class names to import statements
        """
        template = self.load_template("self_healing/project_imports.txt")
        imports_dict = {}
        
        for line in template.content.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                # Parse format: "ClassName: from module import ClassName"
                class_name, import_statement = line.split(':', 1)
                imports_dict[class_name.strip()] = import_statement.strip()
        
        return imports_dict
    
    def load_interface_repair_patterns(self) -> Dict[str, Any]:
        """
        Load interface repair patterns for self-healing
        
        Returns:
            Dictionary with repair patterns and expected interfaces
        """
        template = self.load_template("self_healing/interface_repair.txt")
        patterns = {
            "constructor_patterns": [],
            "method_patterns": [],
            "type_fixes": {},
            "component_name_patterns": []
        }
        
        # Parse the interface repair template
        # This is a simple parser - could be enhanced for more complex patterns
        current_section = None
        for line in template.content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                continue
            elif line.endswith(':'):
                current_section = line[:-1].lower().replace(' ', '_')
            elif ':' in line and current_section:
                key, value = line.split(':', 1)
                if current_section == "type_fixes":
                    patterns["type_fixes"][key.strip()] = value.strip()
                elif current_section not in patterns:
                    patterns[current_section] = []
                    patterns[current_section].append({key.strip(): value.strip()})
        
        return patterns
    
    def validate_prompts(self) -> List[str]:
        """
        Validate all prompts for consistency and completeness
        
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check for contradictory instructions (Root Cause #1)
        try:
            system_prompt_template = self.load_template("component_generation/system_prompt.txt")
            import_instructions = self.load_template("component_generation/import_instructions.txt")
            
            # Check for true contradictions (both say no imports but one contradicts)
            system_says_no_imports = "NO import statements" in system_prompt_template.content
            import_says_generate = "generate import statements" in import_instructions.content.lower()
            import_says_no_imports = "DO NOT GENERATE IMPORT STATEMENTS" in import_instructions.content
            
            # Both templates consistently say no imports - this is correct
            if system_says_no_imports and import_says_no_imports:
                # This is consistent, not contradictory
                pass
            elif system_says_no_imports and import_says_generate:
                issues.append("Contradictory import instructions found between system_prompt.txt and import_instructions.txt")
            # If there's any other actual contradiction, we'd catch it here
            elif not system_says_no_imports and not import_says_generate and not import_says_no_imports:
                # Neither file gives clear import guidance - this could be an issue
                issues.append("Unclear import instructions - neither template provides clear guidance")
        
        except FileNotFoundError as e:
            issues.append(f"Missing core template: {e}")
        
        # Check that all referenced templates exist
        core_templates = [
            "component_generation/system_prompt.txt",
            "component_generation/import_instructions.txt", 
            "component_generation/base_requirements.txt",
            "component_generation/communication_patterns.txt",
            "self_healing/project_imports.txt",
            "self_healing/interface_repair.txt"
        ]
        
        for template_path in core_templates:
            full_path = self.prompts_dir / template_path
            if not full_path.exists():
                issues.append(f"Missing required template: {template_path}")
        
        return issues
    
    def debug_template_composition(self, template_paths: List[str], variables: Dict[str, Any]) -> str:
        """
        Debug template composition by showing how templates are combined
        
        Returns:
            Debug information about template composition
        """
        debug_info = []
        debug_info.append("=== TEMPLATE COMPOSITION DEBUG ===")
        
        for i, template_path in enumerate(template_paths):
            debug_info.append(f"\n--- Template {i+1}: {template_path} ---")
            try:
                template = self.load_template(template_path)
                debug_info.append(f"Variables required: {template.variables}")
                debug_info.append(f"Content length: {len(template.content)} chars")
                debug_info.append(f"First 100 chars: {template.content[:100]}...")
            except Exception as e:
                debug_info.append(f"ERROR loading template: {e}")
        
        debug_info.append(f"\n--- Variables provided ---")
        for key, value in variables.items():
            value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            debug_info.append(f"{key}: {value_preview}")
        
        return "\n".join(debug_info)


# Global instance for easy access
_prompt_loader = None

def get_prompt_loader() -> PromptLoader:
    """Get global prompt loader instance"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_component_prompt_templates() -> Dict[str, str]:
    """
    Load all component prompt templates for compatibility
    
    Returns:
        Dictionary of template names to content
    """
    loader = get_prompt_loader()
    templates = {}
    
    # Load core templates
    core_template_paths = [
        "component_generation/system_prompt.txt",
        "component_generation/import_instructions.txt",
        "component_generation/base_requirements.txt", 
        "component_generation/communication_patterns.txt",
        "component_generation/store_requirements.txt",
        "component_generation/api_endpoint_requirements.txt"
    ]
    
    for template_path in core_template_paths:
        try:
            template = loader.load_template(template_path)
            # Use filename without extension as key
            template_name = Path(template_path).stem
            templates[template_name] = template.content
        except FileNotFoundError:
            # Skip missing optional templates
            pass
    
    return templates


# Export public interface
__all__ = [
    "PromptLoader",
    "PromptTemplate", 
    "get_prompt_loader",
    "load_component_prompt_templates"
]