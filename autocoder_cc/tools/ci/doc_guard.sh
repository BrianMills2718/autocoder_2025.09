#!/usr/bin/env bash
# tools/doc_guard.sh – CI guard ensuring roadmap & guide stay in sync
set -e
python scripts/extract_phase_headings.py docs/Enterprise_roadmap_v3.md > /tmp/phases.txt
python scripts/extract_guide_sections.py docs/Architecture_6.0.md > /tmp/sections.txt
diff -u /tmp/phases.txt /tmp/sections.txt && echo "✅ headings in sync"

grep -R --line-number "TODO" autocoder_cc/ | grep -v tests/ && {
  echo "❌ TODOs found"; exit 1;
} || echo "✅ no stray TODOs" 