#!/usr/bin/env bash
# run_cycle_validation.sh – run Gemini validation against the newest cycle claims
# Usage: ./run_cycle_validation.sh [extra-gemini-args]
# It detects the highest cycle_XX*.md or .yaml in validation_claims/, builds the command,
# and executes the project-specific Gemini reviewer wrapper.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLAIMS_DIR="$ROOT_DIR/validation_claims"

latest_file=$(ls -1 "$CLAIMS_DIR" | grep -E 'cycle_[0-9]+' | sort -V | tail -n 1)
if [[ -z "$latest_file" ]]; then
  echo "❌ No cycle claims file found in $CLAIMS_DIR" >&2
  exit 1
fi

claims_path="$CLAIMS_DIR/$latest_file"

python autocoder_cc/tools/validation/gemini_cycle_review.py autocoder_cc --claims "$claims_path" "$@" 