#!/usr/bin/env python3
"""Insert 'Last verified commit' badge into docs index.md.

This script rewrites the placeholder token `<!-- COMMIT_BADGE -->` in
`autocoder_cc/docs/architecture/index.md` with a Markdown badge that links
back to the current commit SHA.

It is intended for CI use: the modified file is used for site rendering but is
NOT checked back into git.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

INDEX_PATH = Path("autocoder_cc/docs/architecture/index.md")
PLACEHOLDER = "<!-- COMMIT_BADGE -->"

BADGE_TEMPLATE = "![commit](https://img.shields.io/badge/commit-{sha}-blue)"
LINK_TEMPLATE = "[{badge}](https://github.com/{repo}/commit/{sha})"


def get_short_sha() -> str:
    try:
        return (
            subprocess.check_output([
                "git",
                "rev-parse",
                "--short",
                "HEAD",
            ], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        # Fallback: Git metadata absent (e.g., in container build). Use env variable or placeholder.
        env_sha = os.getenv("GITHUB_SHA")
        return (env_sha[:7] if env_sha else "local")


def main() -> None:
    if not INDEX_PATH.exists():
        raise SystemExit(f"index file not found at {INDEX_PATH}")

    sha = get_short_sha()
    repo = os.getenv("GITHUB_REPOSITORY", "repo/unknown")
    badge_md = LINK_TEMPLATE.format(badge=BADGE_TEMPLATE.format(sha=sha), repo=repo, sha=sha)

    content = INDEX_PATH.read_text(encoding="utf-8")

    pattern = rf"{re.escape(PLACEHOLDER)}[\s\S]*?($|\n)"
    replacement = f"{PLACEHOLDER}\n{badge_md}\n"

    if PLACEHOLDER not in content:
        raise SystemExit("Placeholder token not found in index.md")

    new_content = re.sub(pattern, replacement, content, count=1)
    INDEX_PATH.write_text(new_content, encoding="utf-8")
    print(f"Inserted commit badge for {sha}")


if __name__ == "__main__":
    main() 