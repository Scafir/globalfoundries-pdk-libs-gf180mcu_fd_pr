import pya as kdb

from ..tech.gf180_layers import Layers
from ..tech.gf180_rules import Rules
from ..core.node import Node
from ..core.rect import Rect
from ..core.linear import Linear
from ..core.justify import Justify
from ..core.translated import Translated

# ====================================================================
# Model catalog
# ====================================================================

res_models = [
  "rm1", "rm2", "rm3", "tm6k", "tm9k", "tm11k", "tm30k",
  "nplus_s", "pplus_s", "nplus_u", "pplus_u",
  "nwell", "pwell",
  "npolyf_s", "ppolyf_s", "npolyf_u", "ppolyf_u", "ppolyf_u_h",
]

resistor_type_map = {
  "rm1":       ("metal", Layers.metal1, Layers.metal1_res),
  "rm2":       ("metal", Layers.metal2, Layers.metal2_res),
  "rm3":       ("metal", Layers.metal3, Layers.metal3_res),
  "tm6k":      ("metal", Layers.metaltop, Layers.metaltop_res),
  "tm9k":      ("metal", Layers.metaltop, Layers.metaltop_res),
  "tm11k":     ("metal", Layers.metaltop, Layers.metaltop_res),
  "tm30k":     ("metal", Layers.metaltop, Layers.metaltop_res),
  "nplus_s":   ("diffusion", Layers.comp, Layers.res_mk),
  "pplus_s":   ("diffusion", Layers.comp, Layers.res_mk),
  "nplus_u":   ("diffusion", Layers.comp, Layers.res_mk),
  "pplus_u":   ("diffusion", Layers.comp, Layers.res_mk),
  "nwell":     ("well", Layers.nwell, Layers.res_mk),
  "pwell":     ("well", Layers.lvpwell, Layers.res_mk),
  "npolyf_s":  ("poly", Layers.poly, Layers.res_mk),
  "ppolyf_s":  ("poly", Layers.poly, Layers.res_mk),
  "npolyf_u":  ("poly", Layers.poly, Layers.res_mk),
  "ppolyf_u":  ("poly", Layers.poly, Layers.res_mk),
  "ppolyf_u_h": ("poly", Layers.poly, Layers.res_mk),
}

# Classification helpers (underscore prefix = internal)
_salicided = lambda m: "_s" in m
_diffusion = lambda m: m in ("nplus_s", "pplus_s", "nplus_u", "pplus_u")
_poly = lambda m: m in ("npolyf_s", "ppolyf_s", "npolyf_u", "ppolyf_u", "ppolyf_u_h")
_metal = lambda m: m in ("rm1", "rm2", "rm3", "tm6k", "tm9k", "tm11k", "tm30k")
_n_type = lambda m: m in ("nplus_s", "nplus_u", "npolyf_s", "npolyf_u", "nwell", "rm1")

# Public aliases for backward compatibility
is_salicided = _salicided
is_diffusion = _diffusion
is_poly = _poly
is_metal = _metal
is_n_type = _n_type

# ====================================================================
# Grid snapping
# ====================================================================

_DBU = 0.005


def _snap(v):
  """Snap a coordinate to the 5nm grid, matching gdsfactory's snap_to_grid."""
  return round(v / _DBU) * _DBU


# ====================================================================
# Contact stack (diffusion / substrate terminals)
# ====================================================================

_CON_SIZE = 0.22
_CON_ENC = 0.08
_CON_SPC = 0.29
_M1_AREA_MIN = 0.1444


