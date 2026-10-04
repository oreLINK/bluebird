"""Step reports: what each unit of a run (source, dataset, KPI, massif) achieved.

Every layer records one :class:`StepReport` per unit. A local run keeps them in
memory; in CI each job writes its report to a JSON file (``bluebird run
--report``) and the status job merges them into ``diamond/status.json``.

States, from best to worst:

- ``ok``      fresh data, complete;
- ``partial`` fresh data, but some stations are missing;
- ``stale``   the data shown comes from an earlier run;
- ``down``    nothing available.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

State = Literal["ok", "partial", "stale", "down"]
Layer = Literal["bronze", "silver", "gold", "diamond"]

SEVERITY: dict[State, int] = {"ok": 0, "partial": 1, "stale": 2, "down": 3}


def worst(states: Iterable[State], default: State = "down") -> State:
    """The most degraded state of ``states`` (``default`` when empty)."""
    ranked = sorted(states, key=SEVERITY.__getitem__)
    return ranked[-1] if ranked else default


def coverage_state(ok: int, expected: int) -> State:
    """``ok`` when every expected item is there, ``partial`` when some, else ``down``."""
    if ok <= 0:
        return "down"
    return "ok" if ok >= expected else "partial"


class StepReport(BaseModel):
    """Outcome of one unit of one layer."""

    model_config = ConfigDict(extra="forbid")

    layer: Layer
    id: str
    state: State
    ok: int | None = None
    expected: int | None = None
    message: str | None = None


class ReportFile(BaseModel):
    """The JSON written by ``bluebird run --report``."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    run_date: date
    steps: list[StepReport]


def read_reports(directory: Path) -> list[StepReport]:
    """Every step of every ``*.json`` report under ``directory`` (recursively)."""
    steps: list[StepReport] = []
    if not directory.is_dir():
        return steps
    for path in sorted(directory.rglob("*.json")):
        steps.extend(ReportFile.model_validate_json(path.read_text(encoding="utf-8")).steps)
    return steps
