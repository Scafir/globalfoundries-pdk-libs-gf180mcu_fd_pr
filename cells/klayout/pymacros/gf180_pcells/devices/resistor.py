import pya as kdb

from ..tech.gf180_layers import Layers
from ..tech.gf180_rules import Rules
from ..core.node import Node
from ..core.array import Array
from ..core.align import LayerAlign, RefShift
from ..core.pack import PackRef
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
_CON_SPC = 0.25
_CON_SPC_ARRAY = 0.28
_M1_AREA_MIN = 0.1444


def _diffusion_contact_stack(term_w: float, term_h: float):
    nc = max(1, int(term_w // (_CON_SIZE + _CON_SPC)))
    if nc > 1:
        leftover_x = term_w - nc * _CON_SIZE - max(0, nc - 1) * _CON_SPC
        if leftover_x / 2 < _CON_ENC - 1e-10:
            nc -= 1

    nr = max(1, int(term_h // (_CON_SIZE + _CON_SPC)))
    if nr > 1:
        leftover_y = term_h - nr * _CON_SIZE - max(0, nr - 1) * _CON_SPC
        if leftover_y / 2 < _CON_ENC - 1e-10:
            nr -= 1

    spacing = _CON_SPC
    if (nc >= 4) and (nr >= 4):
        spacing = _CON_SPC_ARRAY

    pitch = _CON_SIZE + spacing

    # Pitch container defines spacing; contact is centered within each cell
    pitch_container = Justify(child=Rect(layer=None, w=pitch, h=pitch), ref_point="C")
    contact = Justify(child=Rect(layer=Layers.contact, w=_CON_SIZE, h=_CON_SIZE), ref_point="C")
    cell = Linear(align=None, children=[pitch_container, contact])

    grid = Array(child=cell, nx=nc, ny=nr)

    # Center the entire grid at origin
    centered_grid = Justify(child=grid, ref_point="C")

    # Metal1 enclosure
    grid_w = nc * _CON_SIZE + max(0, nc - 1) * spacing
    grid_h = nr * _CON_SIZE + max(0, nr - 1) * spacing
    m1_w = grid_w + 2 * _CON_ENC
    m1_h = grid_h + 2 * _CON_ENC
    if m1_w * m1_h < _M1_AREA_MIN:
        m1_h = _M1_AREA_MIN / m1_w

    metal1 = Justify(child=Rect(layer=Layers.metal1, w=m1_w, h=m1_h), ref_point="C")

    stack = Linear(align=None, children=[centered_grid, metal1])
    return stack


# ====================================================================
# Shared helpers
# ====================================================================

def _make_substrate(sub_w, sub_h, sub_impl_layer, sub_impl_enc, sub_xmin, sub_ymin):
    """Build a substrate comp + implant + contact stack."""
    sub_rect = Rect(layer=Layers.comp, w=sub_w, h=sub_h)
    sub_impl = Rect(layer=sub_impl_layer, enclose=sub_rect, enl=sub_impl_enc)
    sub_cont = _diffusion_contact_stack(sub_w, sub_h)
    substrate = Linear(align="C", children=[sub_rect, sub_impl, sub_cont])
    return substrate

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
    comp_pp_enc = 0.16
    con_size, con_sp, con_comp_enc = 0.22, 0.28, 0.07
    oxmin, oymin = inner_xmin - gr_w, inner_ymin - gr_w
    oxmax, oymax = inner_xmax + gr_w, inner_ymax + gr_w

    children = []
    def _ring_strips(layer, ix0, iy0, iwidth, iheight, strip_w):
        bot = Translated(child=Rect(layer=layer, w=iwidth + 2 * strip_w, h=strip_w),
                         trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0 - strip_w))))
        top = Translated(child=Rect(layer=layer, w=iwidth + 2 * strip_w, h=strip_w),
                         trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0 + iheight))))
        left = Translated(child=Rect(layer=layer, w=strip_w, h=iheight),
                          trans=kdb.DTrans(kdb.DVector(_snap(ix0 - strip_w), _snap(iy0))))
        right = Translated(child=Rect(layer=layer, w=strip_w, h=iheight),
                           trans=kdb.DTrans(kdb.DVector(_snap(ix0 + iwidth), _snap(iy0))))
        return [top, bot, left, right]

    iw, ih = inner_xmax - inner_xmin, inner_ymax - inner_ymin
    children.extend(_ring_strips(Layers.comp, inner_xmin, inner_ymin, iw, ih, gr_w))

    pps = comp_pp_enc + gr_w + comp_pp_enc
    children.extend(_ring_strips(Layers.pplus, oxmin - comp_pp_enc, oymin - comp_pp_enc,
                                 (oxmax - oxmin) + 2 * comp_pp_enc, (oymax - oymin) + 2 * comp_pp_enc, pps))

    children.extend(_ring_strips(Layers.metal1, inner_xmin, inner_ymin, iw, ih, gr_w))

    contact_rect = Rect(layer=Layers.contact, w=con_size, h=con_size,
                        enl_l=con_size / 2, enl_r=-con_size / 2,
                        enl_b=con_size / 2, enl_t=-con_size / 2)

    cy_bot = inner_ymin - gr_w / 2
    for cx in _contact_positions_on_edge(inner_xmin, inner_xmax, con_size, con_sp):
        children.append(Translated(child=contact_rect, trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy_bot)))))
    cy_top = inner_ymax + gr_w / 2
    for cx in _contact_positions_on_edge(inner_xmin, inner_xmax, con_size, con_sp):
        children.append(Translated(child=contact_rect, trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy_top)))))
    cx_left = inner_xmin - gr_w / 2
    for cy in _contact_positions_on_edge(inner_ymin, inner_ymax, con_size, con_sp):
        children.append(Translated(child=contact_rect, trans=kdb.DTrans(kdb.DVector(_snap(cx_left), _snap(cy)))))
    cx_right = inner_xmax + gr_w / 2
    for cy in _contact_positions_on_edge(inner_ymin, inner_ymax, con_size, con_sp):
        children.append(Translated(child=contact_rect, trans=kdb.DTrans(kdb.DVector(_snap(cx_right), _snap(cy)))))

    return Linear(align=None, children=children)


