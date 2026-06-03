import pya as kdb
import typing
from dataclasses import dataclass

from .node import Node
from .ring import Ring
from .factories import RingSegmentFactory


@dataclass
class RingSpec:
    width: float
    factory: RingSegmentFactory


class GuardRing(Node):
    """
    A concentric guard ring composed of an arbitrary stack of ring layers.

    Each layer is described by a RingSpec: a ring width and a factory
    callable (w, h) -> Node that produces the segment geometry.
    Rings are ordered inside-out: the first spec is innermost.

    Args:
        ring_specs: Ordered list of RingSpec objects, inside-out.
        enclose / w / h: Base boundary (same semantics as before).
        spacing: Outward expansion before ring widths are added.
        halo, halo_*: Packing clearances.
        name: Feature identifier.
    """

    def __init__(self, ring_specs: list[RingSpec],
                 enclose: Node = None, enclose_pack: bool = False,
                 enclose_feature: str = "*", enclose_layer=None,
                 w: float = None, h: float = None,
                 spacing: float = 0.0,
                 halo: float = 0.0, halo_x: float = 0.0, halo_y: float = 0.0,
                 halo_l: float = 0.0, halo_r: float = 0.0,
                 halo_b: float = 0.0, halo_t: float = 0.0,
                 name: str = ""):

        self.name = name
        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t

        # Resolve base dimensions
        if enclose is not None:
            fb = self._resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer)
            self.center = fb.center()
            w_base = fb.width() + 2 * spacing
            h_base = fb.height() + 2 * spacing
        else:
            if w is None or h is None:
                raise ValueError("Either 'enclose' or 'w'/'h' must be provided")
            self.center = kdb.DPoint(0, 0)
            w_base = w
            h_base = h

        # Find the widest segment for determining centerlines
        wmax = 0
        for s in ring_specs:
            if s.width > wmax:
                wmax = w

        # Build rings from inside out, accumulating dimensions
        self._rings: list[Ring] = []
        w_cur, h_cur = w_base - w/2, h_base - w/2  # tracks the shared centerline boundary
        
        for spec in ring_specs:
            self._rings.append(
                Ring(w=w_cur, h=h_cur, width=spec.width,
                     mode="center", segment_factory=spec.factory)
            )
        
        self.w_total = w_base
        self.h_total = h_base

    def bounding_box(self) -> kdb.DBox:
        cx, cy = self.center.x, self.center.y
        return kdb.DBox(cx - self.w_total / 2, cy - self.h_total / 2,
                        cx + self.w_total / 2, cy + self.h_total / 2)

    def pack_box(self) -> kdb.DBox:
        bb = self.bounding_box()
        return kdb.DBox(bb.left - self.halo_l, bb.bottom - self.halo_b,
                        bb.right + self.halo_r, bb.top + self.halo_t)

    def feature_box(self, feature_name: str) -> kdb.DBox:
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        center_trans = trans * kdb.DTrans(self.center)
        for ring in self._rings:
            ring.produce(cell, center_trans)