def _diffusion_contact_stack(term_w, term_h):
  """Create contact+metal1 stack centered at origin, matching gdsfactory via_stack."""
  nc = max(1, int(term_w // (_CON_SIZE + _CON_SPC)))
  leftover_x = term_w - nc * _CON_SIZE - max(0, nc - 1) * _CON_SPC
  if nc > 1 and leftover_x / 2 < _CON_ENC - 1e-10:
    nc -= 1
    leftover_x = term_w - nc * _CON_SIZE - max(0, nc - 1) * _CON_SPC

  nr = max(1, int(term_h // (_CON_SIZE + _CON_SPC)))
  leftover_y = term_h - nr * _CON_SIZE - max(0, nr - 1) * _CON_SPC
  if nr > 1 and leftover_y / 2 < _CON_ENC - 1e-10:
    nr -= 1
    leftover_y = term_h - nr * _CON_SIZE - max(0, nr - 1) * _CON_SPC

  grid_w = nc * _CON_SIZE + max(0, nc - 1) * _CON_SPC
  grid_h = nr * _CON_SIZE + max(0, nr - 1) * _CON_SPC

  m1_w = grid_w + 2 * _CON_ENC
  m1_h = grid_h + 2 * _CON_ENC
  if m1_w * m1_h < _M1_AREA_MIN - 1e-10:
    m1_h = _M1_AREA_MIN / m1_w

  comp = []

  # Individual contact Rects
  if nc == 1 and nr == 1:
    comp.append(Rect(layer=Layers.contact,
                     w=_CON_SIZE, h=_CON_SIZE,
                     enl_l=_CON_SIZE / 2, enl_r=-_CON_SIZE / 2,
                     enl_b=_CON_SIZE / 2, enl_t=-_CON_SIZE / 2))
  else:
    gx0 = -grid_w / 2
    gy0 = -grid_h / 2
    for r in range(nr):
      for cc in range(nc):
        cx = gx0 + cc * (_CON_SIZE + _CON_SPC) + _CON_SIZE / 2
        cy = gy0 + r * (_CON_SIZE + _CON_SPC) + _CON_SIZE / 2
        contact = Rect(layer=Layers.contact, w=_CON_SIZE, h=_CON_SIZE,
                       enl_l=_CON_SIZE / 2, enl_r=-_CON_SIZE / 2,
                       enl_b=_CON_SIZE / 2, enl_t=-_CON_SIZE / 2)
        comp.append(Translated(child=contact,
                               trans=kdb.DTrans(kdb.DVector(cx, cy))))

  comp.append(Rect(layer=Layers.metal1,
                   w=m1_w, h=m1_h,
                   enl_l=m1_w / 2, enl_r=-m1_w / 2,
                   enl_b=m1_h / 2, enl_t=-m1_h / 2))

  return Linear(align=None, children=comp)


# ====================================================================
# Shared helpers
# ====================================================================


def _centered_contact_stack(term_w, term_h, parent_node):
  """Wrap a contact stack and center it on parent_node's center."""
  cw, ch = parent_w, parent_h = term_w, term_h
  cont = _diffusion_contact_stack(cw, ch)
  return Translated(child=cont,
                    trans=kdb.DTrans(kdb.DVector(_snap(cw / 2.0), _snap(ch / 2.0))))


def _make_substrate(sub_w, sub_h, sub_impl_layer, sub_impl_enc, sub_xmin, sub_ymin):
  """Build a substrate comp + implant + contact stack."""
  sub_rect = Rect(layer=Layers.comp, w=sub_w, h=sub_h)
  sub_impl = Rect(layer=sub_impl_layer, enclose=sub_rect, enl=sub_impl_enc)
  sub_cont = _centered_contact_stack(sub_w, sub_h, sub_rect)
  substrate = Linear(align=None, children=[sub_rect, sub_impl, sub_cont])
  return Translated(child=substrate,
                    trans=kdb.DTrans(kdb.DVector(_snap(sub_xmin), _snap(sub_ymin))))


def _con_polys_size(con_w, con_h):
  """Compute the con_polys bounding box size from terminal + metal1 union.

  Returns (cp_xmin, cp_ymin, cp_w, cp_h) in terminal-local coordinates.
  Used for implant sizing so it encloses both comp and metal1.
  """
  _nc = max(1, int(con_w // (_CON_SIZE + _CON_SPC)))
  _nr = max(1, int(con_h // (_CON_SIZE + _CON_SPC)))
  _gw = _nc * _CON_SIZE + max(0, _nc - 1) * _CON_SPC
  _gh = _nr * _CON_SIZE + max(0, _nr - 1) * _CON_SPC
  _mw = _gw + 2 * _CON_ENC
  _mh = _gh + 2 * _CON_ENC

  m1_xmin_local = con_w / 2 - _mw / 2
  m1_ymin_local = con_h / 2 - _mh / 2
  cp_xmin = min(0.0, m1_xmin_local)
  cp_ymin = min(0.0, m1_ymin_local)
  cp_w = max(con_w, m1_xmin_local + _mw) - cp_xmin
  cp_h = max(con_h, m1_ymin_local + _mh) - cp_ymin
  return cp_xmin, cp_ymin, cp_w, cp_h


def _make_terminal(con_w, con_h, cmp_impl_layer, impl_enc):
  """Build a diffusion terminal: comp + implant + contact stack.

  The implant encloses the con_polys (comp union metal1), not just comp.
  """
  cp_xmin, cp_ymin, cp_w, cp_h = _con_polys_size(con_w, con_h)

  con_rect = Rect(layer=Layers.comp, w=con_w, h=con_h)
  con_impl = Rect(layer=cmp_impl_layer,
                  w=cp_w + 2 * impl_enc, h=cp_h + 2 * impl_enc)
  impl_offset = kdb.DTrans(kdb.DVector(cp_xmin - impl_enc, cp_ymin - impl_enc))
  con_cont = _centered_contact_stack(con_w, con_h, con_rect)

  return Linear(align=None, children=[
    con_rect,
    Translated(child=con_impl, trans=impl_offset),
    con_cont,
  ])


def _contact_positions_on_edge(start, end, size, spacing):
  """Generate evenly-spaced contact center positions along one edge."""
  length = end - start
  n = max(1, int(length // (size + spacing)))
  total = n * size + max(0, n - 1) * spacing
  first = start + (length - total) / 2
  return [first + i * (size + spacing) + size / 2 for i in range(n)]


def _make_guard_ring(inner_xmin, inner_ymin, inner_xmax, inner_ymax, gr_w=0.36):
  """Create a P+ guard ring matching gdsfactory pcmpgr_gen.

  The guard ring is a ring between outer and inner rectangles:
    inner = provided (DNWELL + pcmpgr_enc_dn)
    outer = inner + gr_w on all sides

  The ring consists of: comp (outer-inner), pplus (enclosure on both sides),
  contacts (placed at inner rect edges, x-range limited to inner rect),
  and metal1 (same as comp ring).

  Matches gdsfactory boolean-based guard ring geometry.
  """
  comp_pp_enc = 0.16
  con_size = 0.22
  con_sp = 0.28
  con_comp_enc = 0.07

  # Outer rect = inner + gr_w
  oxmin = inner_xmin - gr_w
  oymin = inner_ymin - gr_w
  oxmax = inner_xmax + gr_w
  oymax = inner_ymax + gr_w

  # Comp ring: outer - inner, built as 4 strips of width gr_w
  children = []

  def _ring_strips(layer, ix0, iy0, iwidth, iheight, strip_w):
    # Bottom strip: y=iy0-strip_w to iy0, x=ix0-strip_w to ix0+iwidth+strip_w
    bot = Translated(child=Rect(layer=layer, w=iwidth + 2 * strip_w, h=strip_w),
                      trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0 - strip_w))))
    # Top strip: y=iy0+iheight to iy0+iheight+strip_w
    top = Translated(child=Rect(layer=layer, w=iwidth + 2 * strip_w, h=strip_w),
                      trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0 + iheight))))
    # Left strip: x=ix0-strip_w to ix0, y=iy0 to iy0+iheight
    left = Translated(child=Rect(layer=layer, w=strip_w, h=iheight),
                       trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0))))
    # Right strip: x=ix0+iwidth to ix0+iwidth+strip_w
    right = Translated(child=Rect(layer=layer, w=strip_w, h=iheight),
                        trans=kdb.DTrans(kdb.DVector(_snap(ix0 + iwidth), _snap(iy0))))
    return [top, bot, left, right]

  # Comp strips (width gr_w)
  children.extend(_ring_strips(Layers.comp, inner_xmin, inner_ymin,
                                inner_xmax - inner_xmin, inner_ymax - inner_ymin, gr_w))

  # pplus implant ring: extends comp_pp_enc inside and outside of comp
  # pplus inner = inner - comp_pp_enc, pplus outer = outer + comp_pp_enc
  ppx0 = oxmin - comp_pp_enc
  ppy0 = oymin - comp_pp_enc
  ppw = (oxmax - oxmin) + 2 * comp_pp_enc
  pph = (oymax - oymin) + 2 * comp_pp_enc
  pps = comp_pp_enc + gr_w + comp_pp_enc  # strip width
  children.extend(_ring_strips(Layers.pplus, ppx0, ppy0, ppw, pph, pps))

  # Metal1 ring: same as comp ring (outer - inner of comp)
  children.extend(_ring_strips(Layers.metal1, inner_xmin, inner_ymin,
                                inner_xmax - inner_xmin, inner_ymax - inner_ymin, gr_w))

  # Contacts: placed at inner rect edges
  # gdsfactory via_generator: x_range limited to inner rect, y_range on comp ring
  contact_rect = Rect(layer=Layers.contact, w=con_size, h=con_size,
                       enl_l=con_size / 2, enl_r=-con_size / 2,
                       enl_b=con_size / 2, enl_t=-con_size / 2)

  # Bottom contacts: y_center = inner_ymin + con_comp_enc (on comp strip)
  cy_bot = inner_ymin - gr_w / 2
  for cx in _contact_positions_on_edge(inner_xmin, inner_xmax, con_size, con_sp):
    children.append(Translated(child=contact_rect,
                                trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy_bot)))))
  # Top contacts
  cy_top = inner_ymax + gr_w / 2
  for cx in _contact_positions_on_edge(inner_xmin, inner_xmax, con_size, con_sp):
    children.append(Translated(child=contact_rect,
                                trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy_top)))))
  # Left contacts
  cx_left = inner_xmin - gr_w / 2
  for cy in _contact_positions_on_edge(inner_ymin, inner_ymax, con_size, con_sp):
    children.append(Translated(child=contact_rect,
                                trans=kdb.DTrans(kdb.DVector(_snap(cx_left), _snap(cy)))))
  # Right contacts
  cx_right = inner_xmax + gr_w / 2
  for cy in _contact_positions_on_edge(inner_ymin, inner_ymax, con_size, con_sp):
    children.append(Translated(child=contact_rect,
                                trans=kdb.DTrans(kdb.DVector(_snap(cx_right), _snap(cy)))))

  return Linear(align=None, children=children)


