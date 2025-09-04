#!/usr/bin/env python3
"""generate_build_lock.py

Thin first-cut implementation of the *Security Stamp* deliverable.
It traverses template directories plus `requirements.txt`, computes
SHA-256 checksums, and writes them to `build.lock` (JSON).

If the environment variable ``COSIGN_SKIP`` is **unset** the script will
shell-out to ``cosign sign`` (placeholder – currently prints the command
rather than executing).  This enables future CI wiring while letting
local developers skip signing easily.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEMPLATE_DIRS = [
    "autocoder_cc/autocoder/components",
    "autocoder_cc/autocoder/generators",
    "autocoder_cc/blueprint_language/templates",
]
REQUIREMENTS_FILE = "requirements.txt"
OUTPUT_FILE = "build.lock"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_template_hashes() -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for directory in TEMPLATE_DIRS:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        for file_path in dir_path.rglob("*.*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(Path.cwd()))
                hashes[rel_path] = sha256_of_file(file_path)
    return hashes


def collect_requirement_hashes() -> Dict[str, str]:
    req_hashes: Dict[str, str] = {}
    req_path = Path(REQUIREMENTS_FILE)
    if req_path.exists():
        for line in req_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                req_hashes[line] = hashlib.sha256(line.encode()).hexdigest()
    return req_hashes

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "templates": collect_template_hashes(),
        "requirements": collect_requirement_hashes(),
    }

    Path(OUTPUT_FILE).write_text(json.dumps(data, indent=2))
    print(f"✅ Wrote {OUTPUT_FILE} with {len(data['templates'])} template hashes and {len(data['requirements'])} dependency hashes")

    # Optional cosign signing (real call)
    if os.getenv("COSIGN_SKIP"):
        print("🔒 COSIGN_SKIP is set – skipping signing step")
        return

    cosign_key = os.getenv("COSIGN_KEY", "cosign.key")
    cmd = [
        "cosign",
        "sign",
        "--key",
        cosign_key,
        OUTPUT_FILE,
    ]
    print("🔐 Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print("✅ build.lock signed with cosign")
    except FileNotFoundError:
        print("⚠️  cosign binary not found – signature skipped")
    except subprocess.CalledProcessError as exc:
        print(f"❌ cosign failed: {exc}")


if __name__ == "__main__":  # pragma: no cover
    main() 