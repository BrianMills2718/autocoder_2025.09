# Implementation Relevance Index

*Created: 2025-08-11*  
*Purpose: Prioritized index of documents by relevance to creating the implementation plan*

## Relevance Scoring

- **🔴 CRITICAL (10/10)**: Essential for implementation, must read
- **🟡 HIGH (7-9/10)**: Very useful, should read
- **🟢 MEDIUM (4-6/10)**: Helpful context, optional
- **⚪ LOW (1-3/10)**: Historical/reference only

---

## 🔴 CRITICAL DOCUMENTS (Must Read for Implementation)

### 1. **strategy_and_decision_index.md** [10/10]
**Why Critical**: Contains ALL 55 resolved decisions with implementation details
- v1 Definition of Done
- Concrete technical choices (SQLite, overflow policies, etc.)
- Performance targets (1000 msg/sec)
- 4-week implementation timeline
**Use For**: Primary reference during coding

### 2. **TEST_DRIVEN_MIGRATION_PLAN.md** [10/10]
**Why Critical**: Step-by-step TDD implementation approach
- Phase 1-6 with specific test examples
- Code templates for ports, components, primitives
- Exact test cases to write first
**Use For**: Daily implementation guide

### 3. **port_stream_recipe_design.md** [10/10]
**Why Critical**: Complete technical architecture specification
- Port implementation details (Parts 1-5)
- Recipe system design (Part 6)
- Error handling patterns (Part 7)
- Buffer management (Part 4)
**Use For**: Technical reference during coding

### 4. **IMPLEMENTATION_GUIDE_COMPLETE.md** [10/10]
**Why Critical**: Consolidated implementation guide with checklists
- TDD approach for each phase
- Complete code examples
- Phase-by-phase checklists
- Success metrics
**Use For**: Progress tracking and validation

### 5. **complete_file_dependency_analysis.md** [9/10]
**Why Critical**: Maps exactly which files to modify/replace
- 135 files to replace (30% of codebase)
- Which modules to keep vs rebuild
- Dependency relationships
**Use For**: Understanding scope and dependencies

---

## 🟡 HIGH RELEVANCE (Should Read)

### 6. **SELF_HEALING_INTEGRATION_PLAN.md** [8/10]
**Why Important**: Defines self-healing approach for 100% success
- Transactional healing with rollback
- 5-layer escalation chain
- Pattern detection (observability only)
**Use For**: Implementing Phase 4 self-healing

### 7. **codebase_assessment.md** [8/10]
**Why Important**: Current state analysis
- Import bug at line 1492 (must fix)
- What's working (70%) vs broken (30%)
- Module status table
**Use For**: Understanding existing code issues

### 8. **PRESERVED_ARCHITECTURE_INDEX.md** [7/10]
**Why Important**: Shows what NOT to change (89% preserved)
- Which modules to keep as-is
- Integration points to maintain
- Existing infrastructure to reuse
**Use For**: Avoiding unnecessary changes

### 9. **observability.md** [7/10]
**Why Important**: Observability implementation completed
- Simple generation logger created
- Import template fix documented
- Observable decorator pattern
**Use For**: Debugging and monitoring

### 10. **STANDARDIZED_NUMBERS.md** [7/10]
**Why Important**: Single source of truth for counts
- Official phase numbering (1-6)
- Component counts (5 primitives, 18+ current)
- File counts (~135 to replace)
**Use For**: Consistent references

---

## 🟢 MEDIUM RELEVANCE (Helpful Context)

### 11. **README.md** [6/10]
**Why Helpful**: High-level overview of the switch
- Problem statement
- Target architecture summary
- Key technical decisions table
**Use For**: Quick reference and context

### 12. **START_HERE_CONTEXT.md** [6/10]
**Why Helpful**: Entry point for understanding project
- Quick summary
- Glossary of terms
- What NOT to do list
**Use For**: Onboarding and terminology

### 13. **RESOLVED_UNCERTAINTIES.md** [5/10]
**Why Helpful**: Shows how decisions were made
- Self-healing approach reasoning
- Recipe system justification
- Buffer strategy choices
**Use For**: Understanding rationale

