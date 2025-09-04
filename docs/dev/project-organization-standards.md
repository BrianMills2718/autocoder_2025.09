# Project Organization Standards

**Date**: 2025-07-19  
**Purpose**: Standards for maintaining clean project organization and preventing root directory clutter  
**Status**: Active organizational guidelines

---

## CLUTTER CATEGORIZATION

### **📋 REPORTS & VALIDATION (16 files) - ARCHIVE**
**Files**:
- `ARCHIVAL_CONSOLIDATION_REPORT.md`
- `P0-F5-VALIDATION-REPORT.md`
- `P0-F6-VALIDATION-REPORT.md`
- `P0-F6-GEMINI-VALIDATION-REPORT.md`
- `GEMINI_VALIDATION_REPORT.md`
- `PRODUCTION_STANDARDS_COMPLIANCE.md`
- `Evidence.md`
- `component_model_validation_report.md`
- `comprehensive_test_results.txt`
- `current_validation_results.txt`
- `test_real_world_integration_results.json`
- `datadog_analysis_prompt.md`
- `cursor_notes_2025.0718.md`
- `build_context_test.json`
- `llm_state_test.json`
- `mkdocs.yml`

**Action**: Move to `reports/` directory

### **🔧 DEVELOPMENT ANALYSIS (5 files) - ARCHIVE**  
**Files**:
- `COMPONENT_MODEL_PILOT_STABILIZATION_PLAN.md`
- `architecture_stabilization_analysis.md`  
- `navigation_stabilization_analysis.md`
- `COMPREHENSIVE_CROSS_REFERENCE_MAP.md`
- `CRITICAL_GUILD_STRATEGY_UPDATE.md`

**Action**: Move to `docs/archive/development_analysis_2025/`

### **🏗️ GUILD SETUP (7 files) - ARCHIVE HISTORICAL**
**Files**:
- `ENHANCED_GUILD_SETUP_COMPLETE.md`
- `ENHANCED_GUILD_STATUS.md`
- `FINAL_SETUP_STATUS.md`
- `GLOBAL_MCP_STATUS.md`
- `GUILD_AUTOMATION_SETUP.md`
- `GUILD_HOOKS_DOCUMENTATION.md`
- `READY_FOR_ENHANCED_GUILD_DEVELOPMENT.md`

**Action**: Move to `docs/archive/guild_setup_2025/`

### **🧪 TEST FILES & OUTPUTS (15 files) - ORGANIZE**
**Files**:
- `test_architectural_injection.py`
- `test_crypto_policy_integration.py`
- `test_crypto_simple.py`
- `test_fixed_generation.py`
- `test_import_validation.py`
- `test_p0_f6_comprehensive.py`
- `test_p0_f7_complete.py`
- `test_real_world_integration.py`
- `test_edge_cases_output/`
- `test_fixed_generation_output/`
- `test_injection_output/`
- `test_output/`
- `test_template_output/`

**Action**: Move to `tests/integration/` or `tests/manual/`

### **📦 DOWNLOADED PACKAGES (3 files) - ORGANIZE**
**Files**:
- `kubeseal-0.18.0-linux-amd64.tar.gz`
- `prometheus-2.45.0.linux-amd64.tar.gz`
- `prometheus-2.45.0.linux-amd64.tar.gz.1`
- `prometheus.tar.gz`

**Action**: Move to `tools/` or `bin/`

### **📊 UTILITY SCRIPTS (4 files) - ORGANIZE**
**Files**:
- `analyze_datadog_setup.py`
- `analyze_deployment_config.py`
- `prometheus_simulator.py`
- `setup-enhanced-guilds.sh`

**Action**: Move to `scripts/`

### **🎯 API SETUP (2 files) - ORGANIZE**
**Files**:
- `BRAVE_API_SETUP.md`
- `COMPREHENSIVE_GLOBAL_SETUP_COMPLETE.md`

**Action**: Move to `docs/development/api-setup/`

---

## ROOT CAUSE ANALYSIS

### **Why Files Get Dumped in Root**

