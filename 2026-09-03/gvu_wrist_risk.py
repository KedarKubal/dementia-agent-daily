#!/usr/bin/env python3
"""
Day 2026-09-03 — Wrist-sensor dementia incident-risk flag
Generator–Verifier–Updater (GVU) loop.

Insight prototyped (Brodie et al., Int Psychogeriatr 2025 / Watch Walk–UK Biobank):
slower maximal walking speed, lower running duration, and earlier bedtime
from wrist accelerometry independently predict incident dementia.

This is a scaled-down, rule-based slice — no model weights, no PHI.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List


WALK_HIGH_RISK_MPS = 1.05
WALK_MED_RISK_MPS = 1.25
RUN_HIGH_RISK_MIN = 5.0
RUN_MED_RISK_MIN = 20.0
BED_EARLY_HIGH = 150
BED_EARLY_MED = 180


@dataclass
class WristSample:
    person_id: str
    max_walk_mps: float
    run_min_week: float
    bedtime_min_past_18: float
    steps_day: float
    step_time_cv: float


@dataclass
class RiskDraft:
    person_id: str
    walk_score: float
    run_score: float
    bed_score: float
    composite: float
    band: str
    rationale: str
    pass_n: int


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def generate(sample: WristSample, critique: str = "", pass_n: int = 1) -> RiskDraft:
    walk_score = clamp01((WALK_MED_RISK_MPS - sample.max_walk_mps) / 0.40)
    run_score = clamp01((RUN_MED_RISK_MIN - sample.run_min_week) / RUN_MED_RISK_MIN)
    bed_score = clamp01((BED_EARLY_MED - sample.bedtime_min_past_18) / 90.0)

    if pass_n == 1 and not critique:
        composite = 0.80 * walk_score + 0.10 * run_score + 0.10 * bed_score
        rationale = (
            f"Pass1 draft used walk-heavy mix (0.80/0.10/0.10). "
            f"walk={sample.max_walk_mps:.2f} m/s run={sample.run_min_week:.1f} min "
            f"bed+18={sample.bedtime_min_past_18:.0f}m."
        )
    else:
        cv_bump = clamp01((sample.step_time_cv - 0.08) / 0.12) * 0.08
        composite = 0.38 * walk_score + 0.31 * run_score + 0.31 * bed_score + cv_bump
        composite = clamp01(composite)
        rationale = (
            f"Revised mix after critique: walk/run/bed 0.38/0.31/0.31 + cv_bump={cv_bump:.2f}. "
            f"critique={critique[:160]}"
        )

    if composite >= 0.62:
        band = "high"
    elif composite >= 0.38:
        band = "medium"
    else:
        band = "low"

    return RiskDraft(
        person_id=sample.person_id,
        walk_score=round(walk_score, 3),
        run_score=round(run_score, 3),
        bed_score=round(bed_score, 3),
        composite=round(composite, 3),
        band=band,
        rationale=rationale,
        pass_n=pass_n,
    )


def verify(draft: RiskDraft, sample: WristSample) -> dict:
    """Falsifiable verifier: triple-risk must be high; walk must not dominate after pass 1."""
    reasons: List[str] = []
    ok = True

    if not (0.0 <= draft.composite <= 1.0):
        ok = False
        reasons.append("composite out of [0,1]")
    if draft.band not in {"low", "medium", "high"}:
        ok = False
        reasons.append("invalid band")

    triple_high = (
        sample.max_walk_mps < WALK_HIGH_RISK_MPS
        and sample.run_min_week < RUN_HIGH_RISK_MIN
        and sample.bedtime_min_past_18 < BED_EARLY_HIGH
    )
    if triple_high and draft.band != "high":
        ok = False
        reasons.append(
            "triple paper-risk (slow walk + almost no running + early bed) "
            f"must be high, got {draft.band}"
        )

    triple_low = (
        sample.max_walk_mps >= 1.40
        and sample.run_min_week >= 40.0
        and sample.bedtime_min_past_18 > 210
    )
    if triple_low and draft.band != "low":
        ok = False
        reasons.append(f"triple protective profile must be low, got {draft.band}")

    s = draft.walk_score + draft.run_score + draft.bed_score
    walk_share = draft.walk_score / s if s > 0 else 1.0
    if draft.pass_n >= 2 and walk_share > 0.55 and not triple_high:
        ok = False
        reasons.append(f"walk_share={walk_share:.2f} > 0.55; paper requires co-predictors")

    if draft.pass_n == 1 and "walk-heavy" in draft.rationale:
        ok = False
        reasons.append(
            "pass1 used walk-heavy mix; include running duration and bedtime "
            "as independent predictors (Brodie 2025)"
        )

    if ok and not reasons:
        reasons.append("all explicit criteria passed")

    return {
        "pass": ok,
        "reasons": reasons,
        "walk_share": round(walk_share, 3),
        "triple_high": triple_high,
        "triple_low": triple_low,
    }


def updater(sample: WristSample, max_passes: int = 3) -> List[dict]:
    log: List[dict] = []
    critique = ""
    for n in range(1, max_passes + 1):
        draft = generate(sample, critique=critique, pass_n=n)
        verdict = verify(draft, sample)
        log.append({"pass": n, "draft": asdict(draft), "verify": verdict})
        if verdict["pass"]:
            break
        critique = "; ".join(verdict["reasons"])
    return log


def main() -> None:
    sample = WristSample(
        person_id="smoke-ukb-like-01",
        max_walk_mps=0.98,
        run_min_week=2.0,
        bedtime_min_past_18=135,
        steps_day=3200,
        step_time_cv=0.16,
    )
    log = updater(sample, max_passes=3)
    print(json.dumps({"sample": asdict(sample), "loop": log}, indent=2))
    final = log[-1]
    print(
        "\nSMOKE:",
        f"passes={len(log)}",
        f"first_band={log[0]['draft']['band']}/{log[0]['draft']['composite']}",
        f"final_band={final['draft']['band']}/{final['draft']['composite']}",
        f"final_verify={final['verify']['pass']}",
    )


if __name__ == "__main__":
    main()