def _make_dnwell_layers(device_xmin, device_ymin, device_xmax, device_ymax):
  """Create LVPWELL + DNWELL enclosure layers around a device."""
  lvpwell_enc = 0.6
  dn_enc = 2.5

  children = []
  lvpwell = Rect(layer=Layers.lvpwell,
                 w=(device_xmax - device_xmin) + 2 * lvpwell_enc,
                 h=(device_ymax - device_ymin) + 2 * lvpwell_enc)
  children.append(Translated(child=lvpwell,
                             trans=kdb.DTrans(kdb.DVector(
                                 _snap(device_xmin - lvpwell_enc),
                                 _snap(device_ymin - lvpwell_enc)))))

  dn = Rect(layer=Layers.dnwell,
            w=(device_xmax - device_xmin) + 2 * (lvpwell_enc + dn_enc),
            h=(device_ymax - device_ymin) + 2 * (lvpwell_enc + dn_enc))
  children.append(Translated(child=dn,
                             trans=kdb.DTrans(kdb.DVector(
                                 _snap(device_xmin - lvpwell_enc - dn_enc),
                                 _snap(device_ymin - lvpwell_enc - dn_enc)))))

  return Linear(align=None, children=children)


def _center_contacts(res_xmin, res_ymin, res_xmax, res_ymax, count):
  """Create intermediate contact stacks along the resistor body."""
  if count <= 0:
    return None
  children = []
  spacing = (res_xmax - res_xmin) / (count + 1)
  for i in range(1, count + 1):
    cx = res_xmin + i * spacing
    cy = (res_ymin + res_ymax) / 2
    cont = _diffusion_contact_stack(0.22, 0.22)
    children.append(Translated(child=cont,
                               trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy)))))
  return Linear(align=None, children=children)


# ====================================================================
# Diffusion resistor
# ====================================================================


def _diffusion_params(model):
  """Return parameters for diffusion resistors (salicided vs unsalicided)."""
  sal = _salicided(model)
  return {
    "cmp_res_ext": 0.29 if sal else 0.52,
    "np_enc_cmp":  0.16 if sal else 0.18,
    "con_enc":     0.07 if sal else 0.0,
    "sub_w":       0.36,
    "cmp_area":    0.203,
    "comp_spacing": 0.72,
  }


