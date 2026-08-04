"""
pcells/resistor_pcell.py

ResistorPCell: KLayout PCell wrapper for the diffusion resistor device.
"""
import pya as kdb

from ..devices.guard_ring import GuardRingParams, GuardRing


class GuardRingPCell(kdb.PCellDeclarationHelper):
    
  def __init__(self):
    super().__init__()
    self.param("h", self.TypeDouble, "Height", default=1.0, unit="um")
    self.param("w", self.TypeDouble, "Width", default=1.0, unit="um")

  def _model(self):
    v = self.model
    return v.value if hasattr(v, 'value') else v

  def display_text_impl(self):
    return "Guard Ring height:%.12g width:%.12g" % (self.h, self.w)

  def produce_impl(self):
    params = GuardRingParams(h = self.h, w = self.w)

    gen = GuardRing(p = params)
    gen.apply_overrides(overrides = {})
    gen.produce(self.cell, kdb.DTrans())
