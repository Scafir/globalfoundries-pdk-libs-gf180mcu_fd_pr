"""
core/params.py

ParamSlot  — metadata describing one overridable value on a Node.
Override   — a resolved (path, value) pair to be dispatched into a tree.
Helpers    — collect_params(), flatten_paths(), dispatch_overrides().
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# ParamSlot
# ---------------------------------------------------------------------------

@dataclass
class ParamSlot:
    """Describes one overridable parameter that a Node exposes."""
    description: str
    default: Any
    type: type                      # float | int | bool | str
    unit: str = ""
    min_val: float | None = None
    max_val: float | None = None
    choices: list[tuple[str, Any]] | None = None   # [(label, value), ...]

    def coerce(self, raw: Any) -> Any:
        """Parse/validate a raw value (typically a string from the UI)."""
        value = self.type(raw)
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"Value {value} is below minimum {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Value {value} is above maximum {self.max_val}")
        if self.choices is not None:
            allowed = [v for _, v in self.choices]
            if value not in allowed:
                raise ValueError(f"Value {value!r} not in allowed choices {allowed}")
        return value


# ---------------------------------------------------------------------------
# Override
# ---------------------------------------------------------------------------

@dataclass
class Override:
    """One resolved override: a dot-separated path and its typed value."""
    path: str
    value: Any


# ---------------------------------------------------------------------------
# Registry type alias
# ---------------------------------------------------------------------------
#
# A nested dict produced by Node.collect_params():
#
#   {
#     "left_sub": {
#       "_slots": {"w": ParamSlot(...), "enc": ParamSlot(...)},
#       "_children": {
#         "contact": {
#           "_slots": {"size": ParamSlot(...)},
#           "_children": {}
#         }
#       }
#     }
#   }
#
Registry = dict  # str → {"_slots": dict[str, ParamSlot], "_children": Registry}


def empty_registry() -> Registry:
    return {"_slots": {}, "_children": {}}


# ---------------------------------------------------------------------------
# collect_params  (called on a Node, implemented here for reuse in tests)
# ---------------------------------------------------------------------------

def collect_params(node) -> Registry:
    """
    Walk a Node tree and return the nested Registry.
    Calls node.param_slots() and node._named_children() recursively.
    """
    reg = empty_registry()
    reg["_slots"] = dict(node.param_slots())
    for child_name, child_node in node._named_children():
        reg["_children"][child_name] = collect_params(child_node)
    return reg


# ---------------------------------------------------------------------------
# flatten_paths  — for populating a UI choice list
# ---------------------------------------------------------------------------

def flatten_paths(reg: Registry, prefix: str = "") -> list[tuple[str, ParamSlot]]:
    """
    Return a flat list of (dot_path, ParamSlot) for every slot in the tree.
    Used to build the dropdown of available override targets.
    """
    result = []
    for slot_name, slot in reg.get("_slots", {}).items():
        path = f"{prefix}.{slot_name}" if prefix else slot_name
        result.append((path, slot))
    for child_name, child_reg in reg.get("_children", {}).items():
        child_prefix = f"{prefix}.{child_name}" if prefix else child_name
        result.extend(flatten_paths(child_reg, prefix=child_prefix))
    return result


# ---------------------------------------------------------------------------
# lookup_slot  — resolve a dot-path to a ParamSlot
# ---------------------------------------------------------------------------

def lookup_slot(reg: Registry, path: str) -> ParamSlot:
    """
    Resolve "left_sub.contact.size" → the corresponding ParamSlot.
    Raises KeyError if the path does not exist.
    """
    head, _, tail = path.partition(".")
    if not tail:
        # Terminal: must be a slot at this level
        slots = reg.get("_slots", {})
        if head not in slots:
            raise KeyError(f"No slot {head!r} at this level. "
                           f"Available: {list(slots.keys())}")
        return slots[head]
    else:
        children = reg.get("_children", {})
        if head not in children:
            raise KeyError(f"No child {head!r} at this level. "
                           f"Available: {list(children.keys())}")
        return lookup_slot(children[head], tail)


# ---------------------------------------------------------------------------
# dispatch_overrides  — push Override list into a Node tree
# ---------------------------------------------------------------------------

def dispatch_overrides(node, overrides: list[Override]) -> None:
    """
    Walk the Override list and call apply_overrides() on the correct node
    for each entry.  Modifies the tree in-place; call before produce().
    """
    # Bucket by first path segment
    local: dict[str, Any] = {}
    forwarded: dict[str, list[Override]] = {}

    children = dict(node._named_children())

    for ov in overrides:
        head, _, tail = ov.path.partition(".")
        if not tail:
            local[head] = ov.value
        else:
            forwarded.setdefault(head, []).append(Override(path=tail, value=ov.value))

    if local:
        node.apply_overrides(local)

    for child_name, child_overrides in forwarded.items():
        if child_name not in children:
            raise KeyError(f"No child named {child_name!r} on {node!r}")
        dispatch_overrides(children[child_name], child_overrides)
