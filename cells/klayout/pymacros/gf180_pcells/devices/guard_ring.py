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

from ..core.node import Node
from ..core.ring import Ring

from ..tech.gf180_layers import Layers


class GuardRing(Node):
    """
    A multi-layer concentric guard ring composed of comp, metal1, and pplus rings.
    
    Generates three precisely aligned rings sharing the same center. Supports 
    enclosure of child nodes or explicit base dimensions. All rings expand 
    outward from a common base box by their respective fixed widths.
    
    Args:
        enclose: Child node to enclose. Mutually exclusive with explicit w/h.
        enclose_pack: If True, targets the child's pack_box() boundary.
        enclose_feature: Feature name to target (default: "*" for all).
        enclose_layer: If set, targets this specific layer's bounding box.
                       Takes precedence over enclose_pack and enclose_feature.
        w, h: Explicit base dimensions (before ring widths are added). Required 
              if enclose is None.
        spacing: Outward expansion applied to the base box before ring widths 
                 are added. Adds to inner boundary on all sides.
        halo: Base halo applied to all sides for packing/clearance.
        halo_x, halo_y: Horizontal/vertical halo overrides.
        halo_l, halo_r, halo_b, halo_t: Directional halos.
        name: Feature identifier for feature_box() lookups.
        
    Layer Configuration (Fixed):
        - Layers.comp:   width = 0.36 µm
        - Layers.metal1: width = 0.36 µm (identical to comp)
        - Layers.pplus:  width = 0.63 µm
        
    Note:
        - All rings are concentric (share the same center point).
        - `spacing` only applies when `enclose` is set.
        - Halos affect `pack_box()` but do not change drawn geometry.
        - w/h represent the "core" dimensions. Ring widths are added outward.
    """

    # Fixed design rule widths
    _WIDTH_COMP = 0.36
    _WIDTH_PPPLUS = 0.63

    def __init__(self, enclose: Node = None, enclose_pack: bool = False,
                 enclose_feature: str = "*", enclose_layer: kdb.LayerInfo = None,
                 w: float = None, h: float = None, spacing: float = 0.0,
                 halo: float = 0.0, halo_x: float = 0.0, halo_y: float = 0.0,
                 halo_l: float = 0.0, halo_b: float = 0.0, halo_t: float = 0.0,
                 halo_r: float = 0.0, name: str = ""):

        self.name = name
        
        # Aggregate halos
        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t

        # Resolve base enclosure or explicit dimensions
        if enclose is not None:
            fb = self._resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer)
            self.center = fb.center()
            self.w_base = fb.width()
            self.h_base = fb.height()
        else:
            if w is None or h is None:
                raise ValueError("Either 'enclose' or 'w'/'h' must be provided for GuardRing")
            self.center = kdb.DPoint(0, 0)
            self.w_base = w
            self.h_base = h

        # Apply spacing to base dimensions
        self.w_base += 2 * spacing
        self.h_base += 2 * spacing

        # Compute outer dimensions for each layer group
        self.w_pplus = self.w_base + 2 * self._WIDTH_PPPLUS
        self.h_pplus = self.h_base + 2 * self._WIDTH_PPPLUS

        width_diff = self._WIDTH_PPPLUS - self._WIDTH_COMP  # 0.27
        self.w_comp = self.w_pplus - width_diff
        self.h_comp = self.h_pplus - width_diff

        # Validate ring dimensions
        if self.w_base <= 0 or self.h_base <= 0:
            raise ValueError("Base dimensions must be positive after spacing is applied")

        # Pre-instantiate internal rings (centered at origin for predictable math)

        self._ring_comp = Ring(
            w=self.w_comp, h=self.h_comp, width=self._WIDTH_COMP, mode="outer",
            layer=Layers.comp)
        
        self._ring_metal1 = Ring(
            w=self.w_comp, h=self.h_comp, width=self._WIDTH_COMP, mode="outer",
            layer=Layers.metal1)
        
        self._ring_pplus = Ring(
            w=self.w_pplus, h=self.h_pplus, width=self._WIDTH_PPPLUS, mode="outer",
            layer=Layers.pplus)
        

    @staticmethod
    def _resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer) -> kdb.DBox:
        """Determine the reference box used for enclosure targeting."""
        if enclose_layer is not None:
            fb = enclose.bounding_box_for_layer(enclose_layer)
            if fb.empty():
                raise ValueError(f"Enclosed node has no geometry on layer {enclose_layer}")
            return fb
        elif enclose_pack:
            return enclose.pack_box()
        else:
            return enclose.feature_box(enclose_feature)

    def bounding_box(self) -> kdb.DBox:
        """Returns the absolute outer bounding box (determined by the largest ring)."""
        cx, cy = self.center.x, self.center.y
        return kdb.DBox(
            cx - self.w_pplus / 2, cy - self.h_pplus / 2,
            cx + self.w_pplus / 2, cy + self.h_pplus / 2
        )

    def bounding_box_for_layer(self, layer) -> kdb.DBox:
        """Returns bounding box only if the queried layer matches one of the ring layers."""
        cx, cy = self.center.x, self.center.y
        try:
            from . import layers as Layers
            if layer == Layers.comp or layer == Layers.metal1:
                return kdb.DBox(cx - self.w_comp / 2, cy - self.h_comp / 2,
                                cx + self.w_comp / 2, cy + self.h_comp / 2)
            elif layer == Layers.pplus:
                return self.bounding_box()
        except ImportError:
            pass
        return kdb.DBox()

    def feature_box(self, feature_name: str) -> kdb.DBox:
        """Returns bounding box for wildcard '*' or matching feature name."""
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def pack_box(self) -> kdb.DBox:
        """Returns the packing boundary including halos. Used by layout managers."""
        bb = self.bounding_box()
        return kdb.DBox(
            bb.left - self.halo_l, bb.bottom - self.halo_b,
            bb.right + self.halo_r, bb.top + self.halo_t
        )

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        """Inserts all three concentric rings into the target cell."""
        # Shift the origin-centered internal rings to the computed center
        center_trans = trans * kdb.DTrans(self.center)
        self._ring_comp.produce(cell, center_trans)
        self._ring_metal1.produce(cell, center_trans)
        self._ring_pplus.produce(cell, center_trans)