def _center_contacts(res_xmin, res_ymin, res_xmax, res_ymax, count):
    if count <= 0: return None
    children = []
    spacing = (res_xmax - res_xmin) / (count + 1)
    for i in range(1, count + 1):
        cx = res_xmin + i * spacing
        cy = (res_ymin + res_ymax) / 2
        cont = _diffusion_contact_stack(0.22, 0.22)
        children.append(Translated(child=cont, trans=kdb.DTrans(kdb.DVector(_snap(cx), _snap(cy)))))
    return Linear(align=None, children=children)


# ====================================================================
# Configuration Factory
# ====================================================================

def _get_resistor_cfg(model):
    cfg = {
        "ext": 0.29, "impl_enc": 0.16, "con_enc": 0.07,
        "sub_spacing": 0.72, "sub_w": 0.36, "sub_min_area": 0.203,
        "gr_w": 0.36, "dn_enc": 2.5, "lvpwell_enc": 0.6,
        "with_lvpwell": False, "custom_terminals": False,
        "custom_sab": False, "sab_area": 2.01, "sab_ext": 0.22,
        "sub_ref_layer": None  # DRC reference layer for substrate spacing
    }
    if _diffusion(model):
        cfg.update({
            "ext": 0.29 if _salicided(model) else 0.52,
            "impl_enc": 0.16 if _salicided(model) else 0.18,
            "con_enc": 0.07 if _salicided(model) else 0.0,
            "has_nwell_enc": not _n_type(model),
            "sub_ref_layer": Layers.comp
       })
    elif _poly(model):
        cfg.update({
            "ext": 0.29 if _salicided(model) else 0.66,
            "impl_enc": 0.3,
            "con_enc": 0.07 if _salicided(model) else 0.0,
            "sub_spacing": 0.46 + (0.26 if _n_type(model) else 0.4),
            "sub_ref_layer": Layers.nplus if _n_type(model) else Layers.pplus,
        })
    elif model == "ppolyf_u_h":
        cfg.update({
            "ext": 0.64, "impl_enc": 0.18, "sub_spacing": 0.7,
            "sub_w": 0.42, "custom_sab": True,
            "sab_area": 2.01, "sab_ext": 0.28, "sab_res_ext_x": 0.1,
            "resis_enc_x": 1.04, "resis_enc_y": 0.4,
            "sub_ref_layer": Layers.nplus if _n_type(model) else Layers.pplus,
        })
    elif model in ("nwell", "pwell"):
        cfg.update({
            "ext": 0.48, "impl_enc": 0.12, "sub_spacing": 0.72,
            "custom_terminals": True,
            "sub_ref_layer": Layers.nplus if _n_type(model) else Layers.pplus,
        })
    return cfg