### 14. **notes_202508091324.md** [5/10]
**Why Helpful**: Detailed implementation notes
- Port implementation specification
- Buffer sizing strategy
- Checkpoint system design
**Use For**: Additional technical details

### 15. **current_13_component_types.md** [4/10]
**Why Helpful**: Maps current types to new primitives
- Shows complexity being reduced (18+ to 5)
- Migration mappings
**Use For**: Understanding transformation

---

## ⚪ LOW RELEVANCE (Reference Only)

### 16. **FINAL_STRATEGY_DECISION.md** [3/10]
**Why Low**: Already incorporated into strategy_and_decision_index.md
**Use For**: Historical reference only

### 17. **PLANNING_COMPLETE_SUMMARY.md** [3/10]
**Why Low**: Planning phase summary, now outdated by updates
**Use For**: Historical context

### 18. **IMPLEMENTATION_ASSESSMENT.md** [3/10]
**Why Low**: Early assessment, superseded by complete guide
**Use For**: Historical reference

### 19. **DOCUMENT_INDEX.md** [2/10]
**Why Low**: Document organization, not implementation
**Use For**: Finding other documents

### 20. **HISTORICAL_component_type_decision_complete.md** [2/10]
**Why Low**: Historical debate, decision already made
**Use For**: Understanding past reasoning

### 21. **HISTORICAL_migration_analysis_complete.md** [2/10]
**Why Low**: Historical analysis, decisions resolved
**Use For**: Archive only

### 22. **FINAL_UNCERTAINTIES_AND_INCONSISTENCIES_ASSESSMENT.md** [2/10]
**Why Low**: All uncertainties now resolved
**Use For**: Historical reference

### 23. **INCONSISTENCIES_AND_UNCERTAINTIES_FINAL.md** [2/10]
**Why Low**: Duplicate/outdated, issues resolved
**Use For**: Archive only

### 24. **MINOR_ISSUES_RESOLVED.md** [1/10]
**Why Low**: Minor issues already fixed
**Use For**: Archive only

### 25. **ORGANIZATIONAL_RESTRUCTURE_COMPLETE.md** [1/10]
**Why Low**: Document reorganization complete
**Use For**: Archive only

### 26. **ORGANIZATIONAL_RESTRUCTURE_FINAL.md** [1/10]
**Why Low**: Duplicate of above
**Use For**: Archive only

---

## 📋 RECOMMENDED READING ORDER FOR IMPLEMENTATION

### Day 1: Foundation Understanding
1. **strategy_and_decision_index.md** - All decisions
2. **README.md** - Quick overview
3. **START_HERE_CONTEXT.md** - Terminology

### Day 2: Technical Deep Dive
4. **port_stream_recipe_design.md** - Architecture spec
5. **TEST_DRIVEN_MIGRATION_PLAN.md** - TDD approach
6. **IMPLEMENTATION_GUIDE_COMPLETE.md** - Consolidated guide

### Day 3: Codebase Context
7. **complete_file_dependency_analysis.md** - What to change
8. **codebase_assessment.md** - Current issues
9. **PRESERVED_ARCHITECTURE_INDEX.md** - What to keep

### Day 4: Advanced Topics
10. **SELF_HEALING_INTEGRATION_PLAN.md** - For Phase 4
11. **observability.md** - For debugging

---

## 🎯 QUICK REFERENCE DURING CODING

Keep these 3 documents open while coding:

1. **strategy_and_decision_index.md** - For decisions
2. **TEST_DRIVEN_MIGRATION_PLAN.md** - For test examples
3. **port_stream_recipe_design.md** - For technical specs

---

## 📊 SUMMARY

- **Total Documents**: 26
- **Critical for Implementation**: 5
- **Should Read**: 5
- **Optional Context**: 5
- **Reference Only**: 11

**Minimum Reading**: Just the 5 critical documents (≈500 lines total)
**Recommended Reading**: Critical + High relevance (≈1000 lines total)
**Complete Context**: All except LOW relevance (≈1500 lines total)

---

*Use this index to efficiently navigate the documentation based on your immediate needs.*