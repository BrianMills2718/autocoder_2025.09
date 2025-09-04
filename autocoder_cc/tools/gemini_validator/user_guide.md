# Gemini Code Review Automation

> **Tool-Specific README:** This file documents the Gemini review tool. For project overview and onboarding, start at the root `README.md`.

This tool automates your code review workflow by:
1. Using `repomix` to package your codebase into an AI-friendly format
2. Sending it to Gemini AI for comprehensive analysis
3. Saving the critique and guidance locally

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Node.js is installed (required for repomix):
```bash
node --version  # Should show v14 or higher
```

3. Your Gemini API key is already configured in `.env`

## Usage

### Basic Review (current directory)
```bash
python gemini_review.py
```

### Review a specific project
```bash
python gemini_review.py /path/to/your/project
```

### Focus on specific areas
```bash
python gemini_review.py --prompt "Focus on security vulnerabilities and performance bottlenecks"
```

### Use markdown format (smaller file size)
```bash
python gemini_review.py --format markdown
```

### Keep the repomix output for debugging
```bash
python gemini_review.py --keep-repomix
```

### Review the autocoder project with architectural focus
```bash
python gemini_review.py ./autocoder_cc --prompt "Analyze against the Enterprise Roadmap v2 requirements"
```

## Output

The tool generates:
- `gemini-review.md` - The AI's analysis and recommendations
- `repomix-output.xml` or `repomix-output.md` - The packaged codebase (deleted by default)

## Features

- **Secure**: API key stored in `.env` file (git-ignored)
- **Flexible**: Supports custom prompts for focused reviews
- **Efficient**: Uses repomix to handle large codebases
- **Clean**: Automatically cleans up temporary files
- **Progress**: Shows status updates during processing

## Example Prompts

```bash
# Security audit
python gemini_review.py --prompt "Perform a thorough security audit, focusing on OWASP top 10"

# Performance review
python gemini_review.py --prompt "Identify performance bottlenecks and suggest optimizations"

# Architecture review
python gemini_review.py --prompt "Evaluate the architecture for scalability and maintainability"

# Best practices
python gemini_review.py --prompt "Check adherence to Python/JavaScript best practices and PEP standards"
```

## Troubleshooting

1. **"npx not found"**: Install Node.js from https://nodejs.org/
2. **Token limit errors**: Use `--format markdown` for smaller output
3. **API errors**: Check your API key and Gemini API status

## Security Note

Your API key is stored in `.env` which is git-ignored. Never commit API keys to version control.