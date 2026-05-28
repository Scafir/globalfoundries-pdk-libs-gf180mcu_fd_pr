import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import pytest
import yaml


@dataclass
class PCellTestCase:
    """A single PCell test case discovered from a cases.yaml file."""
    name: str
    pcell_type: str
    model: str
    l: float
    w: float
    goldens_dir: str
    extra_params: Dict = field(default_factory=dict)

    @property
    def golden_path(self) -> str:
        return os.path.join(self.goldens_dir, f"{self.name}_ref.gds")

    @property
    def nat_params(self) -> Dict:
        params = {"model": self.model, "l": self.l, "w": self.w, "contacts": 0}
        params.update(self.extra_params)
        return params


def pytest_addoption(parser):
    parser.addoption(
        "--drc-script-path",
        action="store",
        default="../globalfoundries-pdk-libs-gf180mcu_fd_pv/klayout/drc/gf180mcu.drc",
        help="Path to the KLayout DRC script",
    )
    parser.addoption(
        "--pymacros-dir",
        action="store",
        default=None,
        help="Path to the pymacros directory (default: auto-detected from conftest location)",
    )
    parser.addoption(
        "--regenerate",
        action="store_true",
        default=False,
        help="Regenerate golden GDS files instead of comparing",
    )
    parser.addoption(
        "--output-dir",
        action="store",
        default="test_output",
        help="Directory for test outputs",
    )
    parser.addoption(
        "--goldens-dir",
        action="store",
        default="tests/goldens",
        help="Root directory containing golden files and cases.yaml",
    )


def pytest_generate_tests(metafunc):
    if "pcell_testcase" not in metafunc.fixturenames:
        return

    goldens_root = Path(metafunc.config.getoption("--goldens-dir"))
    testcases: List[PCellTestCase] = []

    # Scan all cases.yaml files under goldens_root
    for cases_file in sorted(goldens_root.rglob("cases.yaml")):
        pcell_type = cases_file.parent.name
        with open(cases_file) as f:
            cases = yaml.safe_load(f) or []

        for case in cases:
            tc = PCellTestCase(
                name=case["name"],
                pcell_type=pcell_type,
                model=case["model"],
                l=case["l"],
                w=case["w"],
                goldens_dir=str(cases_file.parent),
                extra_params=case.get("extra", {}),
            )
            testcases.append(tc)

    metafunc.parametrize("pcell_testcase", testcases, ids=[tc.name for tc in testcases])


@pytest.fixture(scope="session")
def drc_script_path(request) -> str:
    return request.config.getoption("--drc-script-path")


@pytest.fixture(scope="session")
def pymacros_dir(request) -> Path:
    path = request.config.getoption("--pymacros-dir")
    if path is None:
        path = Path(__file__).resolve().parent.parent
    else:
        path = Path(path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path
    return path.resolve()


@pytest.fixture(scope="session")
def regenerate(request) -> bool:
    return request.config.getoption("--regenerate")


@pytest.fixture(scope="session")
def output_dir(request) -> str:
    path = request.config.getoption("--output-dir")
    os.makedirs(path, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
