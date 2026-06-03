"""
RectFill geometry node for tiled rectangular patterns.

Provides a `RectFill` node that generates a rectangular area filled with a 
centered grid of smaller rectangles. Supports automatic grid calculation with 
DRC-aware clearance enforcement, large-array spacing rules, optional outer 
enclosure layers, and full integration with the `Node` layout hierarchy.

Designed to replace manual `Array`/`Justify`/`Linear` composition patterns with 
a single declarative node.
"""

import pya as kdb
import typing

from .node import Node

class RectFill(Node):
    """
    A rectangular area filled with a centered grid of smaller rectangles.
    
    Auto-calculates optimal grid dimensions based on outer bounds, cell size, 
    spacing, and minimum edge clearance. Supports large-array spacing rules 
    and optional outer enclosure layers.
    
    Args:
        layer: Target layer for the fill cells.
        enclose: Child node to enclose. Mutually exclusive with explicit w/h.
        enclose_pack: If True, targets the child's pack_box() boundary.
        enclose_feature: Feature name to target (default: "*" for all).
        enclose_layer: If set, targets this specific layer's bounding box.
        w, h: Explicit outer dimensions. Required if enclose is None.
        cell_w, cell_h: Width and height of individual fill cells.
        spacing: Gap between adjacent cells (uniform in X and Y).
        edge_clearance: Minimum distance required between cell edges and 
                        the outer boundary. Auto-reduces grid count if violated.
        outer_layer: Optional layer for an enclosing rectangle around the fill grid.
        array_rule_limit: If both nc and nr exceed this threshold, array_spacing is applied.
        array_spacing: Alternate spacing used when the large-array rule triggers.
        halo, halo_x, halo_y, halo_l, halo_r, halo_b, halo_t: Packing clearance.
        name: Feature identifier for feature_box() lookups.
        
    Note:
        - Grid counts are automatically optimized to fit within w/h while 
          respecting edge_clearance.
        - Halos affect pack_box() only and do not change drawn geometry.
    """
    @classmethod
    def from_preset(cls, preset_name: str, w=None, h=None, enclose=None, **kwargs):
        presets = {
            "contact": {
                'layer': Layers.contact, 'outer_layer': Layers.metal1,
                'cell_w': 0.26, 'cell_h': 0.26, 'spacing': 0.26,
                'array_rule_limit': 4, 'array_spacing': 0.36, 'edge_clearance': 0.06
            },
        }
        defaults = presets[preset_name].copy()
        defaults.update(kwargs)
        return cls(w=w, h=h, enclose=enclose, **defaults) 

    def __init__(self, layer: kdb.LayerInfo = None,
                 enclose: Node = None, enclose_pack: bool = False,
                 enclose_feature: str = "*", enclose_layer: kdb.LayerInfo = None,
                 w: float = None, h: float = None,
                 cell_w: float = 1.0, cell_h: float = 1.0,
                 spacing: float = 0.0, edge_clearance: float = 0.0,
                 long_edge_extra_clearance: float = 0.0,
                 outer_layer: kdb.LayerInfo = None, 
                 array_rule_limit: int = 4, array_spacing: float = None,
                 halo: float = 0.0, halo_x: float = 0.0, halo_y: float = 0.0,
                 halo_l: float = 0.0, halo_r: float = 0.0,
                 halo_b: float = 0.0, halo_t: float = 0.0,
                 name: str = ""):

        self.layer = layer
        self.cell_w = cell_w
        self.cell_h = cell_h
        self.edge_clearance = edge_clearance
        self.long_edge_extra_clearance = long_edge_extra_clearance
        self.outer_layer = outer_layer
        self.name = name
        self.spacing = spacing  # Will be updated to array_spacing if rule triggers

        # Aggregate halos
        self.halo_l = halo + halo_x + halo_l
        self.halo_r = halo + halo_x + halo_r
        self.halo_b = halo + halo_y + halo_b
        self.halo_t = halo + halo_y + halo_t

        # Resolve outer boundary
        if enclose is not None:
            fb = self._resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer)
            self.center = fb.center()
            self.w = fb.width()
            self.h = fb.height()
        else:
            if w is None or h is None:
                raise ValueError("Either 'enclose' or 'w'/'h' must be provided for RectFill")
            self.center = kdb.DPoint(0, 0)
            self.w = w
            self.h = h

        # 1. Initial calculation with standard spacing
        if self.w > self.h:
            w_available = self.w - 2 * self.edge_clearance - self.long_edge_extra_clearance
            h_available = self.h - 2 * self.edge_clearance
        else:
            w_available = self.w - 2 * self.edge_clearance
            h_available = self.h - 2 * self.edge_clearance - self.long_edge_extra_clearance

        self.nc = self._calc_grid_count(w_available, self.cell_w, spacing)
        self.nr = self._calc_grid_count(h_available, self.cell_h, spacing)

        # 2. Apply large-array spacing rule
        if array_spacing is not None and self.nc > array_rule_limit and self.nr > array_rule_limit:
            self.nc = self._calc_grid_count(w_available, self.cell_w, array_spacing)
            self.nr = self._calc_grid_count(h_available, self.cell_h, array_spacing)
            self.spacing = array_spacing  # Update effective spacing for geometry

    @staticmethod
    def _resolve_enclose_box(enclose, enclose_pack, enclose_feature, enclose_layer) -> kdb.DBox:
        """Determine the reference box used for enclosure targeting."""
        if enclose_layer is not None:
            fb = enclose.bounding_box_for_layer(enclose_layer)
            if fb.empty():
                raise ValueError(f"Enclosed node has no geometry on layer {enclose_layer}")
            return fb
        elif enclose_pack:
            return enclose.pack_box()
        else:
            return enclose.feature_box(enclose_feature)

    def _calc_grid_count(self, dim: float, cell_size: float, spacing: float) -> int:
        """Calculate optimal grid count for a single dimension with clearance enforcement."""
        avail = dim - 2 * self.edge_clearance
        if avail < cell_size:
            return 0
            
        count = 1 + int((avail - cell_size) // (cell_size + spacing))
            
        return count

    def bounding_box(self) -> kdb.DBox:
        """Returns the absolute outer bounding box."""
        cx, cy = self.center.x, self.center.y
        return kdb.DBox(cx - self.w / 2, cy - self.h / 2,
                        cx + self.w / 2, cy + self.h / 2)

    def bounding_box_for_layer(self, layer) -> kdb.DBox:
        """Returns bounding box only if the queried layer matches this node's layers."""
        cx, cy = self.center.x, self.center.y
        if layer == self.layer:
            # Return bounds of the actual fill grid using effective spacing
            grid_w = self.nc * self.cell_w + max(0, self.nc - 1) * self.spacing
            grid_h = self.nr * self.cell_h + max(0, self.nr - 1) * self.spacing
            return kdb.DBox(cx - grid_w / 2, cy - grid_h / 2,
                            cx + grid_w / 2, cy + grid_h / 2)
        elif layer == self.outer_layer:
            return kdb.DBox(cx - self.w / 2, cy - self.h / 2,
                            cx + self.w / 2, cy + self.h / 2)
        return kdb.DBox()

    def feature_box(self, feature_name: str) -> kdb.DBox:
        """Returns bounding box for wildcard '*' or matching feature name."""
        if feature_name == "*" or feature_name == self.name:
            return self.bounding_box()
        return kdb.DBox()

    def pack_box(self) -> kdb.DBox:
        """Returns the packing boundary including halos. Used by layout managers."""
        bb = self.bounding_box()
        return kdb.DBox(bb.left - self.halo_l, bb.bottom - self.halo_b,
                        bb.right + self.halo_r, bb.top + self.halo_t)

    def produce(self, cell: kdb.Cell, trans: kdb.DTrans):
        """Inserts the fill grid and optional outer enclosure into the target cell."""
        cx, cy = self.center.x, self.center.y
        
        # Calculate grid start position (centered) using effective spacing
        grid_w = self.nc * self.cell_w + max(0, self.nc - 1) * self.spacing
        grid_h = self.nr * self.cell_h + max(0, self.nr - 1) * self.spacing
        start_x = cx - grid_w / 2
        start_y = cy - grid_h / 2

        # Draw fill cells
        if self.layer is not None:
            lidx = cell.layout().layer(self.layer)
            for i in range(self.nc):
                for j in range(self.nr):
                    x = start_x + i * (self.cell_w + self.spacing)
                    y = start_y + j * (self.cell_h + self.spacing)
                    box = kdb.DBox(x, y, x + self.cell_w, y + self.cell_h)
                    cell.shapes(lidx).insert(trans * box)

        # Draw outer enclosure if specified
        if self.outer_layer is not None:
            olidx = cell.layout().layer(self.outer_layer)
            obox = kdb.DBox(cx - self.w / 2, cy - self.h / 2, cx + self.w / 2, cy + self.h / 2)
            cell.shapes(olidx).insert(trans * obox)
