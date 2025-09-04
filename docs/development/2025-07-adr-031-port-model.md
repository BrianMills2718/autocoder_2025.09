# Migration Guide: ADR-031 Port-Based Component Model

**Date:** 2025-07-18

ADR-031 replaces the legacy *Source / Transformer / Sink* type system with explicit, named **ports**. This guide explains how to update existing blueprints and components.

---

## 1. What Changed?

| Old Concept | New Concept |
|-------------|-------------|
| `type: Source` / `Sink` / `Transformer` | Optional `type` (deprecated) + mandatory `ports:` map |
| `inputs` / `outputs` arrays | `ports:` object keyed by port name |
| `schema:` string per port | `data_schema: { id, version }` |
| Validation rule *Type Validation* | *Port Semantics Validation* |

Roles (source-like, sink-like, transformer-like) are **derived** from port topology.

---

## 2. Blueprint Conversion Cheat-Sheet

### Before
```yaml
- name: data_enricher
  type: Transformer
  inputs:
    - name: raw_events
      schema: schemas.events.RawEvent
  outputs:
    - name: enriched_events
      schema: schemas.events.EnrichedEvent
```

### After
```yaml
- name: data_enricher
  type: Transformer  # DEPRECATED – safe to keep for now
  ports:
    raw_events:
      semantic_class: data_in
      direction: input
      data_schema:
        id: schemas.events.RawEvent
        version: 1
    enriched_events:
      semantic_class: data_out
      direction: output
      data_schema:
        id: schemas.events.EnrichedEvent
        version: 1
  inputs: []   # DEPRECATED – remove when generator upgraded
  outputs: []  # DEPRECATED
```

> **Tip:** You can keep the `type` field and empty `inputs`/`outputs` for backward compatibility while tooling catches up.

---

## 3. Tooling Support

Run the helper script to auto-migrate a blueprint:
```bash
python autocoder_cc/tools/scripts/port_migrate.py --in old.yaml --out new.yaml
```

## 4. FAQ

**Q: Do I have to remove `type:` right away?**  
No. It’s marked *deprecated*; removal is optional until `v4.0`.

**Q: Can outputs connect to inputs with a different schema version?**  
Only if `producer.version >= consumer.version` and the Compatibility Matrix allows the semantic_class pair.

**Q: How do I reference multiple target components?**  
`ComponentBinding` syntax is unchanged; just reference port names instead of implicit streams.

---

## 5. Rollback

If issues arise, revert to git tag `adr-031-pre-accept`.

---

Happy porting! 🎉 