#!/usr/bin/env python3
"""Quick roadmap cleanup: downgrade misleading ✔️ tags to 🚧.

Usage:
  python fix_false_status.py <markdown_file> [--inplace]

If --inplace is provided, the file is modified in place; otherwise output is printed.
"""
import argparse
import re
from pathlib import Path

def process(content: str) -> str:
    # Replace standalone checkmark emoji/markdown with 🚧
    # Patterns: "✔️", "✅", "[x]", "[X]" within task lists
    replacements = {
        "✔️": "🚧",
        "✅": "🚧",
        "[x]": "[ ]",
        "[X]": "[ ]",
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    return content

def main():
    parser = argparse.ArgumentParser(description="Downgrade false complete status tags")
    parser.add_argument("file", help="Markdown file to process")
    parser.add_argument("--inplace", action="store_true", help="Modify file in place")
    args = parser.parse_args()

    path = Path(args.file)
    data = path.read_text(encoding="utf-8")
    updated = process(data)

    if args.inplace:
        path.write_text(updated, encoding="utf-8")
    else:
        print(updated)

if __name__ == "__main__":
    main() 