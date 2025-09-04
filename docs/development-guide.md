# Documentation Directory Guide

**Purpose**: This directory contains all user-facing and developer documentation for AutoCoder4_CC.

**LLM Assistant Usage**: Use this guide when working with documentation, creating new docs, or understanding the documentation structure.

---

## 📁 Directory Structure

### **Root Documentation Files**
- `README.md` - **Main documentation hub** with user-type-based navigation
- `quickstart.md` - **Quick start guide** for new users
- `contributing.md` - **Contribution guidelines** for developers
- `architecture-overview.md` - **Stable architectural vision** (rarely changes)
- `roadmap-overview.md` - **Dynamic development status** (frequently updated)

### **Core Documentation Directories**

#### `architecture/` - **Stable System Design**
**Purpose**: Defines the final architectural vision and never changes unless fundamental goals change
**Key Files**:
- `component-model.md` - Core component architecture
- `blueprint-language.md` - System specification language
- `validation-framework.md` - Multi-level validation system
- `security-framework.md` - Security architecture
- `observability.md` - Monitoring and operations
- `generation-pipeline.md` - Code generation architecture
- `runtime-orchestration.md` - System execution model

**Subdirectories**:
- `adr/` - Architecture Decision Records with governance
- `schemas/` - JSON schemas for validation

#### `development/` - **Developer Resources**
**Purpose**: Information for project contributors and LLM assistants
**Key Files**:
- `adr-governance.md` - How architectural decisions are made
- `gemini-validation.md` - External validation processes
- `onboarding.md` - Developer setup guide

**Subdirectories**:
- `api-setup/` - API key configuration guides
- `analysis/` - Development analysis work

#### `implementation_roadmap/` - **Development Planning**
**Purpose**: Detailed implementation plans and guild coordination
**Key Files**:
- `overview.md` - Implementation strategy overview
- `p0_the_forge.md` - Foundation phase details
- Guild-specific roadmaps for parallel development

#### `workflows/` - **Process Documentation**
**Purpose**: Step-by-step procedures for common tasks
**Key Files**:
- `pipeline-usage.md` - How to use the generation pipeline
- `pipeline-validation.md` - Validation procedures

### **Archive and Historical**

#### `archive/` - **Historical Documentation**
**Purpose**: Superseded documentation kept for reference
**Subdirectories**:
- `development_analysis_2025/` - Development analysis work
- `guild_setup_2025/` - Guild setup documentation
- `stabilization_2025/` - Documentation stabilization work

#### `migrations/` - **Architecture Migrations**
**Purpose**: Documentation for major architectural changes
**Example**: `2025-07-adr-031-port-model.md` - Port-based component model migration

#### `review/` - **Review Packages**
**Purpose**: Comprehensive review documentation for external validation

---

## 🎯 LLM Assistant Guidelines

### **When Working with Documentation**

#### **Reading Documentation**
1. **Start with README.md** - Understand the navigation structure
2. **Check roadmap-overview.md** - Get current development status
3. **Use architecture-overview.md** - Understand system design
4. **Reference specific architecture files** - For detailed technical information

#### **Creating Documentation**
1. **Determine Document Type**:
   - **Stable Architecture**: Goes in `architecture/` (rarely changes)
   - **Development Status**: Goes in `roadmap-overview.md`
   - **Process/Workflow**: Goes in `workflows/`
   - **Developer Resource**: Goes in `development/`

2. **Follow Documentation Standards**:
   - Use clear headings and structure
   - Include practical examples
   - Add cross-references to related documents
   - Use status indicators when appropriate

3. **Update Cross-References**:
   - Update `README.md` navigation if adding major documents
   - Add relevant links in related documents
   - Ensure ADR references are current

#### **Updating Documentation**
1. **Status Updates**: Only update `ROADMAP_OVERVIEW.md` for development progress
2. **Architecture Changes**: Only update `architecture/` files when fundamental design changes
3. **Process Updates**: Update `workflows/` when procedures change

### **Documentation Categories**

#### **User Documentation**
- **Target**: End users of AutoCoder4_CC
- **Location**: Root level (`quickstart.md`, `README.md`)
- **Style**: Task-oriented, step-by-step instructions

#### **Developer Documentation**
- **Target**: Project contributors
- **Location**: `development/`, `contributing.md`
- **Style**: Process-oriented, comprehensive guides

#### **Architecture Documentation**
- **Target**: System architects and technical stakeholders
- **Location**: `architecture/`
- **Style**: Design-oriented, stable references

#### **Roadmap Documentation**
- **Target**: Project managers and stakeholders
- **Location**: `ROADMAP_OVERVIEW.md`, `implementation_roadmap/`
- **Style**: Status-oriented, frequently updated

---

## 🔧 Common Tasks

### **Adding New Architecture Documentation**
```bash
# 1. Create file in appropriate architecture subdirectory
touch docs/architecture/new-component-design.md

# 2. Add cross-reference in related files
# Edit docs/architecture/component-model.md to reference new file

# 3. Update navigation if major addition
# Edit docs/README.md to include in navigation
```

### **Updating Development Status**
```bash
# 1. Only update ROADMAP_OVERVIEW.md for status changes
edit docs/ROADMAP_OVERVIEW.md

# 2. Add specific details to implementation roadmap
edit docs/implementation_roadmap/relevant-file.md
```

### **Creating Process Documentation**
```bash
# 1. Create workflow file
touch docs/workflows/new-process.md

# 2. Reference from contributing.md or README.md
edit docs/contributing.md
```

### **Archiving Superseded Documentation**
```bash
# 1. Move to external archive (see ARCHIVE_MOVED_NOTICE.md)
mv docs/old-doc.md /home/brian/archive/autocoder4_cc/superseded-docs/

# 2. Update cross-references to point to new location or remove
# 3. Add note in replacement document about archived version
```

---

## 📋 Quality Standards

### **Documentation Requirements**
- **Clarity**: Use clear, concise language
- **Structure**: Logical organization with proper headings
- **Examples**: Include practical, working examples
- **Cross-References**: Link to related documentation
- **Accuracy**: Keep content up-to-date and accurate

### **File Naming Conventions**
- **Lowercase with hyphens**: `component-model.md`
- **Descriptive names**: `adr-governance.md` not `process.md`
- **Consistent terminology**: Use established project terms

### **Content Standards**
- **No temporal references**: Avoid "next week", "recently", etc. in stable docs
- **Status indicators**: Use clear status markers in dynamic docs
- **Practical focus**: Include actionable information
- **Comprehensive coverage**: Cover all relevant aspects

---

## 🚨 Important Notes

### **Document Stability**
- **ARCHITECTURE_OVERVIEW.md**: Only changes when fundamental goals change
- **Architecture files**: Stable reference documents
- **ROADMAP_OVERVIEW.md**: Dynamic, frequently updated
- **Process docs**: Updated when procedures change

### **Navigation Hierarchy**
1. **README.md** - Hub document with user-type navigation
2. **Type-specific entry points** - Architecture, quickstart, contributing
3. **Detailed documentation** - Specific technical documents
4. **Cross-references** - Links between related documents

### **Archive Policy**
- **Keep historical context**: Archive rather than delete
- **Maintain organization**: Use dated archive directories
- **Update references**: Fix broken links when archiving

This documentation structure supports both human users and LLM assistants by providing clear navigation, stable references, and comprehensive coverage of all project aspects.