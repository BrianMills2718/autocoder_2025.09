# Root Cause of Stub Generation - FOUND

## Discovery
The user correctly identified that LLMs don't generate stub code unless prompted to do so. Investigation revealed the true root cause.

## Root Cause
The **recipes in `registry.py`** contain method implementations that reference stub helper methods like `_add_item`, `_get_item`, etc. 

Example from `/autocoder_cc/recipes/registry.py` lines 35-42:
```python
if action == "add_item":
    result = await self._add_item(command)
elif action == "get_item":
    result = await self._get_item(command)
elif action == "list_items":
    result = await self._list_items(command)
elif action == "delete_item":
    result = await self._delete_item(command)
```

The recipe expander was including these method implementations in the code template sent to the LLM (line 138 of expander.py). When the LLM saw these method calls without implementations, it naturally generated stub implementations for them.

## Fix Applied
Modified `/autocoder_cc/recipes/expander.py` to:
1. NOT include the recipe method implementations 
2. Instead provide only method signatures with NotImplementedError
3. Clear instructions that LLM must implement everything

Changed from:
```python
# Add method implementations from recipe
if base_primitive == "Transformer" and "transform" in methods:
    code_lines.append('    ' + methods["transform"].replace('\n', '\n    '))
```

To:
```python
# DO NOT ADD METHOD IMPLEMENTATIONS FROM RECIPE
# Add placeholder for primary method based on primitive type
if base_primitive == "Transformer":
    code_lines.append('    async def transform(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:')
    code_lines.append('        """Transform data. LLM MUST implement this."""')
    code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
    code_lines.append('        raise NotImplementedError("LLM must implement transform method")')
```

## Verification
After the fix, the recipe expander now generates:
- NO references to `_add_item`, `_get_item`, etc.
- Only method signatures with NotImplementedError
- Clear instructions for the LLM to implement everything

## Conclusion
The stub generation was caused by the recipe system providing incomplete code templates to the LLM. The LLM was correctly implementing the helper methods it saw referenced. By removing these references from the template, the LLM should now generate complete implementations without stubs.

This confirms the user's insight that LLMs don't generate stubs unless prompted to - the system was inadvertently prompting for stubs through the recipe templates.