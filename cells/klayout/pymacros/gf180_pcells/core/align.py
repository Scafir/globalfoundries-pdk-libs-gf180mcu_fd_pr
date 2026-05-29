import pya as kdb
from .node import Node

class LayerAlign(Node):
    """Makes alignment/reference points use a specific layer's bounding box."""
    def __init__(self, child: Node, layer):
        self.child = child
        self.layer = layer

    def bounding_box(self) -> kdb.DBox:
        return self.child.bounding_box()
    
    def bounding_box_for_layer(self, l) -> kdb.DBox:
        return self.child.bounding_box_for_layer(l)
    
    def feature_box(self, f: str) -> kdb.DBox:
        return self.child.feature_box(f)
    
    def pack_box(self) -> kdb.DBox:
        bbox = self.child.bounding_box_for_layer(self.layer)
        # Fallback to full pack box if layer is missing
        if bbox.empty():
            raise ValueError("Trying to LayerAlign on an empty layer")

        return bbox
    
    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        self.child.produce(cell, trans)


class RefShift(Node):
    """Shifts reference points by (dx, dy) without moving geometry. 
       Perfect for spacing/offsets between alignment points."""
    def __init__(self, child: Node, dx: float = 0.0, dy: float = 0.0):
        self.child = child
        self.shift = kdb.DVector(dx, dy)

    def ref_point(self, name: str) -> kdb.DPoint:
        return self.child.ref_point(name) + self.shift
    
    def bounding_box(self) -> kdb.DBox:
        return self.child.bounding_box()
    
    def bounding_box_for_layer(self, l) -> kdb.DBox:
        return self.child.bounding_box_for_layer(l)
    
    def feature_box(self, f: str) -> kdb.DBox:
        return self.child.feature_box(f)
    
    def pack_box(self) -> kdb.DBox:
        return self.child.pack_box()
    
    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        self.child.produce(cell, trans)
