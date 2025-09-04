"""
Reference Implementation Package

This is the GOLDEN STANDARD for how the system should work.
All generated code should match this structure and behavior.
"""

from .components.task_store import TaskStore
from .components.task_api import TaskAPI

__all__ = ['TaskStore', 'TaskAPI']