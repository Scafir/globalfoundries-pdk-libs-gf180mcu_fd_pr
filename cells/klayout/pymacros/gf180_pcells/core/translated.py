import pya as kdb

from .node import Node


class Translated(Node):
  """Wrapper that applies a fixed translation to a child node."""

  def __init__(self, child, trans):
    self.child = child
    self.trans = trans

  def bounding_box(self):
    return self.trans * self.child.bounding_box()

  def pack_box(self):
    return self.trans * self.child.pack_box()

  def feature_box(self, feature_name):
    return self.trans * self.child.feature_box(feature_name)

  def ref_point(self, name):
    return self.trans * self.child.ref_point(name)

  def produce(self, cell, trans):
    self.child.produce(cell, trans * self.trans)
