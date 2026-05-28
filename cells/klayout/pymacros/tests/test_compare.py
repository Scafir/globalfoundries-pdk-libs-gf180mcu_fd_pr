import logging
import os

import pytest

from tests.runners.compare_runner import compare, generate_and_export, generate_golden, generate_golden_gf


def test_pcell_compare(pcell_testcase, pymacros_dir, regenerate, regenerate_gf, output_dir):
    """Compare PCell GDS against golden reference."""
    golden_path = pcell_testcase.golden_path
    actual_path = os.path.join(output_dir, f"{pcell_testcase.name}_native.gds")

    if regenerate:
        ok = generate_golden(
            pymacros_dir,
            "gf180_pcells",
            "Resistor",
            pcell_testcase.nat_params,
            golden_path,
        )
        assert ok, f"Failed to generate golden for {pcell_testcase.name}"
        pytest.skip("Golden regenerated")

    if regenerate_gf:
        if pcell_testcase.reference == "pcell":
            pytest.skip(f"Gdsfactory does not match for {pcell_testcase.name} (reference=pcell)")
        ok = generate_golden_gf(
            pcell_testcase.nat_params,
            golden_path,
        )
        assert ok, f"Failed to generate gdsfactory golden for {pcell_testcase.name}"
        pytest.skip("Gdsfactory golden regenerated")

    if not os.path.exists(golden_path):
        assert False, f"No golden found: {golden_path} (run with --regenerate or --regenerate-gf to create)"

    ok = generate_and_export(
        pymacros_dir,
        "gf180_pcells",
        "Resistor",
        pcell_testcase.nat_params,
        actual_path,
    )
    assert ok, f"Failed to generate GDS for {pcell_testcase.name}"

    passed, diffs = compare(actual_path, golden_path)
    assert passed, (
        f"GDS mismatch for {pcell_testcase.name}:\n" + "\n".join(diffs)
    )
