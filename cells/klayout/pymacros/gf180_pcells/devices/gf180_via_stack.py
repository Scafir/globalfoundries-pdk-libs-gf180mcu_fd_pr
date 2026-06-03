"""
GF180-specific via stack configuration and convenience class.
"""
import pya as kdb
from ..core.via_stack import ViaStack, ViaStackTech
from ..tech.gf180_layers import Layers

metal_via_rule = {
        'cell_w': 0.26, 'cell_h': 0.26,
        'spacing': 0.26,
        'edge_clearance': 0.06,
        'array_rule_limit': 4,
        'array_spacing': 0.36
    }

# DRC rules per via type
_GF180_VIA_RULES = {
    Layers.contact: {
        'cell_w': 0.22, 'cell_h': 0.22,
        'spacing': 0.25,
        'edge_clearance': 0.07,
        'array_rule_limit': 4,
        'array_spacing': 0.28
    },
    Layers.via1: metal_via_rule,
    Layers.via2: metal_via_rule,
    Layers.via3: metal_via_rule,
    Layers.via4: metal_via_rule,
    Layers.via5: metal_via_rule
}

_GF180_STACK = ViaStackTech(
    conductors=(Layers.comp, Layers.metal1, Layers.metal2, Layers.metal3,
                Layers.metal4, Layers.metal5, Layers.metaltop),
    vias=(Layers.contact, Layers.via1, Layers.via2, Layers.via3,
          Layers.via4, Layers.via5),
    via_rules=_GF180_VIA_RULES,
    well_paths={
        "nwell": (Layers.nplus, Layers.nwell),
        "pwell": (Layers.pplus, Layers.lvpwell)
    },
    well_offsets={
        Layers.nplus: 0.24,   # 0.24μm nplus enclosure
        Layers.nwell: 0.50,   # 0.50μm nwell enclosure
        Layers.pplus: 0.24,   # 0.24μm pplus enclosure
        Layers.lvpwell: 0.50  # 0.50μm lvpwell enclosure
    },
    #exclusive_groups=[(Layers.nwell, Layers.lvpwell), (Layers.nplus, Layers.pplus)]
)



class GF180ViaStack(ViaStack):
    """Convenience wrapper for GF180 via stacks."""
    def __init__(self, w: float, h: float, from_layer: kdb.LayerInfo, 
                 to_layer: kdb.LayerInfo, **kwargs):
        super().__init__(
            w=w, h=h, 
            from_layer=from_layer, to_layer=to_layer,
            tech=_GF180_STACK,
            **kwargs
        )