#### **1. Convenience Pattern**
- **Pattern**: Quick file creation during development
- **Problem**: `touch analysis.md` instead of `touch docs/analysis/analysis.md`
- **Root Cause**: No clear structure for temporary work

#### **2. Tool Output Defaults**  
- **Pattern**: Tools output to current directory (root)
- **Problem**: Test outputs, build artifacts, downloaded packages
- **Examples**: `test_output/`, `prometheus.tar.gz`, `*.json`

#### **3. Documentation Sprawl**
- **Pattern**: Analysis documents created ad-hoc during development
- **Problem**: No clear home for development documentation
- **Examples**: All the `*_ANALYSIS.md` and `*_REPORT.md` files

#### **4. No Clear Governance**
- **Pattern**: No rules about what belongs in root
- **Problem**: Everything gets dumped there by default
- **Missing**: `.gitignore` rules, clear directory structure

---

## PREVENTION STRATEGY

### **1. Clear Root Policy**
**RULE**: Only these files allowed in project root:
- `README.md` (project overview)
- `LICENSE` (legal)
- `CHANGELOG.md` (user-facing changes)
- `pyproject.toml` (Python project config)  
- `.gitignore` (Git configuration)
- `CLAUDE.md` (development instructions)

**Everything else must have a clear home.**

### **2. Structured Work Areas**

#### **Development Work**
```
docs/
├── archive/
│   ├── development_analysis_2025/
│   ├── guild_setup_2025/
│   └── historical/
└── development/
    ├── analysis/          # Current analysis work
    ├── api-setup/         # API configuration
    └── validation/        # Development validation
```

#### **Testing Organization**  
```
tests/
├── integration/           # Integration test scripts
├── manual/               # Manual test scripts  
├── performance/          # Performance test scripts
└── outputs/              # Test output files
    ├── integration/
    ├── manual/
    └── performance/
```

#### **Tools & Utilities**
```
tools/
├── downloaded/           # Downloaded packages
├── utilities/            # Utility scripts
└── monitoring/           # Monitoring tools
```

### **3. Tool Configuration**
- **Update `.gitignore`** to exclude test outputs
- **Configure tools** to output to specific directories
- **Add pre-commit hooks** to prevent root clutter

### **4. Development Workflow**
- **Rule**: All analysis work goes in `docs/development/analysis/`
- **Rule**: All test outputs go in `tests/outputs/`  
- **Rule**: All downloaded tools go in `tools/downloaded/`
- **Rule**: All temporary work gets cleaned up weekly

---

## IMMEDIATE CLEANUP PLAN

### **Phase 1: Archive Historical (30 files)**
- Reports → `reports/`
- Development analysis → `docs/archive/development_analysis_2025/`
- Guild setup → `docs/archive/guild_setup_2025/`

### **Phase 2: Organize Active (20 files)**
- Test files → `tests/manual/` or `tests/integration/`
- Tools → `tools/`
- Utility scripts → `scripts/`

### **Phase 3: Establish Governance (5 files)**
- Update `.gitignore`
- Add root directory policy to `CLAUDE.md`
- Create pre-commit hooks
- Document directory structure

### **Expected Result**
```
autocoder4_cc/
├── README.md ✅
├── LICENSE ✅  
├── CHANGELOG.md ✅
├── CLAUDE.md ✅
├── pyproject.toml ✅
├── .gitignore ✅
├── autocoder_cc/ ✅
├── docs/ ✅
├── tests/ ✅
├── scripts/ ✅
├── tools/ ✅
├── reports/ ✅
└── [6-8 total files in root, not 65+]
```

---

## PREVENTION MEASURES

### **1. Clear Directory Purpose**
Each directory has a clear, documented purpose and owners take responsibility for organization.

### **2. Tool Configuration**  
Configure development tools to output to appropriate directories, not root.

### **3. Weekly Cleanup**
Automated or manual weekly cleanup of temporary files and development artifacts.

### **4. Pre-commit Governance**
Pre-commit hooks that warn/prevent files being added to root unless they're on the approved list.

This will transform the project from looking like a development sandbox to a professional, well-organized codebase.