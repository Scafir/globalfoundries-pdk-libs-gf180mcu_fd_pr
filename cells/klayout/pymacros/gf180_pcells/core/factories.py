import typing

from .node import Node
from .rect import Rect
from .rect_fill import RectFill


RingSegmentFactory = typing.Callable[[float, float], Node]

def rect_segment(layer) -> RingSegmentFactory:
    """Factory: solid rectangle on a given layer."""
    def make(w, h):
        return Rect(layer=layer, w=w, h=h)
    return make


def rectfill_segment(**kwargs) -> RingSegmentFactory:
    """Factory: RectFill on a given layer."""
    def make(w, h):
        return RectFill(
            w=w, h=h,
            **kwargs
        )
    return make
