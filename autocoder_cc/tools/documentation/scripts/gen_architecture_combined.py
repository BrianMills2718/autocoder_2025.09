#!/usr/bin/env python3
"""Generate Architecture_Combined.md

Usage::

    python scripts/gen_architecture_combined.py

Reads `autocoder_cc/docs/architecture/index.md` to discover the ordered list
of parts / appendices and concatenates them (with section dividers) into
`autocoder_cc/docs/architecture/Architecture_Combined.md`.

The combined file is **auto-generated** – it contains a banner so nobody edits
it by hand.  Run this script (or the pre-commit hook) after changing any of the
individual source files.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # repo root
ARCH_DIR = PROJECT_ROOT / "autocoder_cc" / "docs" / "architecture"
INDEX_FILE = ARCH_DIR / "index.md"
OUTPUT_FILE = ARCH_DIR / "Architecture_Combined.md"

# Regex for Markdown link lines in index (e.g. "1. [Part 1 – Principles](part01_principles.md)")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _ordered_files() -> list[Path]:
    if not INDEX_FILE.exists():
        sys.exit(f"❌ Cannot find {INDEX_FILE.relative_to(PROJECT_ROOT)}")

    ordered: list[Path] = []
    for line in INDEX_FILE.read_text(encoding="utf-8").splitlines():
        m = LINK_RE.search(line)
        if m:
            rel_path = PurePosixPath(m.group(1))
            candidate = ARCH_DIR / rel_path
            if candidate.exists():
                ordered.append(candidate)
            else:
                print(f"⚠️  Skipping missing part file referenced in index: {rel_path}")
    return ordered


def main() -> None:
    sources = _ordered_files()
    if not sources:
        sys.exit("❌ No part files found via index.md – aborting.")

    banner = (
        "<!---\n"
        "⚠️  AUTO-GENERATED FILE – DO NOT EDIT DIRECTLY.\n"
        "     Run `python scripts/gen_architecture_combined.py` to regenerate.\n"
        "--->\n\n"
    )

    combined_parts: list[str] = [banner]
    for path in sources:
        header = f"\n<!-- ===== {path.name} ===== -->\n\n"
        combined_parts.append(header)
        text = path.read_text(encoding="utf-8").rstrip()
        combined_parts.append(text + "\n")

    OUTPUT_FILE.write_text("".join(combined_parts), encoding="utf-8")
    size_kb = OUTPUT_FILE.stat().st_size / 1024
    rel = OUTPUT_FILE.relative_to(PROJECT_ROOT)
    print(f"✓ Wrote {rel}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main() 