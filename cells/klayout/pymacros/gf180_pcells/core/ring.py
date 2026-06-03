"""
Ring geometry node for rectangular frames.

Provides a `Ring` node that generates a rectangular frame composed of four
precisely tiled rectangles (top, bottom, left, right). Supports two primary
instantiation modes:
  1. Enclosure: Wraps an existing node's bounding box (optionally targeting a specific layer)
  2. Explicit: Uses inner/outer/center dimensions with a specified thickness

The node implements the full `Node` interface for predictable hierarchical layout,
packing, and feature querying.
"""

import pya as kdb
import typing
from typing import Union, Callable, Dict, Any, Optional

from .node import Node
from .rect import Rect


class Ring(Node):
    """
    A rectangular frame node composed of four precisely tiled segments.

    Generates a ring geometry on a specified layer with configurable thickness.
    Supports enclosure of child nodes or explicit dimension specification.
    Segment generation is fully pluggable via the `primitive` parameter.

    Args:
        enclose: Child node to enclose. Mutually exclusive with explicit w/h.
        enclose_pack: If True, targets the child's pack_box() boundary.
        enclose_feature: Feature name to target (default: "*" for all).
        enclose_layer: If set, targets this specific layer's bounding box.
                       Takes precedence over enclose_pack and enclose_feature.
        w, h: Explicit dimensions. Required if enclose is None.
        width: Ring thickness (uniform on all sides).
        mode: Dimension reference mode when w/h are explicit. One of:
              - "outer": w/h are outer dimensions
              - "inner": w/h are inner dimensions (outer = w/h + 2*width)
              - "center": w/h are centerline dimensions (outer = w/h + width)
        spacing: Virtual outward expansion applied to the enclosure before the ring
                 is drawn. Only active when enclose is provided. Adds to the inner
                 boundary on all sides (inner = enclosure + 2*spacing).
        primitive: Optional Node class or factory function to generate each segment.
                   If None, falls back to exact rectangular tiling.
                   Receives (w, h, layer, **primitive_kwargs) during instantiation.
        primitive_kwargs: Additional keyword arguments passed to the primitive.
        halo: Base halo applied to all sides for packing/clearance.
        halo_x, halo_y: Horizontal/vertical halo overrides.
        halo_l, halo_r, halo_b, halo_t: Directional halos.
        name: Feature identifier for feature_box() lookups.

    Note:
        - The four segments are tiled without corner overlaps for precise area/DRC.
        - Halos affect `pack_box()` but do not change drawn geometry.
        - Ring width cannot exceed half of the ring's outer dimensions.
        - `spacing` only applies when `enclose` is set. It has no effect on explicit w/h.
    """

    def __init__(self, enclose: Node = None, enclose_pack: bool = False,
                 enclose_feature: str = "*", enclose_layer: kdb.LayerInfo = None,
                 w: float = None, h: float = None, width: float = 0.0, mode: str = "outer",
                 spacing: float = 0.0,
                 primitive: Optional[Union[type, Callable]] = Rect,
                 primitive_kwargs: Optional[Dict[str, Any]] = None,
                 halo: float = 0.0, halo_x: float = 0.0, halo_y: float = 0.0,
                 halo_l: float = 0.0, halo_b: float = 0.0, halo_t: float = 0.0,
                 halo_r: float = 0.0, name: str = ""):
        print("IN RING")
        self.name = name
        self.width = width
        self.spacing = spacing
        self.primitive = primitive
        self.primitive_kwargs = primitive_kwargs or {}

        print("Primitive is "+str(primitive))

        # Aggregate halos
        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t

        # Resolve enclosure or explicit dimensions
        if enclose is not None:
            fb = self._resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer)
            # Spacing expands the inner boundary outward on all sides.
            # inner_dim = enclose_dim + 2*spacing
            # outer_dim = inner_dim + 2*width
            self.w_outer = fb.width() + 2 * spacing + 2 * width
            self.h_outer = fb.height() + 2 * spacing + 2 * width
            self.center = fb.center()
        else:
            if w is None or h is None:
                raise ValueError("Either 'enclose' or 'w'/'h' must be provided for Ring")

            if mode == "outer":
                self.w_outer, self.h_outer = w, h
            elif mode == "inner":
                self.w_outer, self.h_outer = w + 2 * width, h + 2 * width
            elif mode == "center":
                self.w_outer, self.h_outer = w + width, h + width
            else:
                raise ValueError(f"Invalid mode: {mode}. Use 'outer', 'inner', or 'center'.")
            self.center = kdb.DPoint(0, 0)

        # Validation: width cannot consume more than half the outer dimension
        if self.width > self.w_outer / 2 or self.width > self.h_outer / 2:
            raise ValueError(
                f"Ring width {self.width} exceeds half of outer dimensions "
                f"{self.w_outer}×{self.h_outer}. Ring cannot be drawn."
            )

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
        """Returns the absolute outer bounding box of the ring."""
        return kdb.DBox(
            self.center.x - self.w_outer / 2,
            self.center.y - self.h_outer / 2,
            self.center.x + self.w_outer / 2,
            self.center.y + self.h_outer / 2
        )

    def bounding_box_for_layer(self, layer) -> kdb.DBox:
        """Returns bounding box only if the queried layer matches this ring's layer."""
        if self.layer is not None and self.layer == layer:
            return self.bounding_box()
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
        """Inserts the four precisely tiled segments into the target cell."""
        if self.layer is None:
            print("Layer is none")
            return

        lindex = cell.layout().layer(self.layer)
        cx, cy = self.center.x, self.center.y
        w_out, h_out = self.w_outer, self.h_outer
        w_r = self.width

        # Pluggable primitive tiling
        # (seg_w, seg_h, dx_from_center, dy_from_center)
        segments = [
            (w_r, h_out, -w_out/2 + w_r/2, 0),          # left
            (w_r, h_out,  w_out/2 - w_r/2, 0),          # right
            (w_out - 2*w_r, w_r, 0, h_out/2 - w_r/2),   # top
            (w_out - 2*w_r, w_r, 0, -h_out/2 + w_r/2)   # bottom
        ]

        print("HELLO")
        for seg_w, seg_h, dx, dy in segments:
            # Prepare kwargs: primitive_kwargs + segment dimensions + target layer
            inst_kwargs = {**self.primitive_kwargs, "w": seg_w, "h": seg_h}

            # Instantiate the primitive (works for classes or factory callables)
            node = self.primitive(**inst_kwargs)

            # Apply segment offset relative to ring center, then global transform
            seg_trans = trans * kdb.DTrans(kdb.DVector(cx + dx, cy + dy))
            print("Calling produce on" +str(node))
            node.produce(cell, seg_trans)
