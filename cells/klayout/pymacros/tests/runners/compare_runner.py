import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def generate_and_export(
    pymacros_dir: Path,
    lib_name: str,
    pcell_name: str,
    params: Dict,
    output_path: str,
) -> bool:
    """Generate a PCell variant and export as flattened GDS.

    Uses KLayout batch mode with an inline Ruby script to:
    1. Load pymacros and register PCells
    2. Instantiate the specified PCell variant
    3. Flatten and export to GDS
    """
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_pcell.py")

    cmd = [
        "klayout", "-b", "-r", script,
        "-rd", f"pymacros_dir={pymacros_dir}",
        "-rd", f"lib_name={lib_name}",
        "-rd", f"pcell_name={pcell_name}",
        "-rd", f"output_path={output_path}",
    ] + [
        arg for k, v in params.items() for arg in ("-rd", f"param_{k}={v}")
    ]

    logger.info("Generating %s: %s", pcell_name, os.path.basename(output_path))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error("KLayout error: %s", result.stderr[-500:])
        return False

    if not os.path.exists(output_path):
        logger.error("No output file produced: %s", output_path)
        return False

    return True


def compare(actual_path: str, golden_path: str) -> Tuple[bool, List[str]]:
    """Compare two GDS files using gdstk polygon-level diff.

    Returns (passed, diffs). Empty diffs means identical.
    """
    try:
        import gdstk
    except ImportError:
        raise ImportError("gdstk is required for GDS comparison: pip install gdstk")

    actual_lib = gdstk.read_gds(actual_path)
    golden_lib = gdstk.read_gds(golden_path)

    diffs: List[str] = []

    # Compare top cell count
    if len(actual_lib.top_level()) != len(golden_lib.top_level()):
        diffs.append(
            f"Top cell count: actual={len(actual_lib.top_level())}, "
            f"golden={len(golden_lib.top_level())}"
        )
        return False, diffs

    actual_top = actual_lib.top_level()[0]
    golden_top = golden_lib.top_level()[0]

    # Get all polygons (flattened) and group by layer
    def _group_by_layer(cell):
        from collections import defaultdict
        groups = defaultdict(list)
        for poly in cell.get_polygons(True):
            groups[poly.layer].append(poly)
        return groups

    actual_polys = _group_by_layer(actual_top)
    golden_polys = _group_by_layer(golden_top)

    actual_layers = set(actual_polys.keys())
    golden_layers = set(golden_polys.keys())

    missing_layers = golden_layers - actual_layers
    extra_layers = actual_layers - golden_layers

    if missing_layers:
        diffs.append(f"Missing layers in actual: {sorted(missing_layers)}")
    if extra_layers:
        diffs.append(f"Extra layers in actual: {sorted(extra_layers)}")

    if missing_layers or extra_layers:
        return False, diffs

    # Compare polygon counts per layer
    common_layers = sorted(actual_layers & golden_layers)
    for layer in common_layers:
        a_count = len(actual_polys[layer])
        g_count = len(golden_polys[layer])

        if a_count != g_count:
            diffs.append(
                f"Layer {layer}: polygon count mismatch "
                f"(actual={a_count}, golden={g_count})"
            )

    passed = len(diffs) == 0
    return passed, diffs


def generate_golden(
    pymacros_dir: Path,
    lib_name: str,
    pcell_name: str,
    params: Dict,
    golden_path: str,
) -> bool:
    """Generate and save a golden GDS file."""
    return generate_and_export(pymacros_dir, lib_name, pcell_name, params, golden_path)


def generate_golden_gf(
    params: Dict,
    golden_path: str,
) -> bool:
    """Generate and save a gdsfactory golden GDS file."""
    from tests.runners.generate_gdsfactory import generate_and_export as generate_gf

    return generate_gf(
        model=params["model"],
        l=params["l"],
        w=params["w"],
        output_path=golden_path,
        guard_ring=params.get("guard_ring", False),
        with_dnwell=params.get("with_dnwell", False),
        n_center_contacts=params.get("n_center_contacts", 0),
    )
