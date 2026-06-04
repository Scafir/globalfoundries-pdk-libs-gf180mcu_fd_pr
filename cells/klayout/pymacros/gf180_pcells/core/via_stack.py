"""
Technology-agnostic via stack node with automatic planar enclosure resolution.
"""
import pya as kdb
from dataclasses import dataclass
from typing import List, Dict, Set, Optional

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
        doping: TODO
        doping_offsets: Mapping from planar layer -> enclosure amount (μm).
    """
    conductors: List[kdb.LayerInfo]
    vias: List[kdb.LayerInfo]
    via_rules: Dict[kdb.LayerInfo, dict]
    doping: List[kdb.LayerInfo]
    doping_offsets: Dict[kdb.LayerInfo, float]

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
                 tech: ViaStackTech, name: str = ""):

        self.w = w
        self.h = h
        self.name = name
        self.center = kdb.DPoint(0, 0)
        self.tech = tech

        # Resolve stack topology
        self._children = self._resolve_stack(from_layer, to_layer, tech)

    def _resolve_stack(self, from_l, to_l, tech):
        if from_l not in tech.conductors + tech.doping or to_l not in tech.conductors + tech.doping:
            valid = ", ".join(str(l) for l in tech.conductors + tech.doping)
            raise ValueError(f"from/to layers must be in: {valid}")

        # 1. Determine conductor range
        cond_indices = []
        doping = None
        for l in (from_l, to_l):
            if l in tech.conductors:
                cond_indices.append(tech.conductors.index(l))
            else:
                # Doping target: go as far down the stack as possible
                cond_indices.append(0)
                doping = l
                
        start, end = min(cond_indices), max(cond_indices)
        conductors = tech.conductors[start:end+1]
        vias = tech.vias[start:end]

        # 3. Build children
        children = []

        # Conductors
        for layer in conductors:
            children.append(Rect(layer=layer, w=self.w, h=self.h))
                
        for via_layer in vias:
            children.append(RectFill(
                layer=via_layer, w=self.w, h=self.h, outer_layer=None, **tech.via_rules[via_layer]
            ))
        
        if doping:
            children.append(Rect(layer=doping, enclose=children[0], enl=tech.doping_offsets.get(doping)))

        return children

    # ------------------------------------------------------------------ #
    # Node Interface                                                     #
    # ------------------------------------------------------------------ #
    def bounding_box(self) -> kdb.DBox:
        box = kdb.DBox()
        for child in self._children:
            box += child.bounding_box()
        return box

    def bounding_box_for_layer(self, layer: kdb.LayerInfo) -> kdb.DBox:
        box = kdb.DBox()
        for i in range(len(self.children)):
          box += self.children[i].bounding_box_for_layer(layer)

        return box

    def pack_box(self) -> kdb.DBox:
        bb = self.bounding_box()
        return kdb.DBox(
            bb.left, bb.bottom,
            bb.right, bb.top
        )

    def feature_box(self, feature_name: str) -> kdb.DBox:
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        for child in self._children:
            child.produce(cell, trans)