def make_diffusion_resistor(model, l, w, marker_layer, implant_layer, sub_implant_layer, block_layer, nwell_layer,
                             with_contacts=True, with_substrate=True, substrate_side="left",
                             guard_ring=False, with_dnwell=False, n_center_contacts=0):
  """Match gdsfactory's plus_res_inst -> draw_nplus_res / draw_pplus_res."""
  p = _diffusion_params(model)
  cmp_res_ext = p["cmp_res_ext"]
  np_enc_cmp = p["np_enc_cmp"]
  con_enc = p["con_enc"]
  sub_w = p["sub_w"]
  cmp_area = p["cmp_area"]
  comp_spacing = p["comp_spacing"]

  marker = Rect(layer=marker_layer, w=l, h=w, name="marker")
  active = Rect(layer=Layers.comp, enclose=marker, enl_l=cmp_res_ext, enl_r=cmp_res_ext)
  implant = Rect(layer=implant_layer, enclose=active, enl=np_enc_cmp)

  # SAB for unsalicided
  sab = None
  if block_layer:
    sab_area = 2.01
    sab_res_ext = 0.22
    sab_h = w + 2 * sab_res_ext
    if l * sab_h < sab_area:
      sab_h = _snap(sab_area / l)
    sab_ref = Rect(layer=None, w=l, h=sab_h)
    sab = Rect(layer=block_layer, enclose=sab_ref)
    sab = Translated(child=sab, trans=kdb.DTrans(kdb.DVector(0, (w - sab_h) / 2.0)))

  comp = [marker, active, implant]
  if sab:
    comp.append(sab)

  # Contact stacks
  if with_contacts:
    term_w = cmp_res_ext + con_enc
    left_center_x = (-cmp_res_ext + con_enc) / 2
    right_center_x = l + (cmp_res_ext - con_enc) / 2

    left_cont = _diffusion_contact_stack(term_w, w)
    right_cont = _diffusion_contact_stack(term_w, w)

    left_cont_offset = kdb.DTrans(kdb.DVector(_snap(left_center_x), _snap(w / 2)))
    right_cont_offset = kdb.DTrans(kdb.DVector(_snap(right_center_x), _snap(w / 2)))

    comp.append(Translated(child=left_cont, trans=left_cont_offset))
    comp.append(Translated(child=right_cont, trans=right_cont_offset))

  # Center contacts on resistor body
  if n_center_contacts > 0:
    cc = _center_contacts(0, 0, l, w, n_center_contacts)
    if cc:
      comp.append(cc)

  # Substrate
  if with_substrate:
    sub_h_raw = max(w, round(cmp_area / sub_w, 3))
    sub_ymin_exact = w / 2.0 - sub_h_raw / 2.0
    sub_ymax_exact = sub_ymin_exact + sub_h_raw
    sub_h = _snap(sub_ymax_exact) - _snap(sub_ymin_exact)

    if substrate_side == "left":
      sub_target_xmin = -cmp_res_ext - comp_spacing - sub_w
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, np_enc_cmp,
                                  _snap(sub_target_xmin), _snap(sub_ymin_exact)))
    elif substrate_side == "right":
      sub_target_xmin = l + cmp_res_ext + comp_spacing
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, np_enc_cmp,
                                  _snap(sub_target_xmin), _snap(sub_ymin_exact)))
    else:  # both
      sub_left_xmin = -cmp_res_ext - comp_spacing - sub_w
      sub_right_xmin = l + cmp_res_ext + comp_spacing
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, np_enc_cmp,
                                  _snap(sub_left_xmin), _snap(sub_ymin_exact)))
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, np_enc_cmp,
                                  _snap(sub_right_xmin), _snap(sub_ymin_exact)))

  # Nwell for pplus resistors
  if nwell_layer:
    nw_enc = 0.6
    dev_xmin = -cmp_res_ext - comp_spacing - sub_w - np_enc_cmp if with_substrate and substrate_side != "right" else -np_enc_cmp
    if substrate_side == "right":
      dev_xmin = -np_enc_cmp
    elif with_substrate and substrate_side == "left":
      dev_xmin = -cmp_res_ext - comp_spacing - sub_w - np_enc_cmp
    else:
      dev_xmin = -np_enc_cmp
    dev_ymin = -np_enc_cmp
    dev_xmax = l + cmp_res_ext + np_enc_cmp
    dev_ymax = w + np_enc_cmp
    if substrate_side == "right":
      dev_xmax = l + cmp_res_ext + comp_spacing + sub_w + np_enc_cmp
    nw_rect = Rect(layer=nwell_layer,
                   w=(dev_xmax - dev_xmin) + 2 * nw_enc,
                   h=(dev_ymax - dev_ymin) + 2 * nw_enc)
    comp.append(Translated(child=nw_rect,
                           trans=kdb.DTrans(kdb.DVector(dev_xmin - nw_enc, dev_ymin - nw_enc))))

  # DNWELL for nplus models when requested
  if with_dnwell:
    dnx, dny, dpx, dpy = -cmp_res_ext, 0, l + cmp_res_ext, w
    if with_substrate and substrate_side == "left":
      dnx = -cmp_res_ext - comp_spacing - sub_w
    elif with_substrate and substrate_side == "right":
      dpx = l + cmp_res_ext + comp_spacing + sub_w
    elif with_substrate and substrate_side == "both":
      dnx = -cmp_res_ext - comp_spacing - sub_w
      dpx = l + cmp_res_ext + comp_spacing + sub_w
    comp.append(_make_dnwell_layers(dnx, dny, dpx, dpy))

  # Guard ring
  if guard_ring:
    dnx, dny, dpx, dpy = -cmp_res_ext, 0, l + cmp_res_ext, w
    if with_substrate and substrate_side == "left":
      dnx = -cmp_res_ext - comp_spacing - sub_w
    elif with_substrate and substrate_side == "right":
      dpx = l + cmp_res_ext + comp_spacing + sub_w
    elif with_substrate and substrate_side == "both":
      dnx = -cmp_res_ext - comp_spacing - sub_w
      dpx = l + cmp_res_ext + comp_spacing + sub_w
    if with_dnwell:
      # Match gdsfactory: inner = DNWELL + pcmpgr_enc_dn(2.5)
      # DNWELL = device + lvpwell_enc(0.6) + dn_enc(2.5)
      lvpwell_enc = 0.6
      dn_enc = 2.5
      pcmpgr_enc_dn = 2.5
      dnx -= lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dny -= lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dpx += lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dpy += lvpwell_enc + dn_enc + pcmpgr_enc_dn
    comp.append(_make_guard_ring(dnx, dny, dpx, dpy))

  return Linear(align=None, children=comp)


