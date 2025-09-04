#!/usr/bin/env python3
"""Generate Capability-Tier Markdown table.

Reads scripts/capability_tiers.yaml and rewrites the block between
`<!-- CAP_TABLE_START -->` and `<!-- CAP_TABLE_END -->` in
part02_component_model.md.

CLI:
  python scripts/gen_cap_table.py          # rewrite file in-place
  python scripts/gen_cap_table.py --check  # exit 1 if changes would occur
"""
from __future__ import annotations

import argparse
import sys
import yaml
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
PART2_PATH = ROOT / "autocoder_cc/docs/architecture/part02_component_model.md"
YAML_PATH = ROOT / "scripts/capability_tiers.yaml"
START = "<!-- CAP_TABLE_START -->"
END = "<!-- CAP_TABLE_END -->"


def load_rows() -> List[str]:
    data = yaml.safe_load(YAML_PATH.read_text())
    # sort by tier numerically, but keep reserved row 60-80 after 50
    data.sort(key=lambda x: x["tier"] if isinstance(x["tier"], int) else 100)
    rows = [
        "| Tier | Capability (example) | Enum Constant | Purpose |",
        "|------|----------------------|--------------|---------|",
    ]
    for item in data:
        tier = item["tier"]
        name = item["name"]
        enum = f"`{item['enum']}`" if item.get("enum") else "_Pending_"
        purpose = item["purpose"]
        rows.append(f"| {tier} | {name} | {enum} | {purpose} |")
    return rows


def rewrite(check_only: bool = False) -> bool:
    content = PART2_PATH.read_text(encoding="utf-8")
    if START not in content or END not in content:
        sys.stderr.write("Anchor comments not found in part02 file\n")
        sys.exit(2)

    start_idx = content.index(START) + len(START)
    end_idx = content.index(END)
    before = content[:start_idx]
    after = content[end_idx:]

    new_table = "\n" + "\n".join(load_rows()) + "\n"
    new_content = before + new_table + after

    if new_content == content:
        return False  # no changes

    if check_only:
        sys.stderr.write("Capability table out of date. Run gen_cap_table.py to update.\n")
        return True

    PART2_PATH.write_text(new_content, encoding="utf-8")
    print("Capability table regenerated.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if file would change")
    args = parser.parse_args()

    changed = rewrite(check_only=args.check)
    if args.check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main() 