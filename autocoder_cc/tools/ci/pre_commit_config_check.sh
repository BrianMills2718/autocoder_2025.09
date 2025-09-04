#!/bin/bash
# Pre-commit hook to check for config/configuration consistency issues
# 
# Usage:
#   1. Copy this file to .git/hooks/pre-commit
#   2. Make it executable: chmod +x .git/hooks/pre-commit
#   3. Commits will be blocked if consistency issues are found

set -e

echo "🔍 Checking for config/configuration consistency issues..."

# Run the consistency checker
python3 autocoder_cc/tools/validation/config_consistency_check.py \
    --path autocoder_cc \
    --exit-code

if [ $? -eq 0 ]; then
    echo "✅ Config/configuration consistency check passed"
else
    echo "❌ Config/configuration consistency check failed"
    echo ""
    echo "💡 Run the following to auto-fix issues:"
    echo "   python3 autocoder_cc/tools/validation/config_consistency_check.py --path autocoder_cc --fix"
    echo ""
    echo "Or add the fix to your commit:"
    echo "   git add -u && git commit --amend"
    exit 1
fi