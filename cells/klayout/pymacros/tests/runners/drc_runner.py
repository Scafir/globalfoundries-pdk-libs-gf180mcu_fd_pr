import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


# Per-device-type known violations (standalone cells without full chip context)
KNOWN_VIOLATIONS: Dict[str, Set[str]] = {
    # Metal resistor: no poly, no metal2-5, no metaltop
    "rm1": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "rm2": {"M1.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "rm3": {"M1.4", "M2.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "tm6k": {"M1.4", "M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "tm9k": {"M1.4", "M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "tm11k": {"M1.4", "M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "tm30k": {"M1.4", "M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    # Diffusion: no metal2-5, metaltop, poly
    "nplus_s": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "nplus_u": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "pplus_s": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "pplus_u": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    # Poly: no metal2-5, metaltop
    "npolyf_s": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3"},
    "ppolyf_s": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3"},
    "npolyf_u": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3"},
    "ppolyf_u": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3"},
    "ppolyf_u_h": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3"},
    # Well: no metal2-5, metaltop, poly
    "nwell": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
    "pwell": {"M2.4", "M3.4", "M4.4", "M5.4", "MT.3", "PL.8"},
}


@dataclass
class DRCResult:
    """Result of a DRC run."""
    passed: bool
    violated_rules: Set[str]
    unexpected_rules: Set[str]
    known_rules: Set[str]
    log: str
    report_path: str
    command: str


def run_drc(
    gds_path: str,
    drc_script: str,
    model: str,
    output_dir: str,
    skip_density: bool = True,
) -> DRCResult:
    """Run KLayout DRC and check violations against known-violations list.

    Returns DRCResult with passed=True if no unexpected violations found.
    """
    name = Path(gds_path).stem
    report_path = os.path.join(output_dir, f"{name}.drc.lyrdb")
    log_path = os.path.join(output_dir, f"{name}.drc.log")
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "klayout", "-b", "-r", drc_script,
        "-rd", f"input={gds_path}",
        "-rd", f"report={report_path}",
    ]

    if skip_density:
        cmd.extend(["-rd", "decks=-density"])

    logger.info("DRC: %s -> %s", name, os.path.basename(report_path))
    logger.debug("Command: %s", " ".join(cmd))

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    log_lines = []
    for line in proc.stdout or []:
        log_lines.append(line)
        logger.debug(line.rstrip())

    proc.wait()
    log = "".join(log_lines)

    # Parse violations from stdout
    violated_rules: Set[str] = set()
    for line in log_lines:
        stripped = line.strip()
        if stripped.startswith("'") and "'s)" in stripped:
            rule = stripped.split("'")[1]
            violated_rules.add(rule)

    known = KNOWN_VIOLATIONS.get(model, set())
    unexpected = violated_rules - known

    passed = len(unexpected) == 0

    return DRCResult(
        passed=passed,
        violated_rules=violated_rules,
        unexpected_rules=unexpected,
        known_rules=known,
        log=log,
        report_path=report_path,
        command=" ".join(cmd),
    )
