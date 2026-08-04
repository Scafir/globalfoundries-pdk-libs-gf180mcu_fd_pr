import pya as kdb
import typing
from typing import Any

class Node:

  ref_points = {
    "C":  ( 0,  0  ),
    "E":  ( 1, 0  ),
    "NE": ( 1, 1  ),
    "SE": ( 1, -1 ),
    "W":  ( -1,  0  ),
    "NW": ( -1,  1 ),
    "SW": ( -1,  -1 ),
    "S":  ( 0,  -1 ),
    "N":  ( 0,  1  )
  }

  def __init__(self):
    pass

  def param_slots(self) -> dict:
      """Advertise overridable parameters at this node level."""
      return {}

  def _named_children(self) -> list[tuple[str, "Node"]]:
      """Return (name, child_node) pairs for tree walking."""
      return []

  def apply_overrides(self, overrides: dict[str, Any]) -> None:
      """Receive local-name → value dict and mutate accordingly."""
      pass


  def bounding_box(self) -> kdb.DBox:
    return kdb.DBox()
  
  def bounding_box_for_layer(self, layer) -> kdb.DBox:
    """Compute bounding box for a specific layer across the node tree."""
    return kdb.DBox()

  def pack_box(self) -> kdb.DBox:
    return kdb.DBox()

  def feature_box(self, feature_name: str) -> kdb.DBox:
    return kdb.DBox()

  def ref_point(self, name) -> kdb.DPoint:
    jx, jy = Node.ref_points[name]
    b = self.pack_box()
    return b.p1 + kdb.DVector(b.width() * (jx * 0.5 + 0.5), b.height() * (jy * 0.5 + 0.5))

  def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
    pass
