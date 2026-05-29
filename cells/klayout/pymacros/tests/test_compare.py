import os

from tests.runners.compare_runner import compare, generate_and_export


def test_pcell_compare(pcell_testcase, pymacros_dir, output_dir):
    """Compare PCell GDS against golden reference."""
    golden_path = pcell_testcase.golden_path
    actual_path = os.path.join(output_dir, f"{pcell_testcase.name}_native.gds")

    if not os.path.exists(golden_path):
        assert False, f"No golden found: {golden_path}"

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
