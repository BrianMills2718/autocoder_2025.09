#!/usr/bin/env python3
"""docs/doc_matrix.py – CI guardrail for heading drift

Checks that every H1/H2 heading listed in the YAML matrix exists (verbatim) in its
Markdown file.  Fails with exit-code 1 when mismatches are found.

Usage:
    python scripts/doc_matrix.py [matrix_yaml]

If *matrix_yaml* is omitted it defaults to
`autocoder_cc/docs/architecture/appendix_a_xref_matrix.yaml`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Dict

import yaml

# Regex to capture Markdown headings – we only care about text after the '#...'
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")

# ----------------------------------------------------------------------------


def load_matrix(matrix_path: Path) -> Dict[Path, List[str]]:
    """Load the YAML file and normalise it to Path→list[str]."""
    if not matrix_path.exists():
        sys.stderr.write(f"ERROR: matrix file '{matrix_path}' not found\n")
        sys.exit(2)

    with matrix_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "files" not in data:
        sys.stderr.write("ERROR: matrix YAML must have a top-level 'files' mapping\n")
        sys.exit(2)

    result: Dict[Path, List[str]] = {}
    for fname, headings in data["files"].items():
        if not isinstance(headings, list):
            sys.stderr.write(f"ERROR: headings for '{fname}' should be a list\n")
            sys.exit(2)
        result[Path(fname)] = [str(h) for h in headings]
    return result


def extract_headings(md_path: Path) -> List[str]:
    """Return all heading texts found in the Markdown file."""
    if not md_path.exists():
        sys.stderr.write(f"ERROR: referenced markdown file '{md_path}' not found\n")
        sys.exit(2)

    out: List[str] = []
    with md_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            m = HEADING_RE.match(line)
            if m:
                out.append(m.group(2).strip())
    return out


def sed_escape(text: str) -> str:
    """Escape forward-slashes so the string can be used inside sed s/.../.../."""
    return text.replace("/", r"\/")


def main(argv: List[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    matrix_file = Path(argv[0]) if argv else Path(
        "autocoder_cc/docs/architecture/appendix_a_xref_matrix.yaml"
    )

    matrix = load_matrix(matrix_file)
    drift = False

    for md_path, expected_headings in matrix.items():
        actual_headings = extract_headings(md_path)
        for expected in expected_headings:
            if expected not in actual_headings:
                drift = True
                print(
                    f"DRIFT: {md_path} – missing or changed heading\n"
                    f"  expected: {expected}"
                )
                if actual_headings:
                    old = sed_escape(actual_headings[0])
                    new = sed_escape(expected)
                    print(f"  fix: sed -i 's/{old}/{new}/' {md_path}")
                else:
                    print("  fix: (add heading manually)")

    if drift:
        print("\nDoc-matrix validation failed – update the headings or the YAML matrix.")
        sys.exit(1)

    print("Doc-matrix validation passed. ✔️")


if __name__ == "__main__":
    main()