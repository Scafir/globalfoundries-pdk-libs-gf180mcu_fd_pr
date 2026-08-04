import pya as kdb
import typing
from dataclasses import dataclass

from .node import Node
from .ring import Ring
from .params import ParamSlot
from .factories import RingSegmentFactory


@dataclass
class RingSpec:
    width: float
    factory: RingSegmentFactory


class GuardRingBase(Node):
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
                 name: str = ""):
        self.name = name
        self.ring_specs = ring_specs


        if enclose is not None:
            fb = self._resolve_enclose_box()
            self.w = max(w, fb.width())
            self.h = max(h, fb.height())
            self.etrans = kdb.DTrans(fb.center())
        else:
            self.w = w
            self.h = h
            self.etrans = kdb.DTrans()

    def param_slots(self):
        return {
            "h": ParamSlot(
                description="Height of guard ring",
                default=0,
                type=float, unit="um",
            ),
            "w": ParamSlot(
                description="Width of guard ring",
                default=0,
                type=float, unit="um",
            ),

        }

    def apply_overrides(self, overrides: dict):
        if "w" in overrides: self.w    = overrides["w"]
        if "h" in overrides: self.h = overrides["h"]
        self._build()

    def _build(self):
        # Find the widest segment for determining centerlines
        wmax = 0
        for s in self.ring_specs:
            if s.width > wmax:
                wmax = s.width

        # Build rings from inside out, accumulating dimensions
        self._rings: list[Ring] = []
        w_cur, h_cur = self.w - self.w/2, self.h - self.h/2  # tracks the shared centerline boundary
        
        for spec in self.ring_specs:
            self._rings.append(
                Ring(w=w_cur, h=h_cur, width=spec.width,
                     mode="center", segment_factory=spec.factory)
            )

    def _resolve_enclose_box(self) -> kdb.DBox:
        """
        Determine the reference box used for sizing, centering, and packing.

        Priority: enclose_layer > enclose_pack > enclose_feature

        Returns:
            kdb.DBox: Reference bounding box. Empty if enclose is None.

        Raises:
            ValueError: If enclose_layer is set but contains no geometry.
        """
        if self.enclose_layer is not None:
            fb = self.enclose.bounding_box_for_layer(self.enclose_layer)
            if fb.empty():
                raise ValueError(
                    f"Enclosed node has no geometry on layer {self.enclose_layer}. "
                    f"Consider using enclose_pack or enclose_feature instead."
                )
            return fb
        elif self.enclose_pack:
            return self.enclose.pack_box()
        else:
            return self.enclose.feature_box(self.enclose_feature)

    def bounding_box(self) -> kdb.DBox:
        cx, cy = self.etrans.x, self.etrans.y
        return self.etrans * kdb.DBox(-self.w / 2, -self.h/ 2,
                        self.w/ 2, self.h/ 2)

    def pack_box(self) -> kdb.DBox:
        bb = self.bounding_box()
        return kdb.DBox(bb.left - self.halo_l, bb.bottom - self.halo_b,
                        bb.right + self.halo_r, bb.top + self.halo_t)

    def feature_box(self, feature_name: str) -> kdb.DBox:
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        center_trans = trans * self.etrans
        for ring in self._rings:
            ring.produce(cell, center_trans)