# ====================================================================
# Poly resistor
# ====================================================================


def _poly_params(model, with_dnwell=False):
  """Return parameters for poly resistors (n-type vs p-type, salicided vs not)."""
  sub_sp = 0.26 if (_n_type(model) and not with_dnwell) else 0.4
  return {
    "pl_res_ext": 0.29 if _salicided(model) else 0.66,
    "con_enc":    0.07 if _salicided(model) else 0.0,
    "comp_spacing": 0.46 + sub_sp,
  }


def make_poly_resistor(model, l, w, marker_layer, implant_layer, sub_implant_layer, block_layer,
                        with_contacts=True, with_substrate=True, substrate_side="left",
                        guard_ring=False, with_dnwell=False, n_center_contacts=0):
  """Match gdsfactory's polyf_res_inst -> draw_npolyf_res / draw_ppolyf_res."""
  pp = _poly_params(model, with_dnwell=with_dnwell and _n_type(model))
  pl_res_ext = pp["pl_res_ext"]
  con_enc = pp["con_enc"]
  np_enc_poly2 = 0.3
  pp_enc_cmp = 0.16
  sub_w = 0.36
  cmp_area = 0.203
  comp_spacing = pp["comp_spacing"]
  # gdsfactory uses nplus for substrate implant when deepnwell=1 for n-type poly
  if with_dnwell and _n_type(model):
    sub_implant_layer = Layers.nplus

  marker = Rect(layer=marker_layer, w=l, h=w, name="marker")
  poly = Rect(layer=Layers.poly, enclose=marker, enl_l=pl_res_ext, enl_r=pl_res_ext)
  implant = Rect(layer=implant_layer, enclose=poly, enl=np_enc_poly2)

  comp = [marker, poly, implant]

  # SAB for unsalicided
  if block_layer:
    sab_area = 2.01
    sab_res_ext = 0.28
    sab_h = w + 2 * sab_res_ext
    if l * sab_h < sab_area:
      sab_h = _snap(sab_area / l)
    sab_ref = Rect(layer=None, w=l, h=sab_h)
    sab = Rect(layer=block_layer, enclose=sab_ref)
    sab = Translated(child=sab, trans=kdb.DTrans(kdb.DVector(0, (w - sab_h) / 2.0)))
    comp.append(sab)

  # Contact stacks
  if with_contacts:
    left_term_w = pl_res_ext + con_enc
    left_center_x = (-pl_res_ext + con_enc) / 2
    right_center_x = left_center_x + (pl_res_ext - con_enc + l)

    left_cont = _diffusion_contact_stack(left_term_w, w)
    right_cont = _diffusion_contact_stack(left_term_w, w)

    left_cont_offset = kdb.DTrans(kdb.DVector(_snap(left_center_x), _snap(w / 2)))
    right_cont_offset = kdb.DTrans(kdb.DVector(_snap(right_center_x), _snap(w / 2)))

    comp.append(Translated(child=left_cont, trans=left_cont_offset))
    comp.append(Translated(child=right_cont, trans=right_cont_offset))

  # Center contacts on resistor body
  if n_center_contacts > 0:
    cc = _center_contacts(0, 0, l, w, n_center_contacts)
    if cc:
      comp.append(cc)

  # Substrate
  if with_substrate:
    sub_h_raw = max(w, round(cmp_area / sub_w, 3))
    sub_ymin_exact = w / 2.0 - sub_h_raw / 2.0
    sub_ymax_exact = sub_ymin_exact + sub_h_raw
    sub_h = _snap(sub_ymax_exact) - _snap(sub_ymin_exact)

    if substrate_side == "left":
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, pp_enc_cmp,
                                  _snap(-pl_res_ext - comp_spacing - sub_w),
                                  _snap(sub_ymin_exact)))
    elif substrate_side == "right":
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, pp_enc_cmp,
                                  _snap(l + pl_res_ext + comp_spacing),
                                  _snap(sub_ymin_exact)))
    else:  # both
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, pp_enc_cmp,
                                  _snap(-pl_res_ext - comp_spacing - sub_w),
                                  _snap(sub_ymin_exact)))
      comp.append(_make_substrate(sub_w, sub_h, sub_implant_layer, pp_enc_cmp,
                                  _snap(l + pl_res_ext + comp_spacing),
                                  _snap(sub_ymin_exact)))

  # DNWELL for n-type poly when requested
  if with_dnwell:
    dnx, dny, dpx, dpy = -pl_res_ext, 0, l + pl_res_ext, w
    if with_substrate and substrate_side == "left":
      dnx = -pl_res_ext - comp_spacing - sub_w
    elif with_substrate and substrate_side == "right":
      dpx = l + pl_res_ext + comp_spacing + sub_w
    elif with_substrate and substrate_side == "both":
      dnx = -pl_res_ext - comp_spacing - sub_w
      dpx = l + pl_res_ext + comp_spacing + sub_w
    # gdsfactory creates only DNWELL (no LVPWELL) for poly resistors
    dn_enc_cmp = 0.5
    dn_rect = Rect(layer=Layers.dnwell,
                   w=(dpx - dnx) + 2 * dn_enc_cmp,
                   h=(dpy - dny) + 2 * dn_enc_cmp)
    comp.append(Translated(child=dn_rect,
                           trans=kdb.DTrans(kdb.DVector(
                               _snap(dnx - dn_enc_cmp),
                               _snap(dny - dn_enc_cmp)))))

  # Guard ring
  if guard_ring:
    dnx, dny, dpx, dpy = -pl_res_ext, 0, l + pl_res_ext, w
    if with_substrate and substrate_side == "left":
      dnx = -pl_res_ext - comp_spacing - sub_w
    elif with_substrate and substrate_side == "right":
      dpx = l + pl_res_ext + comp_spacing + sub_w
    elif with_substrate and substrate_side == "both":
      dnx = -pl_res_ext - comp_spacing - sub_w
      dpx = l + pl_res_ext + comp_spacing + sub_w
    if with_dnwell:
      # Match gdsfactory: inner = DNWELL + pcmpgr_enc_dn(2.5)
      # Poly DNWELL = device + dn_enc_cmp(0.5)
      dn_enc_cmp = 0.5
      pcmpgr_enc_dn = 2.5
      dnx -= dn_enc_cmp + pcmpgr_enc_dn
      dny -= dn_enc_cmp + pcmpgr_enc_dn
      dpx += dn_enc_cmp + pcmpgr_enc_dn
      dpy += dn_enc_cmp + pcmpgr_enc_dn
    comp.append(_make_guard_ring(dnx, dny, dpx, dpy))

  return Linear(align=None, children=comp)


