# CLAUDE.md Update Command - Evidence-Based Development Workflow

## Overview
commit then update CLAUDE.md to clear out resolved tasks/outdated information and populate it with instructions for resolving the next tasks using evidence-based development practices. The instructions should be detailed enough for a new LLM to implement with no context beyond CLAUDE.md and referenced files. make sure to include the testing plan in the CLAUDE.md

## Core CLAUDE.md Requirements

### 1. Coding Philosophy Section (Mandatory)
Every CLAUDE.md must include:
- **NO LAZY IMPLEMENTATIONS**: No mocking/stubs/fallbacks/pseudo-code/simplified implementations
- **FAIL-FAST PRINCIPLES**: Surface errors immediately, don't hide them
- **EVIDENCE-BASED DEVELOPMENT**: All claims require raw evidence in structured evidence files
- **DON'T EDIT GENERATED SYSTEMS**: Fix the autocoder itself, not generated outputs
- **VALIDATION + SELF-HEALING**: Every validator must have coupled self-healing capability

### 2. Codebase Structure Section (Mandatory)  
Concisely document:
- All relevant planning documentation or other relevant documentation.
- Key entry points and main orchestration files
- Module organization and responsibilities

### 3. Evidence Structure Requirements (Updated)
```
evidence/
├── current/
│   └── Evidence_[PHASE]_[TASK].md     # Current development phase only
├── completed/  
│   └── Evidence_[PHASE]_[TASK].md     # Completed phases (archived)

```

**CRITICAL**: 
- Evidence files must contain ONLY current phase work (no historical contradictions)
- Raw execution logs required for all claims
- No success declarations without demonstrable proof
- Archive completed phases to avoid chronological confusion