# ====================================================================
# Core Builders (return children + bounds)
# ====================================================================

def _build_diff_poly_core(model, l, w, cfg, with_contacts):
    ext, impl_enc, con_enc = cfg["ext"], cfg["impl_enc"], cfg["con_enc"]
    marker_layer = resistor_type_map[model][2]
    active_layer = Layers.comp if _diffusion(model) else Layers.poly
    impl_layer = Layers.nplus if _n_type(model) else Layers.pplus

    # Core stack (all centered at origin)
    marker = Rect(layer=marker_layer, w=l, h=w, name="marker")
    active = Rect(layer=active_layer, enclose=marker, enl_l=ext, enl_r=ext)
    implant = Rect(layer=impl_layer, enclose=active, enl=impl_enc)
    core = Linear(align="C", children=[marker, active, implant])

    # SAB (if unsalicided) - vertically centered with core
    if not _salicided(model):
        sab_h = max(w + 2 * cfg["sab_ext"], _snap(cfg["sab_area"] / l))
        sab = Justify(child=Rect(layer=Layers.sab, w=l, h=sab_h), ref_point="C")
        core = Linear(align="C", children=[core, sab])

    # 3. Side contact helper: aligns inner edge to active boundary
    left_cont = _diffusion_contact_stack(ext + con_enc, w)
    right_cont = _diffusion_contact_stack(ext + con_enc, w)

    # Align on CONTACT layer, apply spacing offsets
    left_aligned  = RefShift(LayerAlign(left_cont, Layers.contact))
    right_aligned = RefShift(LayerAlign(right_cont, Layers.contact))

    # Chain: left | core | right
    assembly = Linear(align="HC", children=[left_aligned, core, right_aligned])

    if not _n_type(model):
        nwell_enc = Rect(
            enclose=assembly,
            enclose_layer=Layers.comp,
            enl=0.6,
            layer=Layers.nwell)
        assembly = Linear(align=None, children=[assembly, nwell_enc])

    return Justify(child=assembly, ref_point="C")

def _build_well_core(model, l, w, cfg, with_contacts):
    children = []
    ext, impl_enc = cfg["ext"], cfg["impl_enc"]
    nw_res_enc = 0.5
    well_layer = Layers.nwell if model == "nwell" else Layers.lvpwell
    marker_layer = resistor_type_map[model][2]
    cmp_impl_layer = Layers.nplus if model == "nwell" else Layers.pplus

    marker = Rect(layer=marker_layer, w=l, h=w + 2 * nw_res_enc, name="marker")
    well = Rect(layer=well_layer, w=l + 2 * ext, h=w)
    well_offset = kdb.DTrans(kdb.DVector(_snap(-ext), _snap(nw_res_enc)))
    children.extend([marker, Translated(child=well, trans=well_offset)])

    con_w = ext - impl_enc
    con_h = w - 2 * impl_enc
    con_xmin, con_ymin = -ext + impl_enc, nw_res_enc + impl_enc

    left_term = _make_terminal(con_w, con_h, cmp_impl_layer, 0.16)
    right_term = _make_terminal(con_w, con_h, cmp_impl_layer, 0.16)

    _cp_xmin, _cp_ymin, _cp_w, _cp_h = _con_polys_size(con_w, con_h)
    con_spacing = l + 2 * ext - 2 * impl_enc - _cp_w

    if with_contacts:
        left_offset = kdb.DTrans(kdb.DVector(_snap(con_xmin), _snap(con_ymin)))
        right_offset = kdb.DTrans(kdb.DVector(_snap(con_xmin + con_spacing), _snap(con_ymin)))
        children.extend([
            Translated(child=left_term, trans=left_offset),
            Translated(child=right_term, trans=right_offset)
        ])

    return Linear(align=None, children=children)


