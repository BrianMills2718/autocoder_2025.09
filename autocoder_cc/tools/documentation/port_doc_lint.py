#!/usr/bin/env python3
"""Simple documentation linter that checks for lingering Source/Transformer/Sink terminology.

Usage: python port_doc_lint.py [path]
- Scans all .md files (recursively) under the given path (default: project root).
- Ignores files that contain the marker string `legacy-doc` (case-insensitive) in the first 100 lines.
- Fails with exit code 1 if any forbidden term is found.

Forbidden patterns:
  * Source/Transformer/Sink (with optional slashes or words in between)
  * three fundamental types

This script is intended to be called from CI (see docs_validation workflow).
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import List

FORBIDDEN_PATTERNS = [
    re.compile(r"Source\s*/\s*Transformer\s*/\s*Sink", re.IGNORECASE),
    re.compile(r"three\s+fundamental\s+types", re.IGNORECASE),
]

# File marker that disables lint for that file (first 100 lines only)
IGNORE_MARKER = re.compile(r"legacy-doc", re.IGNORECASE)


def scan_file(file_path: pathlib.Path) -> List[str]:
    """Return list of offending lines (line numbers & text)."""
    text = file_path.read_text(errors="ignore")
    # Quick skip if ignore marker appears early
    if IGNORE_MARKER.search("\n".join(text.splitlines()[:100])):
        return []

    offenders: List[str] = []
    for idx, line in enumerate(text.splitlines(), 1):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                offenders.append(f"{file_path}:{idx}: {line.strip()}")
                break
    return offenders


def main() -> None:
    parser = argparse.ArgumentParser(description="Port model documentation linter")
    parser.add_argument("path", nargs="?", default=".", help="Root path to scan (default: project root)")
    args = parser.parse_args()

    root = pathlib.Path(args.path).resolve()
    offenders: List[str] = []
    for md_file in root.rglob("*.md"):
        offenders.extend(scan_file(md_file))

    if offenders:
        print("::error ::Legacy Source/Transformer/Sink terminology found in documentation:")
        for off in offenders:
            print(off)
        sys.exit(1)
    else:
        print("Documentation linter: no legacy terminology found. ✅")


if __name__ == "__main__":
    main() 