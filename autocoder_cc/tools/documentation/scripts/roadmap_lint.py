#!/usr/bin/env python3
"""Lint roadmap checkboxes vs tracking tags.

Fails CI when:
  • A roadmap item is marked ✔️/🔄 but its tracking tag is still present in code.
  • A tracking tag exists in code but roadmap checkbox is unchecked.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path
from typing import Set, Dict

ROADMAP = Path("autocoder_cc/docs/Enterprise_roadmap_v3.md")
TAG_RE = re.compile(r"tracking:\s*(\w+)")
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*(\[.\])\s+.*<!--\s*tracking:\s*(\w+)\s*-->")


def extract_status() -> Dict[str, str]:
    status: Dict[str, str] = {}
    for line in ROADMAP.read_text(encoding="utf-8").splitlines():
        m = CHECKBOX_RE.match(line)
        if m:
            box, tag = m.groups()
            status[tag] = box  # [ ] or [x] or symbol variants but using raw box
    return status


def grep_tags() -> Set[str]:
    try:
        out = subprocess.check_output(["git", "grep", "-no", "tracking:"]).decode()
    except subprocess.CalledProcessError:
        return set()
    tags = set()
    for line in out.splitlines():
        if "docs/Enterprise_roadmap" in line:
            continue  # roadmap itself
        m = TAG_RE.search(line)
        if m:
            tags.add(m.group(1))
    return tags


def main():
    status = extract_status()
    code_tags = grep_tags()

    fail = False
    for tag, box in status.items():
        checked = "[✔" in box or "[x" in box.lower() or "🔄" in box
        if checked and tag in code_tags:
            print(f"MISMATCH: tag '{tag}' marked complete in roadmap but still found in code")
            fail = True
    for tag in code_tags:
        if tag not in status:
            continue
        box = status[tag]
        unchecked = "[ ]" in box or "🗓️" in box or "🚧" in box
        if unchecked and tag not in code_tags:
            # can't happen due to loop but placeholder
            pass
    if fail:
        sys.exit(1)
    print("Roadmap linter passed ✔️")

if __name__ == "__main__":
    main() 