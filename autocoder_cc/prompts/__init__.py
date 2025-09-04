"""
Prompt management system for autocoder_cc.

This module provides a centralized way to manage all LLM prompts used throughout
the system. Prompts are stored as YAML files with metadata, variables, and examples.
"""

from .prompt_manager import PromptManager, PromptError

__all__ = ["PromptManager", "PromptError"]