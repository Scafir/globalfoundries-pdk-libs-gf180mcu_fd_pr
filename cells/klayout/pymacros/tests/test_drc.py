import logging
import os

import pytest

from tests.runners.compare_runner import generate_and_export
from tests.runners.drc_runner import run_drc


def test_pcell_drc(pcell_testcase, pymacros_dir, drc_script_path, output_dir):
    """Run KLayout DRC on native PCell GDS and check for unexpected violations."""
    gds_path = pcell_testcase.generated_gds_path(output_dir)

    ok = generate_and_export(
        pymacros_dir,
        "gf180_pcells",
        "Resistor",
        pcell_testcase.nat_params,
        gds_path,
    )
    assert ok, f"Failed to generate GDS for DRC: {pcell_testcase.name}"

    result = run_drc(gds_path, drc_script_path, pcell_testcase.model, output_dir)

    if not result.passed:
        logging.error(
            "DRC unexpected violations for %s: %s",
            pcell_testcase.name,
            result.unexpected_rules,
        )

    assert result.passed, (
        f"DRC unexpected violations for {pcell_testcase.name}: "
        f"{result.unexpected_rules}\n"
        f"Violated: {result.violated_rules}\n"
        f"Known: {result.known_rules}\n"
        f"Command: {result.command}"
    )
