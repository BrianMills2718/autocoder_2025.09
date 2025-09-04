autocoder_cc/healing/semantic_healer.py:            'return "TODO"',
autocoder_cc/healing/semantic_healer.py:            'pass  # TODO',
autocoder_cc/healing/semantic_healer.py:            'return None  # TODO',
autocoder_cc/analysis/__init__.py:- **Placeholder Detection**: Identifies TODO, FIXME, and incomplete code sections
autocoder_cc/analysis/ast_parser.py:- TODO comments in docstrings and code
autocoder_cc/analysis/ast_parser.py:    # TODO: implement this
autocoder_cc/analysis/ast_parser.py:    - TODO, FIXME, XXX, HACK, BUG, NOTE comments in docstrings and inline
autocoder_cc/analysis/ast_parser.py:            r'\b(TODO|FIXME|XXX|HACK|BUG|NOTE)\b[:\s]*(.*)$',
autocoder_cc/analysis/ast_parser.py:            if value in (None, 0, 42, "", "TODO", "placeholder"):
autocoder_cc/analysis/ast_parser.py:                        if value in ("placeholder", "TODO", "FIXME", None, 0, ""):
autocoder_cc/analysis/ast_parser.py:                            if value in ("placeholder", "TODO", "FIXME", None, 0, ""):
autocoder_cc/blueprint_language/llm_component_generator_backup.py:- NO TODO comments or placeholder text in code
autocoder_cc/blueprint_language/llm_component_generator_backup.py:        - TODO comments
autocoder_cc/blueprint_language/llm_component_generator_backup.py:- TODO comments or FIXME comments - FORBIDDEN
autocoder_cc/blueprint_language/llm_component_generator_backup.py:4. NO TODO comments or FIXME comments - FORBIDDEN
autocoder_cc/blueprint_language/llm_component_generator_backup.py:- NO placeholders, TODOs, or return {"value": 42} patterns
autocoder_cc/blueprint_language/llm_component_generator_backup.py:FORBIDDEN: return {{"value": 42}}, TODO, FIXME, NotImplementedError, pass statements, localhost
autocoder_cc/blueprint_language/llm_component_generator_backup.py:FORBIDDEN: return {{"value": 42}}, TODO, FIXME, NotImplementedError, pass, localhost
autocoder_cc/blueprint_language/llm_component_generator_backup.py:6. NO placeholder patterns: return {{"value": 42}}, TODO, NotImplementedError
autocoder_cc/blueprint_language/llm_component_generator_backup.py:            # Check for TODO comments
