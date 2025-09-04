# Gemini Documentation Review

An AI-powered tool that uses Google's Gemini model to assess documentation fidelity and comprehensiveness against source code.

## Purpose

The Gemini Documentation Review tool provides automated analysis of how well documentation matches the actual source code, identifying:
- Missing documented features
- Undocumented code behavior
- Inaccuracies between docs and code
- Documentation quality issues

## Features

### AI-Powered Analysis
- Uses Google's Gemini model for intelligent code-documentation comparison
- Analyzes documentation fidelity and comprehensiveness
- Provides detailed recommendations for improvement
- Supports multiple documentation formats

### Comprehensive Coverage
- Compares documentation against source code
- Identifies missing features and behaviors
- Detects inaccuracies and contradictions
- Suggests improvements for documentation quality

### Flexible Configuration
- Configurable input directories for docs and code
- Customizable ignore patterns
- Additional prompt customization
- Multiple output formats

## Usage

### Basic Usage

```bash
# Review documentation against source code
python autocoder_cc/tools/documentation/gemini_doc_review.py --docs docs/ --code autocoder_cc/

# Specify custom output file
python autocoder_cc/tools/documentation/gemini_doc_review.py --docs docs/ --code autocoder_cc/ --output review_report.md

# Add custom prompt focus
python autocoder_cc/tools/documentation/gemini_doc_review.py --docs docs/ --code autocoder_cc/ --prompt "Focus on API documentation accuracy"
```

### Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--docs` | Directory containing documentation files | Yes |
| `--code` | Directory containing source code | Yes |
| `--ignore` | Patterns to ignore (glob patterns) | No |
| `--prompt` | Additional prompt for the AI review | No |
| `--output` | Output file for the review report | No |

### Environment Variables

- `GEMINI_API_KEY` - Required: Your Google Gemini API key
- `GEMINI_MODEL` - Optional: Gemini model to use (default: gemini-1.5-flash)

## Output Format

The tool generates a comprehensive review report with:

### Summary Verdict
- Overall assessment of documentation fidelity
- High-level recommendations

### Missing Documented Features
- Features present in code but missing from documentation
- Detailed descriptions of what should be documented

### Undocumented Code Behavior
- Code behaviors not explained in documentation
- Internal mechanisms and implementation details

### Inaccuracies
- Contradictions between docs and code
- Outdated information

### Recommendations
- Prioritized action items for improvement
- Specific suggestions for documentation enhancement

## Example Output

```markdown
# Gemini Documentation Review
Generated: 2025-07-14 10:18:06

## Summary Verdict
**Verdict: Not faithful**

The documentation has significant gaps compared to the source code...

## Missing Documented Features
- **Feature X**: Present in code but not documented
- **Feature Y**: Missing from documentation entirely

## Undocumented Code Behavior
- **Internal Logic**: Complex algorithms not explained
- **Error Handling**: Error scenarios not covered

## Recommendations
1. **HIGH**: Document missing feature X
2. **MEDIUM**: Add examples for feature Y
3. **LOW**: Improve error handling documentation
```

## Integration

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Documentation Review
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: |
    python autocoder_cc/tools/documentation/gemini_doc_review.py \
      --docs docs/ \
      --code autocoder_cc/ \
      --output review_report.md
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: gemini-doc-review
      name: Gemini Documentation Review
      entry: python autocoder_cc/tools/documentation/gemini_doc_review.py --docs docs/ --code autocoder_cc/
      language: system
      files: \.(md|rst|txt)$
      pass_filenames: false
```

## Configuration

### Ignore Patterns

Use glob patterns to exclude files from review:

```bash
python autocoder_cc/tools/documentation/gemini_doc_review.py \
  --docs docs/ \
  --code autocoder_cc/ \
  --ignore "**/test_*.py" \
  --ignore "**/__pycache__/**"
```

### Custom Prompts

Add specific focus areas to the AI review:

```bash
python autocoder_cc/tools/documentation/gemini_doc_review.py \
  --docs docs/ \
  --code autocoder_cc/ \
  --prompt "Pay special attention to API endpoint documentation and error handling"
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure `GEMINI_API_KEY` is set correctly
2. **Rate Limits**: The tool respects Gemini API rate limits
3. **Large Codebases**: Consider reviewing specific modules separately
4. **Model Selection**: Use `GEMINI_MODEL` to specify different models

### Performance

- Review time depends on codebase size and API response times
- Large codebases may take several minutes
- Consider breaking large reviews into smaller chunks

## Status

This tool is actively maintained and provides essential AI-powered documentation quality assurance for the Autocoder project. 