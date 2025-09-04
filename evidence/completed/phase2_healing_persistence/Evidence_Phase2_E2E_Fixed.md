🔬 Testing complete system generation with healer fix...
------------------------------------------------------------
🤖 Translating natural language to blueprint...
LLM call attempt 1/6
   Fixed component type: 'Source' → 'Source'
   Fixed component type: 'Store' → 'Store'
LLM call attempt 1/6
✅ Generated blueprint YAML
📝 Blueprint preview (first 200 chars):
schema_version: "1.0.0"

system:
  name: event_processing_system
  description: A system that receives events from a source and stores them in a data store.
  version: 1.0.0
  components:
  - name: ev...

🔧 Generating system components...
Overriding of current MeterProvider is not allowed
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
✅ Centralized prompts loaded successfully - no contradictions found
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
  event_source: Source → SOURCE → SOURCE (in=0, out=1)
  event_store: Store → SINK → SINK (in=1, out=0)
[31m19:18:56 - ERROR -        🚨 Errors (0):[0m
ERROR:VerboseAutocoder:       🚨 Errors (0):
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
LiteLLM completion() model= gemini-2.5-flash; provider = gemini
ERROR:autocoder_cc.llm_providers.unified_llm_provider:Primary model failed after 6.05s (fallback disabled)
ERROR:system_generator:CRITICAL: LLM messaging selection failed: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.
[31m19:19:02 - ERROR - ❌ Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.[0m
ERROR:VerboseAutocoder:❌ Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
[31m19:19:02 - ERROR -   ❌ Generate Service Communication Configuration FAILED (⏱️ 6.05s)[0m
ERROR:VerboseAutocoder:  ❌ Generate Service Communication Configuration FAILED (⏱️ 6.05s)
[31m19:19:02 - ERROR -      💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.[0m
ERROR:VerboseAutocoder:     💥 Error: Messaging configuration generation failed: Failed to select messaging type using LLM: CRITICAL: Failed to generate response using LLM: Primary model gemini_2_5_flash failed. Error: LLM returned empty content (None) from gemini/gemini-2.5-flash. Fallback is DISABLED (enable_fallback=False). Set enable_fallback=True in config to try other models.. System generation cannot proceed without intelligent LLM capability.. System generation cannot proceed without intelligent messaging selection.
    response = future.result()
               ^^^^^^^^^^^^^^^
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
    raise self._exception
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
