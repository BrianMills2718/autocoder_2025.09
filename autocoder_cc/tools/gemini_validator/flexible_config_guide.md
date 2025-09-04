# Gemini Code Review - Flexible Configuration Guide

> **Tool-Specific README:** This file documents flexible configuration for the Gemini review tool. For project overview and onboarding, start at the root `README.md`.

This tool now supports flexible per-project configuration, making it easy to use across different projects with different requirements.

## Quick Start for New Projects

### 1. Initialize Configuration
```bash
# In your project directory
python /path/to/gemini_review.py --init
```

This creates `.gemini-review.yaml` with sensible defaults for your project.

### 2. Run Review
```bash
# The tool automatically finds and uses .gemini-review.yaml
python /path/to/gemini_review.py
```

## Configuration File Format

Configuration files can be YAML or JSON. The tool searches for these files:
- `.gemini-review.yaml` / `.gemini-review.yml` / `.gemini-review.json`
- `gemini-review.yaml` / `gemini-review.yml` / `gemini-review.json`

### Example Configuration

```yaml
project_name: "My Awesome Project"
project_path: "."
output_format: "xml"  # or "markdown" for smaller files
output_file: "gemini-review.md"
keep_repomix: false

# Files/folders to exclude from analysis
ignore_patterns:
  - "*.pyc"
  - "__pycache__"
  - "node_modules"
  - ".git"
  - "venv"
  - "build"
  - "dist"

# Documentation to include in the review
documentation_files:
  - "README.md"
  - "docs/*.md"
  - "ARCHITECTURE.md"

# Optional: Claims to evaluate critically
claims_of_success: |
  Our codebase is:
  - Fully tested with 90% coverage
  - Following all best practices
  - Production ready

# Optional: Custom review focus
custom_prompt: |
  Focus on security vulnerabilities and performance bottlenecks

# Review templates for quick access
review_templates:
  security:
    prompt: "Perform security audit focusing on OWASP top 10"
    focus: ["authentication", "authorization", "input validation"]
  
  performance:
    prompt: "Identify performance bottlenecks"
    focus: ["algorithms", "database queries", "caching"]
```

## Usage Examples

### Basic Usage (Auto-detect Config)
```bash
# Uses .gemini-review.yaml if present
python gemini_review.py
```

### Specify Config File
```bash
python gemini_review.py --config my-project-config.yaml
```

### Use Review Templates
```bash
# Use predefined template from config
python gemini_review.py --template security

# Templates: security, performance, refactoring, django, fastapi, etc.
```

### Override Config Settings
```bash
# Command-line args override config file
python gemini_review.py --format markdown --keep-repomix
```

### Multiple Projects Setup

Create project-specific configs:
```
my-workspace/
├── project-a/
│   └── .gemini-review.yaml    # Auto-detected when in project-a
├── project-b/
│   └── .gemini-review.yaml    # Auto-detected when in project-b
└── configs/
    ├── django-project.yaml     # Shared configs
    └── react-project.yaml
```

Use shared configs:
```bash
cd project-a
python gemini_review.py --config ../configs/django-project.yaml
```

## Example Configurations by Project Type

### Python/Django Project
```yaml
project_name: "Django Web App"
ignore_patterns:
  - "*.pyc"
  - "__pycache__"
  - "staticfiles"
  - "media"
  - "*.sqlite3"
  
documentation_files:
  - "README.md"
  - "docs/*.md"
  
custom_prompt: |
  Review for Django best practices:
  - Security settings
  - Model design
  - View patterns
  - Template security
```

### Node.js/React Project
```yaml
project_name: "React SPA"
ignore_patterns:
  - "node_modules"
  - "build"
  - "dist"
  - ".next"
  - "coverage"
  
custom_prompt: |
  Focus on:
  - React hooks usage
  - Component design
  - State management
  - Bundle size optimization
```

### Enterprise Compliance Review
```yaml
project_name: "Enterprise System"
documentation_files:
  - "docs/roadmap.md"
  - "docs/architecture.md"
  
claims_of_success: |
  - Meets all compliance requirements
  - Fully scalable architecture
  - 99.9% uptime capable
  
custom_prompt: |
  Critically evaluate against enterprise standards
```

## Advanced Features

### Hierarchical Config Search
The tool searches for config files from the current directory up to the root:
```
/home/user/projects/myapp/src/components/ → Searches:
  1. ./gemini-review.yaml
  2. ../gemini-review.yaml
  3. ../../gemini-review.yaml
  4. ... up to root
```

### Environment-Specific Configs
```bash
# Development review
python gemini_review.py --config .gemini-review.dev.yaml

# Production audit
python gemini_review.py --config .gemini-review.prod.yaml
```

### CI/CD Integration
```yaml
# .gemini-review.ci.yaml
output_file: "reports/code-review-${BUILD_NUMBER}.md"
custom_prompt: |
  Focus on:
  - New code in this PR
  - Breaking changes
  - Security issues
```

## Best Practices

1. **Version Control**: Commit your `.gemini-review.yaml` to share review settings with your team

2. **Ignore Patterns**: Be generous with ignore patterns to reduce token usage and focus on relevant code

3. **Documentation**: Always include key documentation files for context

4. **Templates**: Create templates for common review types in your organization

5. **Claims**: Use claims for accountability - paste previous review outcomes or team assertions

## Troubleshooting

- **Config not found**: Use `--config` to specify path explicitly
- **Large projects**: Use `--format markdown` and aggressive ignore patterns
- **Token limits**: Add more ignore patterns or split reviews by subdirectory

## Migration from Hardcoded Reviews

Replace hardcoded scripts with configs:

```bash
# Old way (hardcoded script)
./review_autocoder.sh

# New way (flexible config)
python gemini_review.py --config enterprise-roadmap.yaml
```

The configuration system makes the tool reusable across all your projects!