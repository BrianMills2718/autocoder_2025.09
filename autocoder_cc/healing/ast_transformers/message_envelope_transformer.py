"""AST transformer to fix MessageEnvelope constructor parameters"""
import ast
from typing import Optional


class MessageEnvelopeTransformer(ast.NodeTransformer):
    """Fixes MessageEnvelope constructor parameters"""
    
    PARAM_MAPPING = {
        'sender': 'source_component',
        'recipient': 'target_component',
        'message': 'data'
    }
    
    def visit_Call(self, node):
        self.generic_visit(node)
        
        # Check if this is a MessageEnvelope constructor
        if (isinstance(node.func, ast.Name) and node.func.id == 'MessageEnvelope'):
            # Transform keyword arguments
            new_keywords = []
            has_target_port = False
            
            for keyword in node.keywords:
                if keyword.arg in self.PARAM_MAPPING:
                    # Map old param name to new
                    new_arg = self.PARAM_MAPPING[keyword.arg]
                    new_keywords.append(ast.keyword(arg=new_arg, value=keyword.value))
                elif keyword.arg == 'target_port':
                    has_target_port = True
                    new_keywords.append(keyword)
                else:
                    new_keywords.append(keyword)
            
            # Add target_port if missing
            if not has_target_port:
                new_keywords.append(ast.keyword(
                    arg='target_port',
                    value=ast.Constant(value='input')
                ))
            
            node.keywords = new_keywords
        
        return node