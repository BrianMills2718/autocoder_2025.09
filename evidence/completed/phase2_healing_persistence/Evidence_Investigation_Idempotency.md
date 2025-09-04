=== TESTING HEALER IDEMPOTENCY ===

1st healing:
  Bindings: 3
  Has policy: True

2nd healing (on already healed):
  Bindings: 3
  Has policy: True

3rd healing (on twice healed):
  Bindings: 3
  Has policy: True

Transformations:
  Healing 1: 1 transformations
    - convert_common_object_schema_to_SomeSchema
  Healing 2: 1 transformations
    - convert_common_object_schema_to_SomeSchema
  Healing 3: 1 transformations
    - convert_common_object_schema_to_SomeSchema

Binding count stable: True ✅
Transformations stable: True ✅

=== TESTING SAME HEALER INSTANCE ===
Same healer - healing 1: 3 bindings
Same healer - healing 2: 3 bindings
Same healer - healing 3: 3 bindings
Same healer instance stable: True ✅

Healer stagnation count: 2
Healing history length: 3

=== CONCLUSION ===
✅ Healer is IDEMPOTENT
Safe to use for stateful healing
