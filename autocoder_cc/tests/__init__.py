"""Test suite for the system-first architecture."""

# Import analysis test modules for test discovery
from autocoder_cc.tests.analysis import test_secret_detection
from autocoder_cc.tests.analysis import test_placeholder_detection  
from autocoder_cc.tests.analysis import test_ast_error_handling

__all__ = [
    'test_secret_detection',
    'test_placeholder_detection', 
    'test_ast_error_handling'
]