#!/usr/bin/env python3
"""
Day 2026-09-22 — GVU prototype
Opportunity: ACTIVE-style speed-of-processing booster planner.

Generator drafts a 20-year-inspired cognitive-speed training plan.
Verifier checks an explicit ACTIVE-booster heuristic.
Updater feeds the critique back for 3 passes.

Success criterion (falsifiable):
  PASS iff ALL of:
    - initial_weeks >= 5 and initial_weeks <= 8
    - sessions_per_week in {3, 4, 5}
    - session_minutes in [10, 20]
    - booster_sessions >= 4
    - booster_gap_months in [11, 36]
    - dual_task_levels >= 3 (increasing visual-search difficulty)
    - framing != "test" (must be game/practice, not exam)
    - total_hours in [4.0, 12.0]
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Plan:
    initial_weeks: int
    sessions_per_week: int
    session_minutes: int
    booster_sessions: int
    booster_gap_months: int
    dual_task_levels: int
    framing: str
    notes: str

    @property
    def total_hours(self) -> float:
        initial = self.initial_weeks * self.sessions_per_week * self.session_minutes / 60.0
        booster = self.booster_sessions * self.session_minutes / 60.0
        return round(initial + booster, 2)


def generate(critique: str | None, prior: Plan | None) -> Plan:
    """Generator: naive first draft, then apply verifier critique."""
    if prior is None:
        return Plan(
            initial_weeks=2,
            sessions_per_week=2,
            session_minutes=8,
            booster_sessions=0,
            booster_gap_months=6,
            dual_task_levels=1,
            framing="test",
            notes="Quick UFOV-like screen; no boosters.",
        )

    plan = deepcopy(prior)
    text = (critique or "").lower()

    if "initial_weeks" in text or "weeks" in text:
        plan.initial_weeks = max(plan.initial_weeks, 6)
    if "sessions_per_week" in text or "frequency" in text:
        plan.sessions_per_week = 4
    if "session_minutes" in text or "duration" in text:
        plan.session_minutes = 15
    if "booster_sessions" in text or "booster" in text:
        plan.booster_sessions = max(plan.booster_sessions, 5)
    if "booster_gap" in text or "gap" in text:
        plan.booster_gap_months = 18
    if "dual_task" in text or "levels" in text:
        plan.dual_task_levels = max(plan.dual_task_levels, 4)
    if "framing" in text or "test" in text:
        plan.framing = "game"
    if "total_hours" in text:
        plan.session_minutes = max(plan.session_minutes, 15)
        plan.initial_weeks = max(plan.initial_weeks, 6)

    plan.notes = "Revised from verifier critique: ACTIVE booster protocol."
    return plan


def verify(plan: Plan) -> dict[str, Any]:
    reasons: list[str] = []
    if not (5 <= plan.initial_weeks <= 8):
        reasons.append(f"initial_weeks={plan.initial_weeks} not in [5,8]")
    if plan.sessions_per_week not in {3, 4, 5}:
        reasons.append(f"sessions_per_week={plan.sessions_per_week} not in {{3,4,5}}")
    if not (10 <= plan.session_minutes <= 20):
        reasons.append(f"session_minutes={plan.session_minutes} not in [10,20]")
    if plan.booster_sessions < 4:
        reasons.append(f"booster_sessions={plan.booster_sessions} < 4")
    if not (11 <= plan.booster_gap_months <= 36):
        reasons.append(f"booster_gap_months={plan.booster_gap_months} not in [11,36]")
    if plan.dual_task_levels < 3:
        reasons.append(f"dual_task_levels={plan.dual_task_levels} < 3")
    if plan.framing == "test":
        reasons.append("framing=test (must be game/practice)")
    if not (4.0 <= plan.total_hours <= 12.0):
        reasons.append(f"total_hours={plan.total_hours} not in [4.0,12.0]")

    passed = len(reasons) == 0
    return {
        "pass": passed,
        "reason": "OK — matches ACTIVE booster heuristic" if passed else "; ".join(reasons),
        "plan": asdict(plan) | {"total_hours": plan.total_hours},
    }


def run_gvu(max_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    plan: Plan | None = None
    critique: str | None = None
    for i in range(1, max_passes + 1):
        plan = generate(critique, plan)
        result = verify(plan)
        log.append({"pass": i, **result})
        if result["pass"]:
            break
        critique = result["reason"]
    return log


if __name__ == "__main__":
    print("=== Smoke test: ACTIVE speed-training booster planner ===")
    for row in run_gvu():
        status = "PASS" if row["pass"] else "FAIL"
        print(f"\nPass {row['pass']}  {status}")
        print(f"  reason : {row['reason']}")
        print(f"  plan   : {row['plan']}")
