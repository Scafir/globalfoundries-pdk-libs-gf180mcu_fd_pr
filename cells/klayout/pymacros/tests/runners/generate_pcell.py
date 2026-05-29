"""KLayout batch script for PCell GDS generation.

Called via: klayout -b -r generate_pcell.py -rd pymacros_dir=... -rd param_model=rm1 ...

All -rd variables are accessible as global variables in this script.
"""
import os
import sys

import pya

# All -rd variables are available as globals
pymacros_dir = os.path.abspath(pymacros_dir)
sys.path.insert(0, pymacros_dir)

import gf180_pcells

nat_lib = pya.Library()
nat_lib.description = "GF180 Native PCells"
nat_lib.layout().register_pcell("Resistor", gf180_pcells.ResistorPCell())
nat_lib.register(lib_name)

lib = pya.Library.library_by_name(lib_name)
src_layout = lib.layout()
decl = src_layout.pcell_declaration(pcell_name)

if decl is None:
    print(f"ERROR: PCell '{pcell_name}' not found in library '{lib_name}'")
    sys.exit(1)

# Collect params from all param_* globals, coercing types
def _coerce(v):
    if v == "True":
        return True
    if v == "False":
        return False
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except (ValueError, TypeError):
        return v

params = {}
for key in dir(sys.modules[__name__]):
    if key.startswith("param_"):
        param_name = key[6:]
        value = getattr(sys.modules[__name__], key)
        params[param_name] = _coerce(value)

cell_index = src_layout.add_pcell_variant(src_layout.pcell_id(pcell_name), params)
pcell_cell = src_layout.cell(cell_index)

if pcell_cell is None:
    print(f"ERROR: add_pcell_variant failed for {pcell_name}")
    sys.exit(1)

wrapper = src_layout.create_cell("__wrapper__")
wrapper.insert(pya.CellInstArray(pcell_cell.cell_index(), pya.Trans()))
wrapper.flatten(1)

# Export with layer mapping
out_layout = pya.Layout()
out_layout.dbu = src_layout.dbu

layer_map = {}
for li in src_layout.layer_indices():
    info = src_layout.get_info(li)
    new_li = out_layout.layer(pya.LayerInfo(info.layer, info.datatype, info.name))
    layer_map[li] = new_li

out_wrapper = out_layout.create_cell("__wrapper__")
for li in src_layout.layer_indices():
    new_li = layer_map[li]
    for shape in wrapper.each_shape(li):
        if shape.is_box():
            out_wrapper.shapes(new_li).insert(shape.dbox)
        elif shape.is_simple_polygon():
            out_wrapper.shapes(new_li).insert(shape.dsimple_polygon)
        elif shape.is_polygon():
            out_wrapper.shapes(new_li).insert(shape.dpolygon)
        elif shape.is_path():
            out_wrapper.shapes(new_li).insert(shape.dpath)
        elif shape.is_text():
            out_wrapper.shapes(new_li).insert(shape.dtext)

out_layout.write(output_path)
print(f"Exported: {output_path} ({os.path.getsize(output_path)} bytes)")
