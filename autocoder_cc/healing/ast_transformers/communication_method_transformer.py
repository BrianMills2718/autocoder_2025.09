"""AST transformer to fix send_to_component and query_component method calls"""
import ast
from typing import Optional, List


class CommunicationMethodTransformer(ast.NodeTransformer):
    """Fixes send_to_component and query_component method calls"""
    
    def visit_Call(self, node):
        self.generic_visit(node)
        
        # Check for self.query_component or self.send_to_component
        if (isinstance(node.func, ast.Attribute) and 
            isinstance(node.func.value, ast.Name) and 
            node.func.value.id == 'self'):
            
            if node.func.attr == 'query_component':
                return self._fix_query_component(node)
            elif node.func.attr == 'send_to_component':
                return self._fix_send_to_component(node)
        
        return node
    
    def _fix_query_component(self, node):
        """Fix query_component(envelope) -> query_component(target_component=..., query=..., target_port=...)"""
        if len(node.args) == 1 and not node.keywords:
            # Assume single arg is MessageEnvelope
            envelope_var = node.args[0]
            
            # Create new keyword arguments
            node.args = []
            node.keywords = [
                ast.keyword(arg='target_component', 
                          value=ast.Attribute(value=envelope_var, attr='target_component')),
                ast.keyword(arg='query', 
                          value=ast.Attribute(value=envelope_var, attr='data')),
                ast.keyword(arg='target_port', 
                          value=ast.Constant(value='query'))
            ]
        
        return node
    
    def _fix_send_to_component(self, node):
        """Fix send_to_component(envelope) -> send_to_component(target_component=..., data=..., target_port=...)"""
        if len(node.args) == 1 and not node.keywords:
            # Assume single arg is MessageEnvelope
            envelope_var = node.args[0]
            
            # Create new keyword arguments
            node.args = []
            node.keywords = [
                ast.keyword(arg='target_component',
                          value=ast.Attribute(value=envelope_var, attr='target_component')),
                ast.keyword(arg='data',
                          value=ast.Attribute(value=envelope_var, attr='data')),
                ast.keyword(arg='target_port',
                          value=ast.Constant(value='input'))
            ]
        
        return node