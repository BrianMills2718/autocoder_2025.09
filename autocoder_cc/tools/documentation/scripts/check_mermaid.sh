#!/usr/bin/env bash
# Validate Mermaid diagrams using mmdc
# Requires mermaid-cli installed (npm i -g @mermaid-js/mermaid-cli)
set -euo pipefail

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

fail=0
while IFS= read -r -d '' file; do
  # extract each mermaid block into temp file and validate
  awk '/```mermaid/{flag=1;next}/```/{flag=0}flag' "$file" | \
    tee "$tmpdir/diagram.mmd" >/dev/null
  if [ -s "$tmpdir/diagram.mmd" ]; then
    if ! mmdc --quiet -i "$tmpdir/diagram.mmd" -o /dev/null; then
      echo "Mermaid syntax error in $file" >&2
      fail=1
    fi
    > "$tmpdir/diagram.mmd"
  fi
done < <(git ls-files 'autocoder_cc/docs/**/*.md' -z)

if [ $fail -eq 1 ]; then
  echo "Mermaid diagram validation failed" >&2
  exit 1
fi

echo "Mermaid diagrams valid ✔️" 