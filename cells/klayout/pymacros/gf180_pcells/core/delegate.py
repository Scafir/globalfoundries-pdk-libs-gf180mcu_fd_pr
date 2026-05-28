import pya as kdb
import typing

from .node import Node

class Delegate(Node):

  def __init__(self, child):
    self.child = child

  def bounding_box(self) -> kdb.DBox:
    return self.child.bounding_box()

  def pack_box(self) -> kdb.DBox:
    return self.child.pack_box()

  def feature_box(self, feature_name: str) -> kdb.DBox:
    return self.child.feature_box(feature_name)

  def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
    return self.child.produce(cell, trans)
