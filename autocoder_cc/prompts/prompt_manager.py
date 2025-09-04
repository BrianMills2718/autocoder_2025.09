"""
Prompt manager for loading and rendering prompts from YAML files.

This module provides functionality to:
1. Load prompt templates from YAML files
2. Validate required variables
3. Render prompts with provided context
4. Cache loaded prompts for performance
"""

from pathlib import Path
import yaml
from typing import Dict, Any, Optional, List, Set
import jinja2
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class PromptError(Exception):
    """Base exception for prompt-related errors."""
    pass


class PromptNotFoundError(PromptError):
    """Raised when a prompt file cannot be found."""
    pass


class PromptValidationError(PromptError):
    """Raised when prompt validation fails."""
    pass


@dataclass
class PromptMetadata:
    """Metadata about a prompt."""
    version: str
    description: str
    author: str
    tags: List[str] = None
    
    
@dataclass
class PromptVariable:
    """Definition of a prompt variable."""
    name: str
    description: str
    required: bool = True
    default: Any = None
    

@dataclass
class LoadedPrompt:
    """A loaded and parsed prompt."""
    metadata: PromptMetadata
    variables: List[PromptVariable]
    template: str
    examples: List[Dict[str, Any]] = None
    

class PromptManager:
    """Manages loading and rendering of prompts from YAML files."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt files. 
                        Defaults to autocoder_cc/prompts/
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, LoadedPrompt] = {}
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.prompts_dir)),
            undefined=jinja2.StrictUndefined,  # Fail on undefined vars
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Verify prompts directory exists
        if not self.prompts_dir.exists():
            raise PromptError(f"Prompts directory not found: {self.prompts_dir}")
    
    def load_prompt(self, prompt_path: str) -> LoadedPrompt:
        """
        Load a prompt file and cache it.
        
        Args:
            prompt_path: Relative path to prompt file (e.g., "component_generation/store.yaml")
            
        Returns:
            LoadedPrompt object containing parsed prompt data
            
        Raises:
            PromptNotFoundError: If prompt file doesn't exist
            PromptValidationError: If prompt file is invalid
        """
        # Check cache first
        if prompt_path in self._cache:
            return self._cache[prompt_path]
            
        # Construct full path
        full_path = self.prompts_dir / prompt_path
        if not full_path.exists():
            # Try with .yaml extension if not provided
            if not prompt_path.endswith('.yaml'):
                full_path = self.prompts_dir / f"{prompt_path}.yaml"
                
        if not full_path.exists():
            raise PromptNotFoundError(f"Prompt file not found: {full_path}")
            
        try:
            with open(full_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PromptValidationError(f"Invalid YAML in {full_path}: {e}")
            
        # Validate and parse prompt structure
        loaded_prompt = self._parse_prompt_data(data, prompt_path)
        
        # Cache the loaded prompt
        self._cache[prompt_path] = loaded_prompt
        logger.info(f"Loaded prompt: {prompt_path}")
        
        return loaded_prompt
    
    def _parse_prompt_data(self, data: Dict[str, Any], prompt_path: str) -> LoadedPrompt:
        """Parse and validate prompt data."""
        # Validate required fields
        if 'metadata' not in data:
            raise PromptValidationError(f"Missing 'metadata' in {prompt_path}")
        if 'prompt' not in data:
            raise PromptValidationError(f"Missing 'prompt' template in {prompt_path}")
            
        # Parse metadata
        metadata_dict = data['metadata']
        metadata = PromptMetadata(
            version=metadata_dict.get('version', '1.0.0'),
            description=metadata_dict.get('description', ''),
            author=metadata_dict.get('author', 'unknown'),
            tags=metadata_dict.get('tags', [])
        )
        
        # Parse variables
        variables = []
        for var_data in data.get('variables', []):
            if isinstance(var_data, str):
                # Simple format: just variable name
                variables.append(PromptVariable(name=var_data, description=var_data))
            elif isinstance(var_data, dict):
                # Full format with metadata
                variables.append(PromptVariable(
                    name=var_data['name'],
                    description=var_data.get('description', var_data['name']),
                    required=var_data.get('required', True),
                    default=var_data.get('default')
                ))
            else:
                raise PromptValidationError(f"Invalid variable format in {prompt_path}")
        
        # Get template and examples
        template = data['prompt']
        examples = data.get('examples', [])
        
        return LoadedPrompt(
            metadata=metadata,
            variables=variables,
            template=template,
            examples=examples
        )
    
    def render_prompt(self, prompt_path: str, variables: Dict[str, Any]) -> str:
        """
        Render a prompt with given variables.
        
        Args:
            prompt_path: Path to prompt file
            variables: Dictionary of variables to inject
            
        Returns:
            Rendered prompt string
            
        Raises:
            PromptValidationError: If required variables are missing
        """
        # Load the prompt
        prompt = self.load_prompt(prompt_path)
        
        # Validate required variables
        self._validate_variables(prompt, variables)
        
        # Apply defaults for missing optional variables
        render_vars = self._apply_defaults(prompt, variables)
        
        try:
            # Render the template
            template = self._jinja_env.from_string(prompt.template)
            rendered = template.render(**render_vars)
            
            logger.debug(f"Rendered prompt {prompt_path} with {len(render_vars)} variables")
            return rendered
            
        except jinja2.exceptions.UndefinedError as e:
            raise PromptValidationError(f"Undefined variable in template: {e}")
        except Exception as e:
            raise PromptError(f"Error rendering prompt {prompt_path}: {e}")
    
    def _validate_variables(self, prompt: LoadedPrompt, provided: Dict[str, Any]) -> None:
        """Validate that all required variables are provided."""
        required_vars = {v.name for v in prompt.variables if v.required}
        provided_vars = set(provided.keys())
        missing = required_vars - provided_vars
        
        if missing:
            raise PromptValidationError(
                f"Missing required variables: {sorted(missing)}. "
                f"Required: {sorted(required_vars)}, Provided: {sorted(provided_vars)}"
            )
    
    def _apply_defaults(self, prompt: LoadedPrompt, provided: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing optional variables."""
        result = provided.copy()
        
        for var in prompt.variables:
            if var.name not in result and var.default is not None:
                result[var.name] = var.default
                logger.debug(f"Applied default value for {var.name}: {var.default}")
                
        return result
    
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """
        List all available prompts.
        
        Args:
            category: Optional category filter (e.g., "component_generation")
            
        Returns:
            List of prompt paths
        """
        prompts = []
        
        if category:
            search_dir = self.prompts_dir / category
        else:
            search_dir = self.prompts_dir
            
        for yaml_file in search_dir.rglob("*.yaml"):
            relative_path = yaml_file.relative_to(self.prompts_dir)
            prompts.append(str(relative_path))
            
        return sorted(prompts)
    
    def get_prompt_info(self, prompt_path: str) -> Dict[str, Any]:
        """
        Get information about a prompt without rendering it.
        
        Args:
            prompt_path: Path to prompt file
            
        Returns:
            Dictionary with prompt metadata and variable info
        """
        prompt = self.load_prompt(prompt_path)
        
        return {
            "path": prompt_path,
            "metadata": {
                "version": prompt.metadata.version,
                "description": prompt.metadata.description,
                "author": prompt.metadata.author,
                "tags": prompt.metadata.tags or []
            },
            "variables": [
                {
                    "name": var.name,
                    "description": var.description,
                    "required": var.required,
                    "default": var.default
                }
                for var in prompt.variables
            ],
            "has_examples": len(prompt.examples) > 0 if prompt.examples else False
        }
    
    def validate_prompt_file(self, prompt_path: str) -> List[str]:
        """
        Validate a prompt file and return any issues.
        
        Args:
            prompt_path: Path to prompt file
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            prompt = self.load_prompt(prompt_path)
            
            # Check metadata
            if not prompt.metadata.description:
                issues.append("Missing description in metadata")
            
            # Check for examples
            if not prompt.examples:
                issues.append("No examples provided")
                
            # Check template for common issues
            if "{" in prompt.template and not "{{" in prompt.template:
                issues.append("Template may have unescaped braces")
                
            # Validate examples can be rendered
            for i, example in enumerate(prompt.examples or []):
                if 'input' in example:
                    try:
                        self.render_prompt(prompt_path, example['input'])
                    except Exception as e:
                        issues.append(f"Example {i} fails to render: {e}")
                        
        except Exception as e:
            issues.append(f"Failed to load prompt: {e}")
            
        return issues
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()
        logger.info("Cleared prompt cache")