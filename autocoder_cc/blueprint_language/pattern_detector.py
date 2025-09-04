"""Anti-pattern detector for identifying common issues in generated code"""
import ast
import re
from typing import List, Tuple


class AntiPatternDetector:
    """Detects common anti-patterns in generated code"""
    
    ANTI_PATTERNS = [
        (r'MessageEnvelope\s*\(\s*sender=', 'MessageEnvelope uses wrong parameter: sender'),
        (r'MessageEnvelope\s*\(\s*recipient=', 'MessageEnvelope uses wrong parameter: recipient'),
        (r'MessageEnvelope\s*\(\s*message=', 'MessageEnvelope uses wrong parameter: message'),
        (r'self\.query_component\s*\([^,)]+\)', 'query_component called with single argument'),
        (r'self\.send_to_component\s*\([^,)]+\)', 'send_to_component called with single argument')
    ]
    
    def detect_anti_patterns(self, code: str) -> List[Tuple[str, str]]:
        """Returns list of (pattern, message) for detected anti-patterns"""
        detected = []
        for pattern, message in self.ANTI_PATTERNS:
            if re.search(pattern, code):
                detected.append((pattern, message))
        return detected
    
    def has_anti_patterns(self, code: str) -> bool:
        """Quick check if code has any anti-patterns"""
        return bool(self.detect_anti_patterns(code))