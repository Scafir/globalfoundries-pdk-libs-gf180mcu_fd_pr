"""
GuardRing geometry node for multi-layer concentric frames.

Provides a `GuardRing` node that generates three precisely aligned rings on 
`Layers.comp`, `Layers.metal1`, and `Layers.pplus`. All rings share the same 
center point and scale outward from a base enclosure or explicit dimensions.

Designed to integrate seamlessly with the `Node` hierarchy, supporting layout 
managers, packing queries, and feature lookups.
"""

import pya as kdb
import typing

from ..core.ring import Ring
from ..core.guard_ring import GuardRing, RingSpec
from ..core.factories import rect_segment, rectfill_segment

from ..tech.gf180_layers import Layers

_GF180_RING_SPECS = [
    RingSpec(0.36, rect_segment(Layers.comp)),
    RingSpec(0.36, rectfill_segment(
        layer=Layers.contact,
        outer_layer=Layers.metal1,
        cell_w=0.26, cell_h=0.26,
        spacing=0.26,
        edge_clearance=0.01,
        long_edge_extra_clearance=0.24,
        array_rule_limit=4,
        array_spacing=0.36,
    )),
    RingSpec(0.63, rect_segment(Layers.pplus)),
]

class GuardRing(GuardRing):
    def __init__(self, **kwargs):
        super().__init__(ring_specs=_GF180_RING_SPECS, **kwargs)
