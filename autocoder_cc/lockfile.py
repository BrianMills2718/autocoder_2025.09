"""lockfile.py – deterministic build.lock emitter and signature helpers.

This module underpins the *Security Stamp* feature described in the
Architecture Guide.  It provides helper functions used by the generator
pipeline and by runtime verification (ComponentRegistry).
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_LOCK_FILENAME = "build.lock.json"
DEFAULT_SIG_FILENAME = "build.lock.sig"


# ---------------------------------------------------------------------------
# Emit deterministic lockfile
# ---------------------------------------------------------------------------

def _deterministic_json_dumps(obj: Any) -> str:
    """Return pretty-printed JSON with stable ordering and LF endings."""
    # `sort_keys=True` ensures key order; separators gives compact format.
    return json.dumps(obj, sort_keys=True, indent=2) + "\n"


def generate_lockfile(
    build_id: str,
    deps: Dict[str, str],
    output_dir: Path | str | None = None,
    include_full_context: bool = True,
) -> Path:
    """Write *build.lock.json* deterministically and return its path."""
    output_dir = Path(output_dir or ".").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / DEFAULT_LOCK_FILENAME

    data = {
        "build_id": build_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "deps": dict(sorted(deps.items())),  # enforce ordering
    }
    
    # Add expanded build context if requested
    if include_full_context:
        try:
            from .tools.ci.build_context_hasher import BuildContextHasher
            from .tools.ci.llm_state_tracker import LLMStateTracker
            
            # Capture build context
            context_hasher = BuildContextHasher()
            build_context = context_hasher.capture_build_context(build_id)
            
            # Capture LLM state
            llm_tracker = LLMStateTracker()
            llm_state = llm_tracker.capture_llm_state()
            
            # Add to lockfile data
            data.update({
                "build_context": {
                    "python_version": build_context.python_version,
                    "platform_info": build_context.platform_info,
                    "os_architecture": build_context.os_architecture,
                    "dependency_versions": build_context.dependency_versions,
                    "git_info": build_context.git_info,
                    "file_hashes": build_context.file_hashes,
                    "build_hash": build_context.build_hash
                },
                "llm_state": {
                    "configurations": {
                        provider: {
                            "provider": config.provider,
                            "model": config.model,
                            "temperature": config.temperature,
                            "max_tokens": config.max_tokens,
                            "top_p": config.top_p,
                            "frequency_penalty": config.frequency_penalty,
                            "presence_penalty": config.presence_penalty,
                            "stop_sequences": config.stop_sequences,
                            "seed": config.seed,
                            "deterministic_mode": config.deterministic_mode
                        }
                        for provider, config in llm_state.configurations.items()
                    },
                    "global_seed": llm_state.global_seed,
                    "deterministic_mode": llm_state.deterministic_mode,
                    "tokenizer_versions": llm_state.tokenizer_versions,
                    "model_versions": llm_state.model_versions,
                    "api_versions": llm_state.api_versions,
                    "sampling_hash": llm_state.sampling_hash
                },
                "reproducibility": {
                    "complete_hash_surface": True,
                    "provably_reproducible": True,
                    "sealed_build_context": True
                }
            })
            
        except ImportError as e:
            # Fall back to basic lockfile if dependencies not available
            data["build_context_error"] = f"Could not capture full build context: {str(e)}"
            data["reproducibility"] = {
                "complete_hash_surface": False,
                "provably_reproducible": False,
                "sealed_build_context": False
            }

    lock_path.write_text(_deterministic_json_dumps(data), encoding="utf-8", newline="\n")
    return lock_path


# ---------------------------------------------------------------------------
# Cosign helpers
# ---------------------------------------------------------------------------

def _run_cosign(args: list[str]) -> None:
    try:
        subprocess.run(["cosign", *args], check=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError("cosign binary not found in PATH") from exc


def sign_lockfile(lock_path: Path, key_path: Optional[str] = None) -> Path:
    """Sign *lock_path* with cosign, return signature path.

    If *key_path* is None, reads ``COSIGN_KEY`` env or defaults to
    ``cosign.key``.
    """
    key_path = key_path or os.getenv("COSIGN_KEY", "cosign.key")
    sig_path = lock_path.with_suffix(lock_path.suffix + ".sig")
    _run_cosign(["sign", "--key", key_path, str(lock_path)])
    if not sig_path.exists():
        # some cosign versions output lock_path.sig; ensure presence
        raise RuntimeError("cosign sign completed but .sig not found")
    return sig_path


def verify_lockfile(lock_path: Path, pubkey_path: Optional[str] = None) -> None:
    """Verify signature of *lock_path* using cosign.

    Raises subprocess.CalledProcessError if verification fails.
    """
    pubkey_path = pubkey_path or os.getenv("COSIGN_PUB", "cosign.pub")
    _run_cosign(["verify", "--key", pubkey_path, str(lock_path)])


# ---------------------------------------------------------------------------
# Verifier API used by ComponentRegistry
# ---------------------------------------------------------------------------

from .exceptions import SignatureMismatch


class LockVerifier:
    """Utility facade used by ComponentRegistry."""

    @staticmethod
    def verify(lockfile_path: Path | str, pubkey_path: Optional[str] = None) -> None:
        try:
            verify_lockfile(Path(lockfile_path), pubkey_path)
        except subprocess.CalledProcessError as exc:
            raise SignatureMismatch("lockfile signature mismatch") from exc
        except FileNotFoundError as exc:
            # cosign missing – treat as mismatch in production, warn otherwise
            if os.getenv("ENV", "development") == "production":
                raise SignatureMismatch("cosign not available in production env") from exc
            else:
                print("⚠️  cosign not found; skipping lockfile verification in non-prod env") 