#!/usr/bin/env python3
"""CLI wrapper for build.lock sign/verify operations."""
from __future__ import annotations

import argparse
from pathlib import Path
from autocoder_cc.lockfile import sign_lockfile, verify_lockfile, generate_lockfile


def _cmd_sign(args):
    sign_lockfile(Path(args.lockfile), args.key)


def _cmd_verify(args):
    verify_lockfile(Path(args.lockfile), args.key)


def _cmd_generate(args):
    deps = {}
    for pair in args.dep:
        name, ver = pair.split("==", 1)
        deps[name] = ver
    generate_lockfile(args.build_id, deps)


def main():
    p = argparse.ArgumentParser("autocoder lock helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_sign = sub.add_parser("sign", help="sign build.lock.json")
    s_sign.add_argument("lockfile", nargs="?", default="build.lock.json")
    s_sign.add_argument("--key", default=None)
    s_sign.set_defaults(func=_cmd_sign)

    s_ver = sub.add_parser("verify", help="verify build.lock.json signature")
    s_ver.add_argument("lockfile", nargs="?", default="build.lock.json")
    s_ver.add_argument("--key", default=None)
    s_ver.set_defaults(func=_cmd_verify)

    s_gen = sub.add_parser("generate", help="generate lockfile with deps (dev helper)")
    s_gen.add_argument("build_id")
    s_gen.add_argument("dep", nargs="*", help="dependency spec name==version")
    s_gen.set_defaults(func=_cmd_generate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main() 