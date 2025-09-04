"""Typed IR Builder

Converts a validated blueprint (dictionary or ParsedSystemBlueprint) into the
canonical typed Intermediate Representation (IR) described in
`docs/architecture/blueprint-language.md`.

This helper is **experimental** (Phase 0.5) and is gated by the feature flag
`EMIT_TYPED_IR`.

The output conforms to `schemas/typed_ir_v0_3.schema.json` and is designed to
be forward-compatible. Only the minimal required fields are emitted for now.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

try:
    # Optional import – only available inside the blueprint_language package
    from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint  # type: ignore
    from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedBinding, ParsedComponent  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – during isolated unit tests
    ParsedSystemBlueprint = object  # type: ignore
    ParsedBinding = object  # type: ignore
    ParsedComponent = object  # type: ignore

__all__ = ["build_ir"]

IR_VERSION = "0.3"


def _component_to_ir(comp: Any) -> Dict[str, Any]:
    """Convert a ParsedComponent or plain dict into IR format."""
    if is_dataclass(comp):
        comp_dict = asdict(comp)
    else:
        comp_dict = comp  # Assume already dict-like

    return {
        "name": comp_dict["name"],
        "type": comp_dict.get("type", comp_dict.get("implementation", "Unknown")),
        "implementation": comp_dict.get("implementation", comp_dict.get("type")),
        # Preserve arbitrary extra keys under `config` if present.
        "config": comp_dict.get("config", {}),
    }


def _binding_to_ir(binding: Any) -> Dict[str, Any]:
    """Convert a ParsedBinding or plain dict into IR format."""
    if is_dataclass(binding):
        binding_dict = asdict(binding)
        from_comp = binding_dict["from_component"]
        from_port = binding_dict["from_port"]
        to_components = binding_dict.get("to_components", [])
        to_ports = binding_dict.get("to_ports", [])
    else:
        binding_dict = binding
        from_comp = binding_dict.get("from")
        from_port = binding_dict.get("on") or binding_dict.get("stream")
        to_components = [binding_dict.get("to")] if binding_dict.get("to") else []
        to_ports = [binding_dict.get("as")] if binding_dict.get("as") else []

    targets: List[Dict[str, str]] = []
    for tgt_comp, tgt_port in zip(to_components, to_ports):
        targets.append({"component": tgt_comp, "port": tgt_port})

    return {
        "source": {"component": from_comp, "port": from_port},
        "targets": targets,
    }


def build_ir(blueprint: Union[Dict[str, Any], "ParsedSystemBlueprint"]) -> Dict[str, Any]:
    """Build the typed IR dictionary for *blueprint*.

    Parameters
    ----------
    blueprint:
        Either a *dict* representation of the system blueprint or an instance of
        `ParsedSystemBlueprint`.

    Returns
    -------
    Dict[str, Any]
        A dictionary conforming to `typed_ir_v0_3.schema.json`.
    """
    # Determine blueprint format
    if hasattr(blueprint, "system"):
        # ParsedSystemBlueprint path
        system_obj = blueprint.system  # type: ignore[attr-defined]
        system_meta = {
            "name": system_obj.name,
            "namespace": getattr(blueprint, "metadata", {}).get("namespace", ""),
            "version": system_obj.version,
        }

        components_ir = [_component_to_ir(c) for c in system_obj.components]
        bindings_ir = [_binding_to_ir(b) for b in system_obj.bindings]
        schemas_ir = getattr(blueprint, "schemas", {})
        capabilities_ir = {}  # Future enhancement – derive from components
    else:
        # Dictionary-based path
        sys_dict = blueprint.get("system", {})
        system_meta = {
            "name": sys_dict.get("name"),
            "namespace": sys_dict.get("namespace", ""),
            "version": sys_dict.get("version", "1.0.0"),
        }
        components_ir = [_component_to_ir(c) for c in sys_dict.get("components", [])]
        bindings_ir = [_binding_to_ir(b) for b in sys_dict.get("bindings", [])]
        schemas_ir = blueprint.get("schemas", {})
        capabilities_ir = blueprint.get("capabilities", {})

    ir: Dict[str, Any] = {
        "ir_version": IR_VERSION,
        "system": system_meta,
        "components": components_ir,
        "bindings": bindings_ir,
        "schemas": schemas_ir,
        "capabilities": capabilities_ir,
    }

    return ir 