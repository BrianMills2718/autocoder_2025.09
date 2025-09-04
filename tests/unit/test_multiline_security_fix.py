"""
Unit test for multiline string security detection fix
Using TDD to implement proper multiline security validation
"""
import pytest
import re
from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator


class TestMultilineSecurityDetection:
    """Unit tests for multiline string security detection"""
    
    def test_current_regex_fails_on_multiline(self):
        """Test that shows current single-line regex fails on multiline strings"""
        # GIVEN: Current single-line pattern
        pattern = r"password\s*=\s*['\"][^'\"]+['\"]"
        
        # WHEN: Applied to multiline string
        multiline_code = '''
        connection_string = """
        host=localhost
        password=secret123
        database=mydb
        """
        '''
        
        # THEN: Current pattern doesn't match (this demonstrates the bug)
        matches = re.findall(pattern, multiline_code, re.IGNORECASE)
        assert len(matches) == 0  # This shows the bug - no matches found
    
    def test_improved_regex_handles_multiline(self):
        """Test that improved regex with DOTALL flag handles multiline strings"""
        # GIVEN: Content inside triple quotes containing password
        multiline_code = '''
        connection_string = """
        host=localhost
        password=secret123
        database=mydb
        """
        '''
        
        # WHEN: Using improved multiline-aware pattern
        # Pattern to match content inside triple quotes
        triple_quote_pattern = r'"""(.*?)"""'
        triple_quote_content = re.findall(triple_quote_pattern, multiline_code, re.DOTALL)
        
        # Then search for passwords within the content
        password_found = False
        for content in triple_quote_content:
            if re.search(r'password\s*[=:]\s*[^\s\n]+', content, re.IGNORECASE):
                password_found = True
        
        # THEN: Password should be detected
        assert password_found
    
    def test_detection_works_for_various_formats(self):
        """Test detection works for various multiline formats"""
        test_cases = [
            # Triple quote with key=value format
            '''config = """
            host=localhost
            password=secret123
            """''',
            
            # Triple quote with YAML-like format
            '''yaml_config = """
            database:
              host: localhost
              password: secret_password
            """''',
            
            # Triple quote with JSON-like format
            '''json_config = """
            {
                "host": "localhost",
                "password": "my_password"
            }
            """''',
            
            # Environment file format
            '''env_content = """
            DB_HOST=postgres
            DB_PASSWORD=actual_password_123
            """'''
        ]
        
        for i, code in enumerate(test_cases):
            # Extract content from triple quotes
            triple_quote_pattern = r'"""(.*?)"""'
            contents = re.findall(triple_quote_pattern, code, re.DOTALL)
            
            # Check if any content contains password
            password_found = False
            for content in contents:
                # Multiple patterns to handle different formats
                patterns = [
                    r'password\s*[=:]\s*[^\s\n\r]+',  # key=value or key: value
                    r'"password"\s*:\s*"[^"]+',        # JSON format
                    r'DB_PASSWORD\s*=\s*[^\s\n\r]+',  # Environment variable
                ]
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        password_found = True
                        break
                if password_found:
                    break
            
            assert password_found, f"Failed to detect password in test case {i}: {code[:50]}..."
    
    @pytest.mark.asyncio
    async def test_enhanced_validate_generated_security(self):
        """Test the enhanced _validate_generated_security method handles multiline strings"""
        # GIVEN: A ComponentLogicGenerator with the enhanced method
        generator = ComponentLogicGenerator(output_dir=".")
        
        # WHEN: Validating code with password in multiline string
        test_code = '''
        connection_string = """
        host=localhost
        port=5432
        user=admin
        password=secret123
        database=mydb
        """
        '''
        
        # THEN: Should detect the password violation (this will fail until we implement the fix)
        violations = generator._validate_generated_security(test_code)
        
        # This assertion will initially fail - that's the RED phase
        assert len(violations) > 0, "Should detect password in multiline string"
        assert any("password" in v.lower() for v in violations), "Should mention password in violation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])