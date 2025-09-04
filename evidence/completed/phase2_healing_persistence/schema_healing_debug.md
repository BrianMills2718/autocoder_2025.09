=== TESTING SCHEMA HEALING ===

Blueprint structure:
  Source output schema: common_object_schema
  Store input schema: ItemSchema
  Binding: event_source.output → event_store.input
  Has transformation: False

After healing:
  Has transformation: True
  Transformation: convert_common_object_schema_to_ItemSchema

=== DEBUGGING ===
Source outputs: [{'name': 'output', 'schema_type': 'common_object_schema'}]
Store inputs: [{'name': 'input', 'schema': 'ItemSchema'}]

Binding format:
  _uses_alt_format: True
  from_component: event_source
  to_components: ['event_store']
  from_port: output
  to_ports: ['input']

============================================================
✅ Schema healing works
