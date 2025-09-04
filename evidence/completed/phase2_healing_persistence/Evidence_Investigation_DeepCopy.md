=== TESTING DEEP COPY SAFETY ===
Shallow copy affected by nested change: True ✅
Shallow copy list affected: True ✅
Shallow copy transformation NOT affected: False
Deep copy preserved original nested value: True ✅
Deep copy preserved original list: True ✅
Deep copy preserved original transformation: True ✅

=== TESTING DEEP COPY PERFORMANCE ===
Deep copied large blueprint (50 components, 50 bindings) 100 times
Duration: 0.180s (1.8ms per copy)
Performance acceptable (<1s for 100 copies): ✅

=== CONCLUSION ===
✅ Deep copy is SAFE and PERFORMANT for blueprint healing
Recommendation: Use copy.deepcopy() for stateful healing
