# Development Directory Guide

**Purpose**: Development standards, guidelines, and organizational policies for AutoCoder4_CC project maintenance.

**LLM Assistant Usage**: Use this guide when working with project organization, development standards, or maintenance workflows.

---

## 📁 Development Standards

### **Project Organization Standards**

#### `project-organization-standards.md` - **Project Organization Guidelines**
**Purpose**: Standards for maintaining clean project organization and preventing root directory clutter
**Usage**: Reference for project structure decisions and file placement guidelines
**Key Standards**:
- Root directory policy (only 6-8 essential files allowed)
- Clear directory structure for development work
- Tool configuration to prevent clutter
- Prevention strategies for maintaining organization

**Quick Reference**:
```bash
# Root directory should only contain:
# - README.md, LICENSE, CHANGELOG.md, CLAUDE.md, pyproject.toml, .gitignore
# Everything else has a specific home in subdirectories
```

---

## 🎯 LLM Assistant Development Guidelines

### **Using Development Standards**

#### **Project Organization**
```bash
# Before creating any new file, check organization standards
cat docs/dev/project-organization-standards.md

# Follow directory structure guidelines
# - Development analysis → docs/development/analysis/
# - Test outputs → tests/outputs/
# - Downloaded tools → tools/downloaded/
# - Temporary work → appropriate subdirectory
```

### **Development Best Practices**

#### **File Placement Guidelines**
1. **Root Directory**: Only essential project files (README, LICENSE, etc.)
2. **Development Work**: `docs/development/` or appropriate subdirectory
3. **Test Files**: `tests/` with proper categorization
4. **Tools & Scripts**: `tools/` and `scripts/` with clear organization
5. **Configuration**: `config/` with logical grouping

#### **Preventing Project Clutter**
1. **Before creating files**: Identify proper location based on purpose
2. **Tool outputs**: Configure tools to output to appropriate directories
3. **Temporary work**: Use designated temporary areas, clean up regularly
4. **Documentation**: Follow documentation structure guidelines

### **Maintenance Workflows**

#### **Regular Organization Checks**
```bash
# Check root directory for clutter
ls -la | wc -l  # Should be < 10 files/directories

# Review project structure
tree -d -L 2

# Validate organization standards compliance
docs/dev/project-organization-standards.md
```

#### **Development Workflow Standards**
1. **Analysis Work**: Document in `docs/development/analysis/`
2. **API Setup**: Use `docs/development/api-setup/`
3. **Validation**: Place in `docs/development/validation/`
4. **Archive**: Use `docs/archive/` for historical content

---

## 🔧 Project Structure Guidelines

### **Approved Root Directory Content**
**Essential Files Only**:
- `README.md` - Project overview and quick start
- `LICENSE` - Legal/licensing information
- `CHANGELOG.md` - User-facing changes
- `CLAUDE.md` - Development instructions for LLM assistants
- `pyproject.toml` - Python project configuration
- `.gitignore` - Git configuration

**Essential Directories Only**:
- `autocoder_cc/` - Main codebase
- `docs/` - Documentation
- `tests/` - Test suite
- `scripts/` - Utility scripts
- `tools/` - Development tools
- `config/` - Configuration files

### **Development Directory Structure**
```
docs/
├── README.md              # Documentation hub
├── architecture-overview.md   # Core architectural vision
├── roadmap-overview.md     # Current roadmap status
├── dev/                   # Development standards and guidelines
│   ├── CLAUDE.md          # This guide
│   └── project-organization-standards.md
├── reference/             # Reference documentation
├── implementation_roadmap/# Roadmap details
├── development/           # Current development work
│   ├── analysis/          # Development analysis
│   ├── api-setup/         # API configuration guides
│   └── validation/        # Development validation
└── archive/              # Historical/superseded content
    ├── development_analysis_2025/
    ├── guild_setup_2025/
    └── stabilization_2025/
```

### **Tool and Output Organization**
```
tools/
├── downloaded/           # Downloaded packages and tools
├── utilities/            # Utility scripts
└── monitoring/           # Monitoring tools

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── performance/         # Performance tests
└── outputs/             # Test output files
    ├── integration/
    ├── manual/
    └── performance/
```

---

## 🚨 Important Guidelines

### **Development Standards**
1. **File Placement**: Every file has a proper home - use organization standards
2. **Root Directory**: Keep clean - only essential project files
3. **Documentation**: Follow documentation structure for consistency
4. **Tool Configuration**: Configure tools to output to appropriate directories
5. **Regular Cleanup**: Weekly cleanup of temporary files and development artifacts

### **Quality Maintenance**
1. **Organization Reviews**: Regular checks of project structure compliance
2. **Standard Updates**: Keep organization standards current with project evolution
3. **Documentation Maintenance**: Keep development documentation up-to-date
4. **Archive Management**: Proper archival of historical/superseded content
5. **Prevention Focus**: Prevent clutter rather than cleaning up after the fact

### **Development Efficiency**
1. **Clear Structure**: Well-organized project enables faster development
2. **Predictable Locations**: Developers can quickly find relevant content
3. **Reduced Confusion**: Clear separation prevents mixing of content types
4. **Professional Appearance**: Well-organized project demonstrates quality
5. **Maintenance Ease**: Organized structure reduces maintenance burden

This development directory provides the standards and guidelines needed to maintain a clean, professional, and well-organized AutoCoder4_CC project structure.