def _build_ppolyf_u_h_core(model, l, w, cfg, with_contacts):
    children = []
    ext = cfg["ext"]
    marker_layer = resistor_type_map[model][2]
    marker = Rect(layer=marker_layer, w=l, h=w, name="marker")

    resis = Rect(layer=Layers.resistor, w=l + 2 * cfg["resis_enc_x"], h=w + 2 * cfg["resis_enc_y"])
    resis_offset = kdb.DTrans(kdb.DVector(_snap(-cfg["resis_enc_x"]), _snap(-cfg["resis_enc_y"])))

    sab_w = l + 2 * cfg["sab_res_ext_x"]
    sab_h_raw = w + 2 * cfg["sab_ext"]
    if sab_w * sab_h_raw < cfg["sab_area"]:
        sab_h_raw = round(cfg["sab_area"] / sab_w, 3)
    sab_xmin, sab_xmax = _snap(l / 2 - sab_w / 2), _snap(l / 2 + sab_w / 2)
    sab_ymin, sab_ymax = _snap(w / 2 - sab_h_raw / 2), _snap(w / 2 + sab_h_raw / 2)
    sab = Rect(layer=Layers.sab, w=sab_xmax - sab_xmin, h=sab_ymax - sab_ymin)
    sab_trans = kdb.DTrans(kdb.DVector(sab_xmin, sab_ymin))

    poly = Rect(layer=Layers.poly, enclose=marker, enl_l=ext, enl_r=ext)

    pp_w = ext + cfg["impl_enc"]
    pp_h = w + 2 * cfg["impl_enc"]
    pp_left = Rect(layer=Layers.pplus, w=pp_w, h=pp_h)
    pp_right = Rect(layer=Layers.pplus, w=pp_w, h=pp_h)
    pp_left_off = kdb.DTrans(kdb.DVector(_snap(-ext - cfg["impl_enc"]), _snap(-cfg["impl_enc"])))
    pp_right_off = kdb.DTrans(kdb.DVector(_snap(l), _snap(-cfg["impl_enc"])))

    children.extend([
        marker, Translated(child=resis, trans=resis_offset),
        Translated(child=sab, trans=sab_trans), poly,
        Translated(child=pp_left, trans=pp_left_off),
        Translated(child=pp_right, trans=pp_right_off)
    ])

    if with_contacts:
        con_size = 0.36
        left_cx = _snap(-ext + con_size / 2)
        right_cx = _snap(ext + l - con_size / 2)
        cy = _snap(w / 2.0)
        left_cont = _diffusion_contact_stack(con_size, w)
        right_cont = _diffusion_contact_stack(con_size, w)
        children.extend([
            Translated(child=left_cont, trans=kdb.DTrans(kdb.DVector(left_cx, cy))),
            Translated(child=right_cont, trans=kdb.DTrans(kdb.DVector(right_cx, cy)))
        ])

    return Linear(align=None, children=children)


# ====================================================================
# Peripheral Pipeline (bounds-tracking)
# ====================================================================

