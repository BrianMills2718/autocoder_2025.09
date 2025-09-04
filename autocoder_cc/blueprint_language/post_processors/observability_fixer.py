"""Fix observability API usage in generated components"""
import re
from typing import Dict, Tuple

class ObservabilityAPIFixer:
    """Post-processor to fix observability API mismatches"""
    
    # Map wrong patterns to correct ones
    API_FIXES = [
        # Status fixes
        (r'tracer\.status\.OK', 'SpanStatus.OK'),
        (r'tracer\.status\.ERROR', 'SpanStatus.ERROR'),
        (r'tracer\.Status\.OK', 'SpanStatus.OK'),
        (r'tracer\.Status\.ERROR', 'SpanStatus.ERROR'),
        
        # Span method fixes
        (r'span\.add_event\((.*?)\)', r'span.set_attribute("event", \1)'),
        
        # Metrics fixes
        (r'metrics_collector\.get_current_timestamp\(\)', 'time.time()'),
    ]
    
    def fix_code(self, code: str) -> Tuple[str, list]:
        """
        Fix observability API usage
        Returns: (fixed_code, list_of_changes_made)
        """
        changes = []
        
        for pattern, replacement in self.API_FIXES:
            matches = re.findall(pattern, code)
            if matches:
                code = re.sub(pattern, replacement, code)
                changes.append(f"Replaced {pattern} with {replacement} ({len(matches)} occurrences)")
        
        # Ensure SpanStatus is imported if used
        if 'SpanStatus' in code and 'from observability import' in code:
            import_matches = re.findall(r'from observability import (.*)', code)
            if import_matches and 'SpanStatus' not in import_matches[0]:
                code = re.sub(
                    r'from observability import (.*)',
                    r'from observability import \1, SpanStatus',
                    code
                )
                changes.append("Added SpanStatus to imports")
        
        return code, changes