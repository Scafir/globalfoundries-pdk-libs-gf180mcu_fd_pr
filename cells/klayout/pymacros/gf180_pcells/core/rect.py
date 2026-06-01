"""
Rectangular geometry node with flexible enclosure targeting.

Provides a `Rect` node that generates rectangular shapes on a specific KLayout layer.
It supports optional enclosure of child nodes with three orthogonal targeting modes:
  - By layer (`enclose_layer`)
  - By pack boundary (`enclose_pack`)
  - By named feature (`enclose_feature`)

The node also supports asymmetric halos (for layout clearance/padding) and
enlargements (for explicit geometry overrides or guard bands).
"""

import pya as kdb
import typing

from .node import Node

class Rect(Node):
    """
    A rectangular geometry node that optionally encloses another node.

    The rectangle can be sized explicitly or derived from an enclosed node's
    reference box. It supports asymmetric halos for layout managers and
    enlargements for actual geometry generation.

    Args:
        layer: Target KLayout layer for output geometry.
        enclose: Child node to enclose. If provided, determines center and base size.
        enclose_layer: If set, enclosure targets this specific layer's bounding box.
                       Takes precedence over enclose_pack and enclose_feature.
        enclose_pack: If True, enclosure targets the child's pack_box() boundary.
        enclose_feature: Feature name to target for enclosure (default: "*" for all).
                         Used when enclose_layer is None and enclose_pack is False.
        name: Feature identifier used by feature_box() lookups.
        w, h: Explicit width/height. If larger than enclosure, overrides it.
        halo: Base halo applied to all sides (added to directional halos).
        halo_x, halo_y: Horizontal/vertical halo overrides.
        halo_l, halo_r, halo_b, halo_t: Directional halos (left, right, bottom, top).
        enl: Base enlargement applied to all sides (added to directional enlargements).
        enl_x, enl_y: Horizontal/vertical enlargement overrides.
        enl_l, enl_r, enl_b, enl_t: Directional enlargements relative to center.

    Note:
        - Halos affect `pack_box()` and are used by parent layout managers for
          spacing/clearance. They do NOT affect drawn geometry.
        - Enlargements affect `bounding_box()` and determine the actual inserted shape.
        - When `enclose` is None, directional enlargements default to reconstruct
          the explicit w/h dimensions. When `enclose` is set, they default to 0.
    """

    def __init__(self, layer: kdb.LayerInfo=None,
                         enclose: Node=None,
                         enclose_pack: bool=False,
                         enclose_feature: str="*",
                         enclose_layer: kdb.LayerInfo=None,
                         name: str="",
                         w: float=0.0, h: float=0.0,
                         halo: float=0.0, halo_x: float=0.0, halo_y: float=0.0,
                         halo_l: float=0.0, halo_b: float=0.0, halo_t: float=0.0, halo_r: float=0.0,
                         enl: float=0.0, enl_x: float=0.0, enl_y: float=0.0,
                         enl_l: float=0.0, enl_b: float=0.0, enl_t: float=0.0, enl_r: float=0.0):

        self.enclose = enclose
        self.enclose_layer = enclose_layer
        self.enclose_pack = enclose_pack
        self.enclose_feature = enclose_feature
        self.name = name
        self.layer = layer

        if enclose is not None:
            fb = self._resolve_enclose_box()
            self.w = max(w, fb.width())
            self.h = max(h, fb.height())
            self.etrans = kdb.DTrans(fb.center())
        else:
            self.w = w
            self.h = h
            self.etrans = kdb.DTrans()

        if enl_b is None:
            enl_b = 0.0 if enclose is not None else -self.h
        if enl_t is None:
            enl_t = 0.0 if enclose is not None else -self.h
        if enl_l is None:
            enl_l = 0.0 if enclose is not None else -self.w
        if enl_r is None:
            enl_r = 0.0 if enclose is not None else -self.w

        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t
        self.enl_l = enl + enl_x + enl_l
        self.enl_r = enl + enl_x + enl_r
        self.enl_b = enl + enl_y + enl_b
        self.enl_t = enl + enl_y + enl_t

    def _resolve_enclose_box(self) -> kdb.DBox:
        """
        Determine the reference box used for sizing, centering, and packing.

        Priority: enclose_layer > enclose_pack > enclose_feature

        Returns:
            kdb.DBox: Reference bounding box. Empty if enclose is None.

        Raises:
            ValueError: If enclose_layer is set but contains no geometry.
        """
        if self.enclose is None:
            return kdb.DBox()

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
        """
        Returns the absolute bounding box including enlargements.

        Used for geometry generation and layer-specific queries.

        Returns:
            kdb.DBox: Absolute bounding box in the node's local coordinate system.
        """
        return self.etrans * kdb.DBox(
            -self.w/2 - self.enl_l, -self.h/2 - self.enl_b,
             self.w/2 + self.enl_r,  self.h/2 + self.enl_t
        )

    def bounding_box_for_layer(self, layer) -> kdb.DBox:
        """
        Returns bounding box only if the queried layer matches this node's layer.

        Args:
            layer: KLayout layer to query.

        Returns:
            kdb.DBox: Bounding box if layer matches, else empty box.
        """
        if self.layer is not None and self.layer == layer:
            return self.bounding_box()
        return kdb.DBox()

    def feature_box(self, feature_name: str) -> kdb.DBox:
        """
        Returns bounding box for wildcard "*" or matching feature name.

        Args:
            feature_name: Feature identifier to query.

        Returns:
            kdb.DBox: Bounding box if name matches or is "*", else empty box.
        """
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        else:
            return kdb.DBox()

    def pack_box(self) -> kdb.DBox:
        """
        Returns the packing boundary including halos.

        Used by parent layout managers (Linear, Array, etc.) to determine
        spacing and alignment. Does not include enlargements.

        Returns:
            kdb.DBox: Packing boundary in local coordinates.
        """
        if self.enclose is not None:
            fb = self._resolve_enclose_box()
            return kdb.DBox(fb.left - self.halo_l, fb.bottom - self.halo_b,
                            fb.right + self.halo_r, fb.top + self.halo_t)
        else:
            return kdb.DBox(
                -self.w/2 - self.halo_l, -self.h/2 - self.halo_b,
                 self.w/2 + self.halo_r,  self.h/2 + self.halo_t
            )

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        """
        Inserts the rectangle geometry into a KLayout cell.

        Args:
            cell: Target KLayout cell.
            trans: Transformation to apply during insertion.
        """
        if self.layer is not None:
            lindex = cell.layout().layer(self.layer)
            cell.shapes(lindex).insert(trans * self.bounding_box())