# ====================================================================
# ppolyf_u_h (high sheet resistance poly)
# ====================================================================


def make_ppolyf_u_h(model, l, w, marker_layer, implant_layer, sub_implant_layer, block_layer,
                     with_contacts=True, with_substrate=True, substrate_side="left",
                     guard_ring=False):
  """Match gdsfactory's draw_ppolyf_u_high_Rs_res."""
  pl_res_ext = 0.64
  pp_enc_poly2 = 0.18
  pp_enc_cmp = 0.02
  comp_spacing = 0.7
  sab_res_ext_x = 0.1
  sab_res_ext_y = 0.28
  con_size = 0.36
  resis_enc_x = 1.04
  resis_enc_y = 0.4
  np_pp_area = 0.351
  sab_area = 2.01
  sub_w = 0.42

  marker = Rect(layer=marker_layer, w=l, h=w, name="marker")

  # Resistor layer
  resis = Rect(layer=Layers.resistor, w=l + 2 * resis_enc_x, h=w + 2 * resis_enc_y)
  resis_offset = kdb.DTrans(kdb.DVector(_snap(-resis_enc_x), _snap(-resis_enc_y)))

  # SAB with vertex snapping
  sab_w = l + 2 * sab_res_ext_x
  sab_h_raw = w + 2 * sab_res_ext_y
  if sab_w * sab_h_raw < sab_area:
    sab_h_raw = round(sab_area / sab_w, 3)
  sab_xmin_s = _snap(l / 2 - sab_w / 2)
  sab_xmax_s = _snap(l / 2 + sab_w / 2)
  sab_ymin_s = _snap(w / 2 - sab_h_raw / 2)
  sab_ymax_s = _snap(w / 2 + sab_h_raw / 2)
  sab = Rect(layer=block_layer, w=sab_xmax_s - sab_xmin_s, h=sab_ymax_s - sab_ymin_s)
  sab = Translated(child=sab, trans=kdb.DTrans(kdb.DVector(sab_xmin_s, sab_ymin_s)))

  # Poly
  poly = Rect(layer=Layers.poly, enclose=marker, enl_l=pl_res_ext, enl_r=pl_res_ext)

  # P+ implant pads at two ends
  pplus_w = pl_res_ext + pp_enc_poly2
  pplus_h = w + 2 * pp_enc_poly2
  pplus_left = Rect(layer=implant_layer, w=pplus_w, h=pplus_h)
  pplus_right = Rect(layer=implant_layer, w=pplus_w, h=pplus_h)
  pplus_left_offset = kdb.DTrans(kdb.DVector(_snap(-pl_res_ext - pp_enc_poly2), _snap(-pp_enc_poly2)))
  pplus_right_offset = kdb.DTrans(kdb.DVector(_snap(l), _snap(-pp_enc_poly2)))

  comp = [
    marker,
    Translated(child=resis, trans=resis_offset),
    sab,
    poly,
    Translated(child=pplus_left, trans=pplus_left_offset),
    Translated(child=pplus_right, trans=pplus_right_offset),
  ]

  # Contact stacks
  if with_contacts:
    left_cont = _diffusion_contact_stack(con_size, w)
    right_cont = _diffusion_contact_stack(con_size, w)
    left_center_x = -pl_res_ext + con_size / 2
    right_center_x = pl_res_ext + l - con_size / 2
    left_cont_offset = kdb.DTrans(kdb.DVector(_snap(left_center_x), _snap(w / 2.0)))
    right_cont_offset = kdb.DTrans(kdb.DVector(_snap(right_center_x), _snap(w / 2.0)))

    comp.append(Translated(child=left_cont, trans=left_cont_offset))
    comp.append(Translated(child=right_cont, trans=right_cont_offset))

  # Substrate (custom implant sizing with min area)
  if with_substrate:
    sub_rect = Rect(layer=Layers.comp, w=sub_w, h=w)
    sub_impl_w = sub_w + 2 * pp_enc_cmp
    sub_impl_h = w + 2 * pp_enc_cmp
    if sub_impl_w * sub_impl_h < np_pp_area:
      sub_impl_h = _snap(round(np_pp_area / sub_impl_w, 3))
    sub_impl = Rect(layer=sub_implant_layer, w=sub_impl_w, h=sub_impl_h)
    sub_impl_centered = Translated(
      child=sub_impl,
      trans=kdb.DTrans(kdb.DVector(_snap((sub_w - sub_impl_w) / 2.0),
                                   _snap((w - sub_impl_h) / 2.0))))
    sub_cont = _centered_contact_stack(sub_w, w, sub_rect)
    substrate = Linear(align=None, children=[sub_rect, sub_impl_centered, sub_cont])

    if substrate_side == "left":
      sub_offset = kdb.DTrans(kdb.DVector(_snap(-pl_res_ext - comp_spacing - sub_w), _snap(0)))
    elif substrate_side == "right":
      sub_offset = kdb.DTrans(kdb.DVector(_snap(l + pl_res_ext + comp_spacing), _snap(0)))
    else:  # both
      sub_left_offset = kdb.DTrans(kdb.DVector(_snap(-pl_res_ext - comp_spacing - sub_w), _snap(0)))
      sub_right_offset = kdb.DTrans(kdb.DVector(_snap(l + pl_res_ext + comp_spacing), _snap(0)))
      comp.append(Translated(child=substrate, trans=sub_left_offset))
      comp.append(Translated(child=substrate, trans=sub_right_offset))
    if substrate_side != "both":
      comp.append(Translated(child=substrate, trans=sub_offset))

  # Guard ring
  if guard_ring:
    dnx, dny, dpx, dpy = -pl_res_ext, 0, l + pl_res_ext, w
    if with_substrate and substrate_side == "left":
      dnx = -pl_res_ext - comp_spacing - sub_w
    elif with_substrate and substrate_side == "right":
      dpx = l + pl_res_ext + comp_spacing + sub_w
    elif with_substrate and substrate_side == "both":
      dnx = -pl_res_ext - comp_spacing - sub_w
      dpx = l + pl_res_ext + comp_spacing + sub_w
    comp.append(_make_guard_ring(dnx, dny, dpx, dpy))

  return Linear(align=None, children=comp)


