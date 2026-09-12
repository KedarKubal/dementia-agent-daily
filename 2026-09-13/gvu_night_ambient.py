#!/usr/bin/env python3
"""
Day 2026-09-13 — Night-time ambient safety flag (GVU).

Insight prototyped: Serban et al. 2025 night-time ambient sensing
produced many true "out of home" events, but ~15% were routine
(bathroom / known kitchen loop). Generator that treats every exit as
risk is too noisy. GVU loop learns a routine-suppression weight.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class NightFeatures:
    """One night of ambient + mattress + door signals (unitless 0–1 or hours)."""

    motion_after_midnight: float  # fraction of minutes with motion 00:00–05:00
    door_opens_night: int
    hours_outside: float
    mattress_absence_hours: float
    known_routine_overlap: float  # 0–1 overlap with learned bathroom/kitchen windows
    caregiver_on_site: bool


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def generate(feat: NightFeatures, routine_w: float, exit_w: float) -> dict[str, Any]:
    """Draft risk: exits + mattress absence minus routine overlap."""
    exit_component = clamp(feat.hours_outside / 2.5) * 0.55 + clamp(
        feat.door_opens_night / 6.0
    ) * 0.15
    absence = clamp(feat.mattress_absence_hours / 2.5) * 0.25
    motion = clamp(feat.motion_after_midnight) * 0.12
    raw = exit_w * (exit_component + absence + motion)
    # Soft routine discount so true long exits still score high.
    suppressed = raw * (1.0 - 0.55 * routine_w * feat.known_routine_overlap)
    if feat.caregiver_on_site:
        suppressed *= 0.7
    score = clamp(suppressed)
    if score >= 0.65:
        band = "high"
    elif score >= 0.40:
        band = "medium"
    else:
        band = "low"
    alert = score >= 0.55 and feat.hours_outside >= 0.5 and feat.known_routine_overlap < 0.7
    return {
        "score": round(score, 3),
        "band": band,
        "alert": alert,
        "routine_w": round(routine_w, 3),
        "exit_w": round(exit_w, 3),
        "reason": (
            f"exit={exit_component:.2f} absence={absence:.2f} "
            f"routine_overlap={feat.known_routine_overlap:.2f}"
        ),
    }


def verify(out: dict[str, Any], feat: NightFeatures) -> dict[str, Any]:
    """
    Success criterion (falsifiable):
    1) score in [0.55, 0.85] for this anomalous-but-partly-routine sample
    2) routine_w >= 0.55 (routine suppression is active, not ignored)
    3) alert is True only if hours_outside >= 0.5 AND overlap < 0.70
    4) band is medium or high
    """
    reasons: list[str] = []
    ok_score = 0.55 <= out["score"] <= 0.85
    if not ok_score:
        reasons.append(f"score {out['score']} outside [0.55, 0.85]")
    ok_w = out["routine_w"] >= 0.55
    if not ok_w:
        reasons.append(f"routine_w {out['routine_w']} < 0.55 (treating routine as risk)")
    expected_alert = feat.hours_outside >= 0.5 and feat.known_routine_overlap < 0.70
    ok_alert = out["alert"] == expected_alert
    if not ok_alert:
        reasons.append(f"alert {out['alert']} != expected {expected_alert}")
    ok_band = out["band"] in {"medium", "high"}
    if not ok_band:
        reasons.append(f"band {out['band']} not medium/high")
    passed = ok_score and ok_w and ok_alert and ok_band
    return {"pass": passed, "reasons": reasons or ["all criteria met"]}


def update(out: dict[str, Any], critique: dict[str, Any]) -> tuple[float, float]:
    routine_w, exit_w = out["routine_w"], out["exit_w"]
    text = " ".join(critique["reasons"]).lower()
    if "routine_w" in text:
        routine_w = min(0.80, routine_w + 0.40)
    if "score" in text and out["score"] < 0.55:
        exit_w = min(1.4, exit_w + 0.15)
        routine_w = max(0.40, routine_w - 0.05)
    if "score" in text and out["score"] > 0.85:
        routine_w = min(0.90, routine_w + 0.10)
        exit_w = max(0.70, exit_w - 0.10)
    if "alert" in text:
        routine_w = min(0.85, routine_w + 0.15)
    return routine_w, exit_w


def run_loop(feat: NightFeatures, passes: int = 3) -> list[dict[str, Any]]:
    routine_w, exit_w = 0.20, 1.00  # naive first draft: almost no routine discount
    log: list[dict[str, Any]] = []
    for i in range(1, passes + 1):
        out = generate(feat, routine_w, exit_w)
        critique = verify(out, feat)
        log.append({"pass": i, "output": out, "verify": critique})
        if critique["pass"]:
            break
        routine_w, exit_w = update(out, critique)
    return log


SAMPLE = NightFeatures(
    motion_after_midnight=0.42,
    door_opens_night=3,
    hours_outside=1.8,
    mattress_absence_hours=2.1,
    known_routine_overlap=0.35,
    caregiver_on_site=False,
)


def main() -> None:
    log = run_loop(SAMPLE)
    print("=== SAMPLE (anomalous night, partial routine overlap) ===")
    print(json.dumps(asdict(SAMPLE), indent=2))
    print("\n=== GVU LOG ===")
    print(json.dumps(log, indent=2))
    first, last = log[0]["output"], log[-1]["output"]
    print("\n=== BEFORE / AFTER ===")
    print(
        f"pass1 score={first['score']} band={first['band']} "
        f"alert={first['alert']} routine_w={first['routine_w']}"
    )
    print(
        f"pass{log[-1]['pass']} score={last['score']} band={last['band']} "
        f"alert={last['alert']} routine_w={last['routine_w']} "
        f"verified={log[-1]['verify']['pass']}"
    )


if __name__ == "__main__":
    main()
