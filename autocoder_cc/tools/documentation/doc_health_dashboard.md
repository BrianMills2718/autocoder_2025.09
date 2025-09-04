# Documentation Health Dashboard

A comprehensive tool for scanning and validating documentation health across the Autocoder codebase.

## Purpose

The Documentation Health Dashboard provides automated analysis of documentation quality, identifying issues such as:
- Broken links in markdown files
- Missing documentation for key modules
- Code example validation and syntax checking
- Architecture currency and consistency

## Features

### Link Integrity Checking
- Validates internal markdown links and anchor references
- Supports standard markdown headers, explicit anchors `{#anchor}`, and HTML anchors
- Skips external links (http/https/mailto)
- Reports broken file references and missing anchors

### Documentation Coverage Analysis
- Identifies missing README files in key directories
- Checks for module-level documentation
- Validates documentation structure and completeness

### Code Example Validation
- Parses Python code blocks in documentation
- Validates syntax using AST parsing
- Checks import statements for validity
- Identifies non-existent module references

### Architecture Currency Checks
- Verifies documented classes exist in codebase
- Identifies outdated references
- Excludes properly marked example classes
- Maintains accuracy between docs and code

### Health Scoring
- Calculates overall documentation health score (0-100)
- Applies weighted penalties for different issue types
- Provides actionable recommendations
- Tracks trends over time

## Usage

### Basic Usage

```bash
# Scan current directory
python autocoder_cc/tools/documentation/doc_health_dashboard.py

# Scan specific directory
python autocoder_cc/tools/documentation/doc_health_dashboard.py --root-dir /path/to/project

# Limit issues per category
python autocoder_cc/tools/documentation/doc_health_dashboard.py --max-issues 5
```

### Output Options

```bash
# Save custom report
python autocoder_cc/tools/documentation/doc_health_dashboard.py --output my_report.md

# Save JSON data for programmatic access
python autocoder_cc/tools/documentation/doc_health_dashboard.py --json data.json

# Both custom report and JSON
python autocoder_cc/tools/documentation/doc_health_dashboard.py --output report.md --json data.json
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--root-dir` | Root directory to scan | Current directory |
| `--output` | Output file for markdown report | `docs_health_report.md` |
| `--json` | Output JSON data to file | `docs_health_data.json` |
| `--max-issues` | Maximum issues per category | 10 |

## Output Format

### Markdown Report

The tool generates a comprehensive markdown report with:

- **Summary Statistics**: File counts, issue counts, health score
- **Link Issues**: Broken links with file locations and severity
- **Coverage Gaps**: Missing documentation with directory paths
- **Code Example Issues**: Syntax errors and import problems
- **Currency Issues**: Outdated references and missing classes
- **Recommendations**: Prioritized action items

### JSON Data

For programmatic access, the tool outputs structured JSON:

```json
{
  "scan_timestamp": "2025-07-14T11:19:25.502789",
  "summary": {
    "total_doc_files": 73,
    "total_code_files": 277,
    "link_issues": 0,
    "coverage_gaps": 0,
    "code_example_issues": 0,
    "currency_issues": 0,
    "total_issues": 0,
    "health_score": 100
  },
  "link_issues": [],
  "coverage_gaps": [],
  "code_example_issues": [],
  "currency_issues": [],
  "recommendations": []
}
```

## Health Score Calculation

The health score is calculated on a 0-100 scale:

- **Starting Score**: 100 points
- **Broken Links**: -5 points each
- **Code Example Issues**: -8 points each  
- **Coverage Gaps**: -3 points each
- **Currency Issues**: -2 points each

### Score Interpretation

- **90-100**: Excellent documentation health
- **70-89**: Good documentation with minor issues
- **50-69**: Moderate issues requiring attention
- **0-49**: Significant documentation problems

## Integration

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Documentation Health Check
  run: |
    python autocoder_cc/tools/documentation/doc_health_dashboard.py --max-issues 5
    if [ $? -ne 0 ]; then
      echo "Documentation health check failed"
      exit 1
    fi
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: doc-health-check
      name: Documentation Health Check
      entry: python autocoder_cc/tools/documentation/doc_health_dashboard.py --max-issues 3
      language: system
      files: \.(md|rst|txt)$
      pass_filenames: false
```

## Configuration

### Key Directories

The tool checks these directories for documentation coverage:

- `autocoder_cc/autocoder/`
- `autocoder_cc/blueprint_language/`
- `autocoder_cc/tools/`
- `examples/`

### Major Modules

Within the autocoder module, these submodules are checked:

- `security/`
- `components/`
- `validation/`
- `observability/`

### Example Class Detection

The tool automatically identifies and excludes example classes marked with:

- `# NOTE: This is an example class for documentation purposes only`
- `# Example class for documentation`
- `# This is an example`
- `# Example:`
- `# NOTE: Example`
- `# NOTE: These are example classes for documentation purposes only`

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure read access to scanned directories
2. **Encoding Issues**: Files should be UTF-8 encoded
3. **Large Codebases**: Use `--max-issues` to limit output size
4. **False Positives**: Check example class markers for currency issues

### Performance

- Scans typically complete in 5-30 seconds depending on codebase size
- Memory usage scales with number of files
- Consider running on subsets for very large codebases

## Status

This tool is actively maintained and used in the Autocoder development workflow. It provides essential quality assurance for documentation standards. 