# ====================================================================
# Well resistor (nwell, pwell)
# ====================================================================


def make_well_resistor(model, l, w, marker_layer, well_layer, cmp_impl_layer, sub_implant_layer,
                        with_contacts=True, with_substrate=True, substrate_side="left",
                        guard_ring=False, with_dnwell=False):
  """Match gdsfactory's draw_well_res."""
  nw_res_ext = 0.48
  nw_res_enc = 0.5
  nw_enc_cmp = 0.12
  sub_w = 0.36
  pp_enc_cmp = 0.16
  nw_comp_spacing = 0.72
  dn_enc_lvpwell = 2.5
  lvpwell_enc = 0.6
  dn_enc = 2.5

  marker = Rect(layer=marker_layer, w=l, h=w + 2 * nw_res_enc, name="marker")

  # Well
  well = Rect(layer=well_layer, w=l + 2 * nw_res_ext, h=w)
  well_offset = kdb.DTrans(kdb.DVector(_snap(-nw_res_ext), _snap(nw_res_enc)))

  # Terminal comp dimensions
  con_w = nw_res_ext - nw_enc_cmp
  con_h = w - 2 * nw_enc_cmp
  con_xmin = -nw_res_ext + nw_enc_cmp
  con_ymin = nw_res_enc + nw_enc_cmp

  # Both left and right terminals use the same implant sizing logic:
  # implant encloses con_polys (comp union metal1), not just comp
  left_terminal = _make_terminal(con_w, con_h, cmp_impl_layer, pp_enc_cmp)
  right_terminal = _make_terminal(con_w, con_h, cmp_impl_layer, pp_enc_cmp)

  _cp_xmin, _cp_ymin, _cp_w, _cp_h = _con_polys_size(con_w, con_h)
  con_spacing = l + 2 * nw_res_ext - 2 * nw_enc_cmp - _cp_w

  left_offset = kdb.DTrans(kdb.DVector(_snap(con_xmin), _snap(con_ymin)))
  right_offset = kdb.DTrans(kdb.DVector(_snap(con_xmin + con_spacing), _snap(con_ymin)))

  comp = [
    marker,
    Translated(child=well, trans=well_offset),
  ]

  if with_contacts:
    comp.append(Translated(child=left_terminal, trans=left_offset))
    comp.append(Translated(child=right_terminal, trans=right_offset))

  # Substrate
  if with_substrate:
    sub_ymin = nw_res_enc
    if substrate_side == "left":
      sub_xmin = -nw_res_ext - nw_comp_spacing - sub_w
      comp.append(_make_substrate(sub_w, w, sub_implant_layer, pp_enc_cmp,
                                  _snap(sub_xmin), _snap(sub_ymin)))
    elif substrate_side == "right":
      sub_xmin = l + nw_res_ext + nw_comp_spacing
      comp.append(_make_substrate(sub_w, w, sub_implant_layer, pp_enc_cmp,
                                  _snap(sub_xmin), _snap(sub_ymin)))
    else:  # both
      sub_left_xmin = -nw_res_ext - nw_comp_spacing - sub_w
      sub_right_xmin = l + nw_res_ext + nw_comp_spacing
      comp.append(_make_substrate(sub_w, w, sub_implant_layer, pp_enc_cmp,
                                  _snap(sub_left_xmin), _snap(sub_ymin)))
      comp.append(_make_substrate(sub_w, w, sub_implant_layer, pp_enc_cmp,
                                  _snap(sub_right_xmin), _snap(sub_ymin)))

  # DNWell for pwell model (always) or nwell with dnwell flag
  if model == "pwell":
    dn_well = Rect(layer=Layers.dnwell,
                   w=l + 2 * nw_res_ext + 2 * dn_enc_lvpwell,
                   h=w + 2 * dn_enc_lvpwell)
    dn_offset = kdb.DTrans(kdb.DVector(_snap(-nw_res_ext - dn_enc_lvpwell),
                                       _snap(nw_res_enc - dn_enc_lvpwell)))
    comp.append(Translated(child=dn_well, trans=dn_offset))

  # DNWELL for nwell model when requested
  if with_dnwell and model == "nwell":
    dnx = -nw_res_ext - nw_comp_spacing - sub_w if with_substrate and substrate_side in ("left", "both") else -nw_res_ext
    dpx = l + nw_res_ext + nw_comp_spacing + sub_w if with_substrate and substrate_side in ("right", "both") else l + nw_res_ext
    comp.append(_make_dnwell_layers(dnx, nw_res_enc, dpx, w + nw_res_enc))

  # Guard ring
  if guard_ring:
    dnx = -nw_res_ext - nw_comp_spacing - sub_w if with_substrate and substrate_side in ("left", "both") else -nw_res_ext
    dpx = l + nw_res_ext + nw_comp_spacing + sub_w if with_substrate and substrate_side in ("right", "both") else l + nw_res_ext
    dny = nw_res_enc - nw_res_enc
    dpy = w + nw_res_enc
    if model == "pwell":
      # Match gdsfactory: inner = DNWELL + pcmpgr_enc_dn(2.5)
      # pwell DNWELL = well + dn_enc_lvpwell(2.5)
      dnx -= dn_enc_lvpwell + dn_enc_lvpwell
      dny -= dn_enc_lvpwell + dn_enc_lvpwell
      dpx += dn_enc_lvpwell + dn_enc_lvpwell
      dpy += dn_enc_lvpwell + dn_enc_lvpwell
    elif with_dnwell:
      # nwell with DNWELL: inner = LVPWELL+DNWELL + pcmpgr_enc_dn
      pcmpgr_enc_dn = 2.5
      dnx -= lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dny -= lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dpx += lvpwell_enc + dn_enc + pcmpgr_enc_dn
      dpy += lvpwell_enc + dn_enc + pcmpgr_enc_dn
    comp.append(_make_guard_ring(dnx, dny, dpx, dpy))

  return Linear(align=None, children=comp)


