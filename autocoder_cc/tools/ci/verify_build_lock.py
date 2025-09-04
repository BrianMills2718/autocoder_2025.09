#!/usr/bin/env python3
"""verify_build_lock.py

Verify the `build.lock` signature using cosign.

Usage::

    python tools/verify_build_lock.py [--key cosign.pub] [path/to/build.lock]

If cosign binary is missing, the script exits with code 2 so CI can catch it.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_LOCK_PATH = Path("build.lock")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify build.lock signature with cosign")
    p.add_argument("lockfile", nargs="?", default=str(DEFAULT_LOCK_PATH), help="Path to build.lock")
    p.add_argument("--key", default="cosign.pub", help="Public key for verification")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    lock_path = Path(args.lockfile)
    if not lock_path.exists():
        print(f"❌ lockfile not found: {lock_path}")
        sys.exit(1)

    cmd = ["cosign", "verify", "--key", args.key, str(lock_path)]
    try:
        subprocess.run(cmd, check=True)
        print("✅ build.lock verified successfully")
    except FileNotFoundError:
        print("❌ cosign binary not found – cannot verify signature")
        sys.exit(2)
    except subprocess.CalledProcessError as exc:
        print(f"❌ cosign verify failed: {exc}")
        sys.exit(exc.returncode)


if __name__ == "__main__":  # pragma: no cover
    main() 