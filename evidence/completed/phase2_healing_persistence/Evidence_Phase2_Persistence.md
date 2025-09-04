=== TESTING HEALING PERSISTENCE FIX ===

This blueprint will cause:
1. Healer generates missing binding
2. Port generator changes Store.data → Store.input
3. Validation fails on schema mismatch
4. Healer adds transformation (should persist now)
🔍 DEBUG VALIDATION - Component role analysis:
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
🔍 DEBUG VALIDATION - Sources: {'event_source'}
🔍 DEBUG VALIDATION - Sinks: {'event_store'}
🔍 DEBUG VALIDATION - API pattern: has_api_endpoint=False
🔍 DEBUG VALIDATION - Store/Controller: has_store_or_controller=True

✅ Parsing succeeded!
  Binding: event_source.output → event_store.data
    Transformation: NONE
  Binding: event_source.output → event_store.input
    Transformation: NONE

============================================================
✅ HEALING PERSISTENCE FIX SUCCESSFUL
Transformations now persist across validation attempts
