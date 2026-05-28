import pya as kdb

from ..devices.resistor import res_models, make_resistor, is_metal
from ..tech.gf180_rules import Rules

class ResistorPCell(kdb.PCellDeclarationHelper):

  def __init__(self):
    super().__init__()

    choices = [(s, s) for s in res_models]

    self.param("_version", self.TypeInt, "Version", hidden=True, default=0)
    self.param("model", self.TypeInt, "Resistor Model", choices=choices, default=res_models[0])
    self.param("l", self.TypeDouble, "Length", default=1.0, unit="um")
    self.param("w", self.TypeDouble, "Width", default=1.0, unit="um")
    self.param("contacts", self.TypeInt, "End Contacts (0=none, 1+with vias)", default=0)

  def coerce_parameters_impl(self):
    m = self.model
    if m == "rm1":
      self.l = max(Rules.rm1_l, self.l)
      self.w = max(Rules.rm1_w, self.w)
    elif m in ("rm2", "rm3"):
      self.l = max(Rules.rm2_l, self.l)
      self.w = max(Rules.rm2_w, self.w)
    elif m == "tm6k":
      self.l = max(Rules.tm6k_l, self.l)
      self.w = max(Rules.tm6k_w, self.w)
      if self.l * self.w < 0.563:
        self.l = round(0.563 / self.w, 2)
    elif m in ("tm9k", "tm11k"):
      self.l = max(Rules.tm9k_l, self.l)
      self.w = max(Rules.tm9k_w, self.w)
      if self.l * self.w < 0.563:
        self.l = round(0.563 / self.w, 2)
    elif m == "tm30k":
      self.l = max(Rules.tm30k_l, self.l)
      self.w = max(Rules.tm30k_w, self.w)
    elif m == "ppolyf_u_h":
      self.l = max(1.0, self.l)
      self.w = max(1.0, self.w)
    else:
      self.l = max(0.42, self.l)
      self.w = max(0.42, self.w)

  def display_text_impl(self):
    return "Resistor %s l:%.12g w:%.12g" % (self.model, self.l, self.w)

  def produce_impl(self):
    gen = make_resistor(model=self.model, l=self.l, w=self.w, contacts=self.contacts)
    gen.produce(self.cell, kdb.DTrans())
