#!/usr/bin/env python3
"""Day 2026-09-17 — CCT2x Dose-Adaptive Cognitive Training Planner (GVU).

Generator: drafts a 7-day computerized cognitive training (CCT) plan.
Verifier: checks Jeong et al. 2025 CCT2x success criteria (falsifiable).
Updater: feeds critique back for 3 passes and logs score trajectory.

Success criterion (all must hold):
  1. sessions >= 24 planned-equivalent intensity units over the week
     (session_minutes / 30 * intensity_multiplier; 2x sessions count 2.0)
  2. each session duration > 30 minutes
  3. at least 3 cognitive domains covered (global, episodic, working, attention, executive)
  4. dual-task or speed-of-processing present at least twice (ACTIVE/BrainHQ signal)
  5. aversion-safe: no session framed as 'test/exam/diagnosis'; max 1 high-frustration drill
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from typing import Any


DOMAINS = ("global", "episodic", "working", "attention", "executive")
FRUSTRATION_DRILLS = {"nback-hard", "stroop-punitive", "exam-battery"}


@dataclass
class Session:
    day: int
    minutes: int
    intensity: float  # 1.0 = CCT, 2.0 = CCT2x
    domain: str
    drill: str
    framing: str  # "practice" | "game" | "test" | "exam"


@dataclass
class Plan:
    sessions: list[Session] = field(default_factory=list)
    notes: str = ""

    def intensity_units(self) -> float:
        return sum((s.minutes / 30.0) * s.intensity for s in self.sessions)


def generate(critique: str | None, prior: Plan | None) -> Plan:
    """Generator: produce or revise a weekly CCT plan."""
    if prior is None:
        return Plan(
            sessions=[
                Session(1, 20, 1.0, "working", "nback-hard", "test"),
                Session(3, 25, 1.0, "working", "digit-span", "exam"),
                Session(5, 20, 1.0, "working", "stroop-punitive", "test"),
            ],
            notes="short working-memory drills",
        )

    plan = deepcopy(prior)
    c = (critique or "").lower()

    if "duration" in c or "30" in c:
        for s in plan.sessions:
            if s.minutes <= 30:
                s.minutes = 35

    if "intensity" in c or "24" in c or "units" in c:
        for s in plan.sessions:
            s.intensity = 2.0
            if s.minutes < 55:
                s.minutes = 55
        existing_days = {s.day for s in plan.sessions}
        extras = [
            Session(2, 55, 2.0, "episodic", "story-recall-game", "practice"),
            Session(4, 55, 2.0, "attention", "ufov-speed", "game"),
            Session(6, 55, 2.0, "executive", "dual-task-walk-tap", "practice"),
            Session(7, 55, 2.0, "global", "mixed-circuit", "game"),
        ]
        for e in extras:
            if e.day not in existing_days:
                plan.sessions.append(e)
        plan.sessions.sort(key=lambda s: s.day)

    if "domain" in c:
        used = {s.domain for s in plan.sessions}
        for i, d in enumerate(DOMAINS):
            if d not in used and i < len(plan.sessions):
                plan.sessions[i].domain = d

    if "dual-task" in c or "speed" in c:
        if not any("dual" in s.drill or "speed" in s.drill or "ufov" in s.drill for s in plan.sessions):
            plan.sessions.append(Session(4, 35, 2.0, "attention", "ufov-speed", "game"))
            plan.sessions.append(Session(6, 40, 2.0, "executive", "dual-task-walk-tap", "practice"))
        plan.sessions.sort(key=lambda s: s.day)

    if "aversion" in c or "framing" in c or "frustration" in c:
        for s in plan.sessions:
            if s.framing in ("test", "exam"):
                s.framing = "practice"
            if s.drill in FRUSTRATION_DRILLS:
                s.drill = "adaptive-span-game"

    plan.notes = f"revised after: {critique[:80] if critique else 'init'}"
    return plan


def verify(plan: Plan) -> dict[str, Any]:
    reasons: list[str] = []
    units = plan.intensity_units()
    if units < 24:
        reasons.append(f"intensity units {units:.2f} < 24")
    short = [s.day for s in plan.sessions if s.minutes <= 30]
    if short:
        reasons.append(f"duration <=30 on days {short}")
    domains = {s.domain for s in plan.sessions if s.domain in DOMAINS}
    if len(domains) < 3:
        reasons.append(f"only {len(domains)} domains covered: {sorted(domains)}")
    speedish = sum(
        1 for s in plan.sessions if any(k in s.drill for k in ("dual", "speed", "ufov"))
    )
    if speedish < 2:
        reasons.append(f"dual-task/speed sessions={speedish} < 2")
    test_framed = [s.day for s in plan.sessions if s.framing in ("test", "exam")]
    if test_framed:
        reasons.append(f"aversion framing test/exam on days {test_framed}")
    frustrate = [s.day for s in plan.sessions if s.drill in FRUSTRATION_DRILLS]
    if len(frustrate) > 1:
        reasons.append(f"high-frustration drills on days {frustrate}")

    passed = len(reasons) == 0
    return {
        "pass": passed,
        "reasons": reasons if reasons else ["all CCT2x + aversion-safe criteria met"],
        "units": round(units, 3),
        "domains": sorted(domains),
        "n_sessions": len(plan.sessions),
    }


def updater(n_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    plan: Plan | None = None
    critique: str | None = None
    for i in range(1, n_passes + 1):
        plan = generate(critique, plan)
        result = verify(plan)
        entry = {
            "pass": i,
            "plan": [asdict(s) for s in plan.sessions],
            "notes": plan.notes,
            "verify": result,
        }
        log.append(entry)
        if result["pass"]:
            break
        critique = "; ".join(result["reasons"])
    return log


def main() -> None:
    log = updater(3)
    print("=== GVU CCT2x planner smoke test ===")
    for entry in log:
        v = entry["verify"]
        status = "PASS" if v["pass"] else "FAIL"
        print(f"\nPass {entry['pass']}: {status} units={v['units']} domains={v['domains']}")
        print(f"  sessions={entry['plan']}")
        print(f"  reasons={v['reasons']}")
    before = log[0]["verify"]
    after = log[-1]["verify"]
    print("\n--- before/after ---")
    print(f"before: pass={before['pass']} units={before['units']} reasons={before['reasons']}")
    print(f"after:  pass={after['pass']} units={after['units']} reasons={after['reasons']}")
    with open("smoke_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print("wrote smoke_log.json")


if __name__ == "__main__":
    main()
