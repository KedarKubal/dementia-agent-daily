#!/usr/bin/env python3
"""GVU prototype: 4-week ambient-gait fall-risk flag for dementia LTC.

Insight prototyped (Adeli et al. 2023 IEEE JBHI): frequently updated
short-horizon fall risk from ambient gait beats static clinical scores.

Verifier criterion (falsifiable):
  PASS iff
    - risk_band in {low, medium, high}
    - 0.0 <= score <= 1.0
    - if step_time_cv >= 0.08 OR gait_speed_m_s < 0.6 then score >= 0.55 and band != low
    - if step_time_cv < 0.04 AND gait_speed_m_s >= 0.9 then score <= 0.35 and band == low
    - score uses both gait_speed and step_time_cv (not a single feature)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List


@dataclass
class GaitSample:
    gait_speed_m_s: float
    step_time_cv: float
    dual_task_slowing_pct: float
    days_since_last_fall: int


@dataclass
class Flag:
    score: float
    band: str
    rationale: str
    weights: dict


def _band(score: float) -> str:
    if score >= 0.65:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def generate(sample: GaitSample, critique: str = "") -> Flag:
    # Naive first pass: overweight speed only (will fail verifier if CV is high).
    w_speed, w_cv, w_dual = 0.80, 0.10, 0.10
    if "increase weight on step_time_cv" in critique:
        w_speed, w_cv, w_dual = 0.35, 0.45, 0.20
    if "raise score" in critique:
        w_speed, w_cv, w_dual = 0.30, 0.50, 0.20
    if "lower score" in critique:
        w_speed, w_cv, w_dual = 0.50, 0.25, 0.25

    speed_risk = max(0.0, min(1.0, (0.95 - sample.gait_speed_m_s) / 0.55))
    cv_risk = max(0.0, min(1.0, sample.step_time_cv / 0.14))
    dual_risk = max(0.0, min(1.0, sample.dual_task_slowing_pct / 35.0))
    recency = 0.15 if sample.days_since_last_fall <= 28 else 0.0

    raw = w_speed * speed_risk + w_cv * cv_risk + w_dual * dual_risk + recency
    score = round(max(0.0, min(1.0, raw)), 3)
    rationale = (
        f"weights speed={w_speed:.2f} cv={w_cv:.2f} dual={w_dual:.2f}; "
        f"speed_risk={speed_risk:.2f} cv_risk={cv_risk:.2f} dual_risk={dual_risk:.2f} recency={recency:.2f}"
    )
    return Flag(score=score, band=_band(score), rationale=rationale, weights={"speed": w_speed, "cv": w_cv, "dual": w_dual})


def verify(sample: GaitSample, flag: Flag) -> dict:
    reasons: List[str] = []
    ok = True
    if flag.band not in {"low", "medium", "high"}:
        ok = False
        reasons.append("band not in {low,medium,high}")
    if not (0.0 <= flag.score <= 1.0):
        ok = False
        reasons.append("score out of [0,1]")
    uses_both = flag.weights.get("speed", 0) >= 0.15 and flag.weights.get("cv", 0) >= 0.20
    if not uses_both:
        ok = False
        reasons.append("increase weight on step_time_cv (must be >=0.20 and speed >=0.15)")
    high_var = sample.step_time_cv >= 0.08 or sample.gait_speed_m_s < 0.6
    if high_var and (flag.score < 0.55 or flag.band == "low"):
        ok = False
        reasons.append("raise score: high variability or slow gait requires score>=0.55 and band!=low")
    stable = sample.step_time_cv < 0.04 and sample.gait_speed_m_s >= 0.9
    if stable and (flag.score > 0.35 or flag.band != "low"):
        ok = False
        reasons.append("lower score: stable fast gait requires score<=0.35 and band=low")
    if ok:
        reasons.append("all explicit criteria met")
    return {"pass": ok, "reason": "; ".join(reasons)}


def updater_loop(sample: GaitSample, max_passes: int = 3) -> list:
    log = []
    critique = ""
    flag = None
    for i in range(1, max_passes + 1):
        flag = generate(sample, critique)
        v = verify(sample, flag)
        log.append({"pass": i, "flag": asdict(flag), "verify": v})
        if v["pass"]:
            break
        critique = v["reason"]
    return log


def main() -> None:
    sample = GaitSample(
        gait_speed_m_s=0.72,
        step_time_cv=0.11,
        dual_task_slowing_pct=22.0,
        days_since_last_fall=12,
    )
    log = updater_loop(sample)
    print("SAMPLE", asdict(sample))
    print("BEFORE (pass 1)")
    print(json.dumps(log[0], indent=2))
    print("AFTER (final pass)")
    print(json.dumps(log[-1], indent=2))
    print("FULL_LOG")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
