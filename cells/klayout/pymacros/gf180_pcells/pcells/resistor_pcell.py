import pya as kdb

from ..devices.resistor import res_models, make_resistor, is_metal, is_diffusion, is_poly
from ..tech.gf180_rules import Rules

class ResistorPCell(kdb.PCellDeclarationHelper):

  def __init__(self):
    super().__init__()

    choices = [(s, s) for s in res_models]
    side_choices = [("left", 0), ("right", 1), ("both", 2)]

    self.param("_version", self.TypeInt, "Version", hidden=True, default=1)
    self.param("model", self.TypeInt, "Resistor Model", choices=choices, default=res_models[0])
    self.param("l", self.TypeDouble, "Length", default=1.0, unit="um")
    self.param("w", self.TypeDouble, "Width", default=1.0, unit="um")
    self.param("with_contacts", self.TypeBoolean, "Terminal contacts", default=True)
    self.param("with_substrate", self.TypeBoolean, "Substrate tap", default=True)
    self.param("substrate_side", self.TypeInt, "Substrate side", choices=side_choices, default=0)
    self.param("guard_ring", self.TypeBoolean, "Guard ring", default=False)
    self.param("with_dnwell", self.TypeBoolean, "Deep NWell", default=False)
    self.param("n_center_contacts", self.TypeInt, "Center contacts", default=0)

  def _model(self):
    v = self.model
    return v.value if hasattr(v, 'value') else v

  def callback_impl(self, name):
    m = self._model()

    # Metal: hide all advanced options
    if is_metal(m):
      self.with_contacts.visible = False
      self.with_substrate.visible = False
      self.substrate_side.visible = False
      self.guard_ring.visible = False
      self.with_dnwell.visible = False
      self.n_center_contacts.visible = False
      return

    # Substrate side only visible when substrate is enabled
    self.substrate_side.visible = self.with_substrate.value

    # Center contacts: diffusion, poly, ppolyf_u_h
    self.n_center_contacts.visible = is_diffusion(m) or is_poly(m) or m == "ppolyf_u_h"

    # DNWELL: only n-type diffusion and n-type poly and nwell
    n_diff = is_diffusion(m) and m.startswith("n")
    n_poly = is_poly(m) and m.startswith("n")
    self.with_dnwell.visible = n_diff or n_poly or m == "nwell"

    # Guard ring: diffusion, poly, ppolyf_u_h, well
    self.guard_ring.visible = is_diffusion(m) or is_poly(m) or m in ("ppolyf_u_h", "nwell", "pwell")

    # Contacts and substrate: visible for all non-metal
    self.with_contacts.visible = True
    self.with_substrate.visible = True

  def coerce_parameters_impl(self):
    m = self._model()
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

    self.n_center_contacts = max(0, self.n_center_contacts)

  def display_text_impl(self):
    return "Resistor %s l:%.12g w:%.12g" % (self._model(), self.l, self.w)

  def produce_impl(self):
    gen = make_resistor(
        model=self._model(),
        l=self.l,
        w=self.w,
        with_contacts=self.with_contacts,
        with_substrate=self.with_substrate,
        substrate_side=["left", "right", "both"][self.substrate_side],
        guard_ring=self.guard_ring,
        with_dnwell=self.with_dnwell,
        n_center_contacts=self.n_center_contacts,
    )
    gen.produce(self.cell, kdb.DTrans())