# ====================================================================
# Entry point
# ====================================================================


def make_resistor(
    model, l=1.0, w=1.0,
    with_contacts=True,
    with_substrate=True,
    substrate_side="left",
    guard_ring=False,
    with_dnwell=False,
    n_center_contacts=0,
    contacts=0,  # deprecated, kept for backward compatibility
):
  """Parametric resistor generator. Returns a Node tree.

  with_contacts: include terminal contacts at both ends (default True)
  with_substrate: include substrate tap (default True)
  substrate_side: placement of substrate tap - "left", "right", or "both" (default "left")
  guard_ring: add P+ guard ring around device (default False)
  with_dnwell: add DNWELL + LVPWELL enclosure (default False, only for nplus/npolyf/nwell)
  n_center_contacts: number of intermediate contacts along resistor body (default 0)
  contacts: deprecated, kept for backward compatibility
  """
  if model not in resistor_type_map:
    raise ValueError(f"Unknown resistor model: {model!r}. "
                     f"Valid models: {res_models}")

  res_type, res_layer, marker_layer = resistor_type_map[model]

  if _metal(model):
    m_ext = 0.28
    body = Rect(layer=marker_layer, w=l, h=w, name="body")
    device = Linear(align="C", children=[
      body,
      Rect(layer=res_layer, enclose=body, enl_l=m_ext, enl_r=m_ext),
    ])
    return Justify(child=device, ref_point="SW")

  if _diffusion(model):
    implant_layer = Layers.nplus if _n_type(model) else Layers.pplus
    sub_implant_layer = Layers.pplus if _n_type(model) else Layers.nplus
    block_layer = Layers.sab if not _salicided(model) else None
    nwell_layer = Layers.nwell if not _n_type(model) else None
    return make_diffusion_resistor(model, l, w, marker_layer, implant_layer,
                                   sub_implant_layer, block_layer, nwell_layer,
                                   with_contacts=with_contacts,
                                   with_substrate=with_substrate,
                                   substrate_side=substrate_side,
                                   guard_ring=guard_ring,
                                   with_dnwell=with_dnwell and _n_type(model),
                                   n_center_contacts=n_center_contacts)

  if model == "ppolyf_u_h":
    return make_ppolyf_u_h(model, l, w, marker_layer, Layers.pplus, Layers.pplus, Layers.sab,
                           with_contacts=with_contacts,
                           with_substrate=with_substrate,
                           substrate_side=substrate_side,
                           guard_ring=guard_ring)

  if _poly(model):
    implant_layer = Layers.nplus if _n_type(model) else Layers.pplus
    block_layer = Layers.sab if not _salicided(model) else None
    return make_poly_resistor(model, l, w, marker_layer, implant_layer,
                              Layers.pplus, block_layer,
                              with_contacts=with_contacts,
                              with_substrate=with_substrate,
                              substrate_side=substrate_side,
                              guard_ring=guard_ring,
                              with_dnwell=with_dnwell and _n_type(model),
                              n_center_contacts=n_center_contacts)

  if model in ("nwell", "pwell"):
    cmp_impl_layer = Layers.nplus if model == "nwell" else Layers.pplus
    sub_implant_layer = Layers.pplus if model == "nwell" else Layers.nplus
    well_layer = Layers.nwell if model == "nwell" else Layers.lvpwell
    return make_well_resistor(model, l, w, marker_layer, well_layer,
                              cmp_impl_layer, sub_implant_layer,
                              with_contacts=with_contacts,
                              with_substrate=with_substrate,
                              substrate_side=substrate_side,
                              guard_ring=guard_ring,
                              with_dnwell=with_dnwell and (model == "nwell"))

  raise ValueError(f"Resistor model {model!r} has no generator implemented.")
