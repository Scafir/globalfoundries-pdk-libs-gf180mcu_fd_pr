import pya as kdb
import typing

from .node import Node

class Rect(Node):

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
        """Returns the reference box used for sizing, positioning, and packing."""
        if self.enclose is None:
            return kdb.DBox()

        if self.enclose_layer is not None:
            fb = self.enclose.bounding_box_for_layer(self.enclose_layer)
            if fb.empty():
                raise ValueError(f"Enclosed node has no geometry on layer {self.enclose_layer}")
            return fb
        elif self.enclose_pack:
            return self.enclose.pack_box()
        else:
            return self.enclose.feature_box(self.enclose_feature)

    def bounding_box(self) -> kdb.DBox:
        return self.etrans * kdb.DBox(
            -self.w/2 - self.enl_l, -self.h/2 - self.enl_b,
             self.w/2 + self.enl_r,  self.h/2 + self.enl_t
        )

    def bounding_box_for_layer(self, layer) -> kdb.DBox:
        if self.layer is not None and self.layer == layer:
            return self.bounding_box()
        return kdb.DBox()

    def feature_box(self, feature_name: str) -> kdb.DBox:
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        else:
            return kdb.DBox()

    def pack_box(self) -> kdb.DBox:
        # Consistently use the same enclosure reference box for packing
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
        if self.layer is not None:
            lindex = cell.layout().layer(self.layer)
            cell.shapes(lindex).insert(trans * self.bounding_box())