def _apply_substrate(children, cfg, model, side):
    ref_layer = cfg.get("sub_ref_layer")
    if ref_layer is None:
        return children  # Skip for metal or models without substrate rules

    box = children.bounding_box_for_layer(ref_layer)
    if box.empty():
        raise ValueError("Cannot apply substrate: missing reference layer")

    # 1. Dimensions & implant config
    sub_w = cfg["sub_w"]
    sub_h_raw = max(box.height(), round(cfg["sub_min_area"] / sub_w, 3))
    sub_impl_layer = Layers.pplus if _n_type(model) else Layers.nplus
    impl_enc = 0.16 if model in ("nwell", "pwell") else cfg["impl_enc"]

    # 2. Build a centered substrate stack (no Translated needed)
    def _build_centered_sub():
        sub_rect = Rect(layer=Layers.comp, w=sub_w, h=sub_h_raw)
        sub_impl = Rect(layer=sub_impl_layer, enclose=sub_rect, enl=impl_enc)
        sub_cont = _diffusion_contact_stack(sub_w, sub_h_raw)
        return Linear(align=None, children=[sub_rect, sub_impl, sub_cont])

    # 3. Declarative alignment chain
    chain = []
    spacing = cfg["sub_spacing"]

    if side in ("right", "both"):
        left_sub = _build_centered_sub()
        # Align on comp layer, pull reference point left by spacing
        left_aligned = RefShift(LayerAlign(left_sub, Layers.comp), dx=spacing, dy=0)
        chain.append(left_aligned)

    chain.append(children)  # Resistor core

    if side in ("left", "both"):
        right_sub = _build_centered_sub()
        # Align on comp layer, push reference point right by spacing
        right_aligned = RefShift(LayerAlign(right_sub, Layers.comp), dx=-spacing, dy=0)
        chain.append(right_aligned)

    # 4. Chain horizontally & re-center
    assembly = Linear(align="HC", children=chain)
    return Justify(child=assembly, ref_point="C")

def _apply_nwell_enclosure(children, cfg):
    """Add N WELL enclosure (for pplus diffusion resistors)."""
    if not cfg.get("has_nwell_enc", False):
        return children, bounds

    box = children.bounding_box_for_layer(Layers.comp)
    xmin, ymin, xmax, ymax = box.left, box.bottom, box.right, box.top
    nw_enc = 0.6
    nw_rect = Rect(layer=Layers.nwell,
                   w=(xmax - xmin) + 2 * nw_enc,
                   h=(ymax - ymin) + 2 * nw_enc)
    children.append(Translated(child=nw_rect,
                               trans=kdb.DTrans(kdb.DVector(_snap(xmin - nw_enc),
                                                            _snap(ymin - nw_enc)))))
    return Linear(align=None, children=children)

def _apply_dnwell(children, cfg, model):
    box = children.bounding_box_for_layer(Layers.comp)
    xmin, ymin, xmax, ymax = box.left, box.bottom, box.right, box.top

    if model == "pwell" or (model == "nwell" and True):
        # Pwell always has DNWELL. Nwell gets it when flagged.
        lvp_enc = cfg["lvpwell_enc"]
        dn_enc = cfg["dn_enc"]

        if model == "pwell":
            dn_enc_lvpwell = 2.5
            dn_well = Rect(layer=Layers.dnwell,
                           w=(xmax - xmin) + 2 * dn_enc_lvpwell,
                           h=(ymax - ymin) + 2 * dn_enc_lvpwell)
            dn_offset = kdb.DTrans(kdb.DVector(_snap(xmin - dn_enc_lvpwell), _snap(ymin - dn_enc_lvpwell)))
            children.append(Translated(child=dn_well, trans=dn_offset))
            xmin, ymin = xmin - dn_enc_lvpwell, ymin - dn_enc_lvpwell
            xmax, ymax = xmax + dn_enc_lvpwell, ymax + dn_enc_lvpwell
        else:
            # Nwell: LVPWELL + DNWELL
            children.append(Rect(layer=Layers.lvpwell,
                                 w=(xmax - xmin) + 2 * lvp_enc,
                                 h=(ymax - ymin) + 2 * lvp_enc))
            xmin, ymin = xmin - lvp_enc, ymin - lvp_enc
            xmax, ymax = xmax + lvp_enc, ymax + lvp_enc

            children.append(Rect(layer=Layers.dnwell,
                                 w=(xmax - xmin) + 2 * dn_enc,
                                 h=(ymax - ymin) + 2 * dn_enc))
            xmin, ymin = xmin - dn_enc, ymin - dn_enc
            xmax, ymax = xmax + dn_enc, ymax + dn_enc

    elif _poly(model):
        dn_enc_cmp = 0.5
        children.append(Rect(layer=Layers.dnwell,
                             w=(xmax - xmin) + 2 * dn_enc_cmp,
                             h=(ymax - ymin) + 2 * dn_enc_cmp))
        xmin, ymin = xmin - dn_enc_cmp, ymin - dn_enc_cmp
        xmax, ymax = xmax + dn_enc_cmp, ymax + dn_enc_cmp

    return Linear(align=None, children=children)


