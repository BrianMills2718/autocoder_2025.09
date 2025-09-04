# ADR-032: Focused LLM Generation Architecture

**Status**: Accepted  
**Date**: 2025-07-23  
**Deciders**: Development Team  
**Technical Story**: Fix fundamental LLM generation architecture issues causing 80% failure rate

## Context

Investigation of the LLM code generation system revealed critical architectural flaws:

### Current Problems
1. **Boilerplate Generation**: LLM generates 150+ lines of infrastructure code, wasting cognitive capacity
2. **Information Loss**: Blueprint business requirements stripped away during conversion to context
3. **Wrong Validation Target**: System validates boilerplate presence instead of business logic correctness
4. **Over-Contextualization**: Vague guidance ("system-wide architecture awareness") confuses LLMs
5. **Pattern Matching**: Examples encourage copying instead of solving specific problems

### Evidence
- Current system generates 6,614 characters but `has_business_logic: False`
- Success rate approximately 20% due to focusing on structure over logic
- Token waste: 80%+ spent on boilerplate instead of business requirements

## Decision

We will implement a **Focused LLM Generation Architecture** that treats LLMs as expert developers who implement business logic, while tooling handles scaffolding.

### Core Principles

1. **LLM Generates**: Business logic methods only (50-100 lines)
2. **System Injects**: Boilerplate, imports, error handling programmatically  
3. **Prompts Focus**: Specific transformation requirements, not code structure
4. **Validation Targets**: Business logic accomplishes blueprint requirements

### Architecture Changes

#### Before (Problematic)
```
Blueprint → Simplified Dict → Verbose Context → Full Component Generation → Boilerplate Validation
```

#### After (Focused)  
```
Blueprint → Business Requirements → Focused Prompt → Method Generation → Programmatic Assembly → Logic Validation
```

## Implementation Plan

### Phase 1: Blueprint Information Preservation
- Enhance `_convert_blueprint_to_dict()` to preserve business requirements
- Create `BusinessLogicSpec` dataclass for LLM requirements
- Extract specific transformation requirements from descriptions

### Phase 2: Boilerplate Separation
- Remove 150+ lines of boilerplate from prompts
- Create `ComponentAssembler` for programmatic injection
- Update generation pipeline for method-only generation

### Phase 3: Validation Refactor
- Replace boilerplate validation with business logic validation
- Validate methods accomplish specified transformations
- Check input/output schema compliance

### Phase 4: Error Handling Simplification
- Remove verbose examples and pattern-matching guidance
- Create targeted feedback based on business requirements
- Focus retry prompts on business logic issues

## Expected Benefits

### Quality Improvements
- **Success Rate**: >80% (vs current ~20%)  
- **Business Logic**: Generated methods solve actual problems
- **Maintainability**: Clear separation of concerns

### Cost Reductions
- **Token Usage**: 50% reduction per component
- **Generation Time**: 30% improvement due to focused prompts
- **Retry Frequency**: Fewer failures due to clearer requirements

### Developer Experience
- **Predictable Results**: Consistent quality across component types
- **Faster Debugging**: Business logic separate from infrastructure
- **Easier Testing**: Focused methods easier to unit test

## Consequences

### Positive
- Dramatically improved generation success rates
- Reduced token costs and generation time
- Better separation of business logic from infrastructure
- Easier maintenance and debugging
- Foundation for all future development

### Negative  
- Requires significant refactoring of generation pipeline
- Need to update all integration points
- Temporary disruption during migration
- Team needs to learn new architecture patterns

### Neutral
- Changes development workflow (business logic focus)
- Requires comprehensive testing of new approach
- Need monitoring to validate improvements

## Compliance

This ADR aligns with:
- **ADR-027**: LLM Provider Abstraction Layer (improves provider utilization)
- **ADR-031**: Component Semantics (better business logic generation)
- **TDD Requirements**: All changes implemented with test-first approach

## Migration Strategy

1. **Feature Flag**: Gradual rollout with rollback capability
2. **Parallel Implementation**: Keep existing system functional during transition  
3. **Comprehensive Testing**: Extensive test coverage before rollout
4. **Performance Monitoring**: Real-time success rate tracking
5. **Team Training**: Ensure understanding of new architecture

## Success Metrics

### Quantitative
- Generation success rate >80%
- Token usage reduction of 50%+
- Business logic quality >90%
- Generation time improvement of 30%

### Qualitative
- Generated components contain actual transformation logic
- Code is maintainable and testable
- Developer experience is improved
- System reliability increases

## References

- [LLM Generation Investigation](../../code_generation_experiments/FINDINGS_SUMMARY.md)
- [Test Evidence](../../code_generation_experiments/)
- [Current Generation Issues](../../code_generation_experiments/02_blueprint_information_flow_analysis.md)
- [Boilerplate Analysis](../../code_generation_experiments/03_boilerplate_analysis.md)