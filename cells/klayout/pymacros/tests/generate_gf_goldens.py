"""Generate gdsfactory golden GDS files for resistor test cases."""

import argparse
import inspect
import os
import sys
from pathlib import Path

import yaml

# Ensure project root is in sys.path so 'cells' package is discoverable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from cells import draw_res

def main():
    parser = argparse.ArgumentParser(description="Generate gdsfactory golden GDS files")
    parser.add_argument(
        "--cases-file",
        default="tests/goldens/resistors/cases.yaml",
        help="Path to cases.yaml",
    )
    parser.add_argument(
        "--output-dir",
        default="tests/goldens/resistors",
        help="Output directory for golden GDS files",
    )
    args = parser.parse_args()


    # Centralized mapping: model name -> draw function
    MODEL_DRAW_MAP = {
        "nplus_s": draw_res.draw_nplus_res,
        "nplus_u": draw_res.draw_nplus_res,
        "pplus_s": draw_res.draw_pplus_res,
        "pplus_u": draw_res.draw_pplus_res,
        "npolyf_s": draw_res.draw_npolyf_res,
        "npolyf_u": draw_res.draw_npolyf_res,
        "ppolyf_s": draw_res.draw_ppolyf_res,
        "ppolyf_u": draw_res.draw_ppolyf_res,
        "ppolyf_u_h": draw_res.draw_ppolyf_u_high_Rs_res,
        "nwell": draw_res.draw_well_res,
        "pwell": draw_res.draw_well_res,
        # Metal resistors can be added here when draw functions are available
        "rm1": draw_res.draw_metal_res,
        "rm2": draw_res.draw_metal_res,
        "rm3": draw_res.draw_metal_res,
    }

    # YAML key -> PCell parameter translation
    KEY_TRANSLATION = {
        "name": "name",
        "l": "l_res",
        "w": "w_res",
        "model": "res_type",
        "guard_ring": "pcmpgr",
        "with_dnwell": "deepnwell",
    }

    with open(args.cases_file) as f:
        cases = yaml.safe_load(f)

    for case in cases:
        name = case["name"]
        model = case["model"]

        draw_func = MODEL_DRAW_MAP.get(model)
        if draw_func is None:
            raise ValueError(f"Unknown model: {model}")

        kwargs = {}
        for k, v in case.items():
            if k not in KEY_TRANSLATION:
                raise ValueError(
                    f"Unknown YAML key '{k}' in case '{case['name']}'. "
                )
            kwargs[KEY_TRANSLATION[k]] = v

        kwargs.pop('name')

        if model == 'ppolyf_u_h':
            kwargs.pop('res_type')

        c = draw_func(**kwargs)
        output_path = os.path.join(args.output_dir, f"{name}_ref.gds")
        c.write_gds(output_path)
        print(f"  OK   {name} -> {os.path.basename(output_path)}")

if __name__ == "__main__":
    main()