def _apply_guard_ring(children, cfg, model):
    box = children.bounding_box_for_layer(Layers.comp)
    xmin, ymin, xmax, ymax = box.left, box.bottom, box.right, box.top
    gr_w = cfg["gr_w"]

    # Adjust inner box based on DNWELL presence to match gdsfactory
    if with_dnwell:
        if model == "pwell":
            enc = 2.5 + 2.5
            xmin, ymin = xmin - enc, ymin - enc
            xmax, ymax = xmax + enc, ymax + enc
        elif model == "nwell":
            enc = cfg["lvpwell_enc"] + cfg["dn_enc"] + 2.5
            xmin, ymin = xmin - enc, ymin - enc
            xmax, ymax = xmax + enc, ymax + enc
        elif _poly(model):
            enc = 0.5 + 2.5
            xmin, ymin = xmin - enc, ymin - enc
            xmax, ymax = xmax + enc, ymax + enc
        elif _diffusion(model):
            enc = cfg["lvpwell_enc"] + cfg["dn_enc"] + 2.5
            xmin, ymin = xmin - enc, ymin - enc
            xmax, ymax = xmax + enc, ymax + enc

    children.append(_make_guard_ring(_snap(xmin), _snap(ymin), _snap(xmax), _snap(ymax), gr_w))
    return Linear(align=None, children=children)


# ====================================================================
# Entry point
# ====================================================================

def make_resistor(
        model, l=1.0, w=1.0,
        with_contacts=True,
        with_substrate=False,
        substrate_side="left",
        guard_ring=False,
        with_dnwell=False,
        n_center_contacts=0,
        contacts=0  # deprecated
        ):
    if model not in resistor_type_map:
        raise ValueError(f"Unknown resistor model: {model!r}. Valid: {res_models}")

    cfg = _get_resistor_cfg(model)
    children = []
    bounds = None

    # 1. Build model-specific core
    if _metal(model):
        m_ext = 0.28
        body = Rect(layer=resistor_type_map[model][2], w=l, h=w, name="body")
        res_layer = Rect(layer=resistor_type_map[model][1], enclose=body, enl_l=m_ext, enl_r=m_ext)
        children = Linear(align=None, children=[body, res_layer])

    elif cfg["custom_terminals"]:
        children = _build_well_core(model, l, w, cfg, with_contacts)

    elif cfg["custom_sab"]:
        children = _build_ppolyf_u_h_core(model, l, w, cfg, with_contacts)

    else:
        children = _build_diff_poly_core(model, l, w, cfg, with_contacts)

    # 2. Sequential peripheral pipeline
    if with_substrate:
        children = _apply_substrate(children, cfg, model, substrate_side)

    if cfg.get("has_nwell_enc", False) == True:
        nwell_enc = Rect(
            enclose=assembly,
            enclose_layer=Layers.comp,
            enl=0.6,
            layer=Layers.nwell)
        children = Linear(align=None, children=[children, nwell_enc])

    if with_dnwell:
        children = _apply_dnwell(children, cfg, model)
    if guard_ring:
        children = _apply_guard_ring(children, cfg, model)

    return children
