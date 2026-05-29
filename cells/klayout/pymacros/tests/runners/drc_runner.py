import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class DRCResult:
    """Result of a DRC run."""
    passed: bool
    violated_rules: Set[str]
    log: str
    report_path: str
    command: str


def run_drc(
    gds_path: str,
    drc_script: str,
    output_dir: str,
) -> DRCResult:
    """Run KLayout DRC and check violations.

    Returns DRCResult with passed=True if no violations found.
    """
    name = Path(gds_path).stem
    report_path = os.path.join(output_dir, f"{name}.drc.lyrdb")
    log_path = os.path.join(output_dir, f"{name}.drc.log")
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "klayout", "-b", "-r", drc_script,
        "-rd", "decks=-density",
        "-rd", f"input={gds_path}",
        "-rd", f"report={report_path}",
    ]

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

    passed = len(violated_rules) == 0

    return DRCResult(
        passed=passed,
        violated_rules=violated_rules,
        log=log,
        report_path=report_path,
        command=" ".join(cmd),
    )
