"""
Technology-agnostic via stack node with automatic planar enclosure resolution.
"""
import pya as kdb
from dataclasses import dataclass
from typing import Tuple, Dict, Set, Optional

from .node import Node
from .rect import Rect
from .rect_fill import RectFill


@dataclass(frozen=True)
class ViaStackTech:
    """
    Technology-specific via stack configuration.
    
    Args:
        conductors: Ordered tuple of conductor layers (bottom to top).
        vias: Ordered tuple of via layers. Must be len(conductors) - 1.
        via_rules: Mapping from via_layer -> RectFill kwargs.
        well_paths: Dict mapping path name -> tuple of planar layers (inner to outer).
        well_offsets: Mapping from planar layer -> enclosure amount (μm).
    """
    conductors: Tuple[kdb.LayerInfo, ...]
    vias: Tuple[kdb.LayerInfo, ...]
    via_rules: Dict[kdb.LayerInfo, dict]
    well_paths: Dict[str, Tuple[kdb.LayerInfo, ...]]
    well_offsets: Dict[kdb.LayerInfo, float]

    def __post_init__(self):
        if len(self.vias) != len(self.conductors) - 1:
            raise ValueError(f"vias must have {len(self.conductors) - 1} entries, got {len(self.vias)}")


class ViaStack(Node):
    """
    A rectangular via stack connecting two layers, with automatic planar enclosure resolution.
    
    If `from_layer` or `to_layer` belongs to a well path, concentric enclosures are 
    built automatically using `Rect(enclose=..., enl=...)`. No explicit flag required.
    """
    def __init__(self, w: float, h: float, from_layer: kdb.LayerInfo, to_layer: kdb.LayerInfo,
                 tech: ViaStackTech,
                 via_overrides: Optional[Dict[kdb.LayerInfo, dict]] = None,
                 halo: float = 0.0, halo_x: float = 0.0, halo_y: float = 0.0,
                 halo_l: float = 0.0, halo_r: float = 0.0,
                 halo_b: float = 0.0, halo_t: float = 0.0,
                 name: str = ""):

        self.w = w
        self.h = h
        self.name = name
        self.center = kdb.DPoint(0, 0)
        self.tech = tech

        # Aggregate halos
        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t

        # Resolve stack topology
        self._conductors, self._vias, self._well_path, self._children, self._all_layers = \
            self._resolve_stack(from_layer, to_layer, tech, via_overrides)

    def _resolve_stack(self, from_l, to_l, tech, via_overrides):
        """Auto-detect conductor range, well path, and instantiate children."""
        all_conductors = set(tech.conductors)
        all_wells = {l for path in tech.well_paths.values() for l in path}
        
        if from_l not in all_conductors.union(all_wells) or to_l not in all_conductors.union(all_wells):
            valid = ", ".join(str(l) for l in tech.conductors) + " or " + ", ".join(str(l) for l in all_wells)
            raise ValueError(f"from/to layers must be in: {valid}")

        # 1. Determine conductor range
        cond_indices = []
        for l in (from_l, to_l):
            if l in tech.conductors:
                cond_indices.append(tech.conductors.index(l))
                
        if not cond_indices:
            raise ValueError("At least one conductor layer (comp, metal, etc.) must be specified")
            
        start, end = min(cond_indices), max(cond_indices)
        conductors = tech.conductors[start:end+1]
        vias = tech.vias[start:end]

        # 2. Detect well path automatically
        active_well_path = None
        for l in (from_l, to_l):
            if l in all_wells:
                for name, path in tech.well_paths.items():
                    if l in path:
                        if active_well_path is not None and active_well_path != name:
                            raise ValueError("Cannot mix mutually exclusive well paths in a single stack")
                        active_well_path = name
                        break

        # If a well is requested, comp must be in the conductor range
        if active_well_path and tech.conductors[0] not in conductors:
            raise ValueError("Well/diffusion layers require comp layer to be included in the stack range")

        # 3. Build children
        children = []
        all_layers = set(conductors) | set(vias)

        # Conductors
        for layer in conductors:
            children.append(Rect(layer=layer, w=self.w, h=self.h))
            
        # Vias
        merged_rules = {**tech.via_rules}
        if via_overrides:
            for layer, ov in via_overrides.items():
                merged_rules[layer] = {**merged_rules.get(layer, {}), **ov}
                
        for via_layer in vias:
            children.append(RectFill(
                layer=via_layer, w=self.w, h=self.h, outer_layer=None, 
                **merged_rules.get(via_layer, {})
            ))
            all_layers.add(via_layer)

        # Auto-chained planar enclosures
        well_path = None
        if active_well_path:
            well_path = tech.well_paths[active_well_path]
            base_rect = children[0]  # First conductor is comp
            prev_rect = base_rect
            for layer in well_path:
                offset = tech.well_offsets.get(layer, 0.0)
                enc_rect = Rect(layer=layer, enclose=prev_rect, enl=offset)
                children.append(enc_rect)
                all_layers.add(layer)
                prev_rect = enc_rect

        return conductors, vias, well_path, children, all_layers

    # ------------------------------------------------------------------ #
    # Node Interface                                                     #
    # ------------------------------------------------------------------ #
    def bounding_box(self) -> kdb.DBox:
        box = kdb.DBox()
        for child in self._children:
            box += child.bounding_box()
        return box

    def bounding_box_for_layer(self, layer: kdb.LayerInfo) -> kdb.DBox:
        if layer in self._all_layers:
            return self.bounding_box()
        return kdb.DBox()

    def pack_box(self) -> kdb.DBox:
        bb = self.bounding_box()
        return kdb.DBox(
            bb.left - self.halo_l, bb.bottom - self.halo_b,
            bb.right + self.halo_r, bb.top + self.halo_t
        )

    def feature_box(self, feature_name: str) -> kdb.DBox:
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        for child in self._children:
            child.produce(cell, trans)
