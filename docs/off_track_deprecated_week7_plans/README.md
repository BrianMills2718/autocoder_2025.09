# Off-Track and Deprecated Week 7 Plans

This directory contains Week 7 plans that went off-track from the original architecture.

## Why These Plans Were Deprecated

These plans focused on "production readiness" features and Connection-centric design, which violated our original port-based architecture where:

1. **Components have Ports** (typed interfaces with Pydantic schemas)
2. **Ports connect via Connections** (simple transport layer)
3. **Type safety is maintained** through the Port abstraction

## What Went Wrong

- We started fixing the walking skeleton pragmatically using Connections directly
- External evaluators reviewed and improved our Connection class
- We kept adding production features (policies, drain parameters, etc.)
- We lost sight of the Port abstraction that provides type safety
- The Connection class became a "god class" doing what Ports should do

## The Correct Architecture

Components should interact through typed Ports:
```python
# CORRECT - Using ports
await source.output_ports["out_requests"].send(request)
message = await validator.input_ports["in_requests"].receive()

# WRONG - Bypassing ports (what these deprecated plans did)
await conn1.send(request)
message = await conn1.receive()
```

## Files in This Directory

1. **off_track_and_deprecated_WEEK_7_PLAN_20250824.md** - Initial production readiness plan
2. **off_track_and_deprecated_WEEK_7_PLAN_20250824_FINAL.md** - First revision with evaluator feedback
3. **off_track_and_deprecated_WEEK_7_PLAN_20250824_FINAL_v2.md** - Second revision with more evaluator feedback

These plans contain good ideas about production features but should not be implemented until the basic port-based architecture is working.

## Current Status

See `/home/brian/projects/autocoder4_cc/docs/WEEK_7_SIMPLIFIED_FINAL.md` for the correct Week 7 plan that:
- Completes the original anyio migration
- Fixes recipe integration
- Fixes the import bug
- Maintains the port-based architecture

The simplified plan focuses on completing the original tasks without adding unnecessary complexity.