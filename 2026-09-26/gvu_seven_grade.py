#!/usr/bin/env python3
"""Seven-grade Viveka speech flag — GVU prototype for 2026-09-26.

Maps Yoga Sutra II.26–27 (unbroken discrimination; sevenfold knowledge)
onto a staged speech-biomarker ladder instead of a binary AD/HC call.

Educational prototype only. Not a medical device.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any


GRADES = [
    "g1_known_enough",      # search dissatisfaction gone — screening complete
    "g2_pain_absent",       # no functional pain / ADL friction
    "g3_full_knowledge",    # rich linguistic+acoustic coverage
    "g4_duty_complete",     # protocol adherence / task completion
    "g5_chitta_free",       # fluency / low vacillation (pause, fillers)
    "g6_chitta_dissolves",  # residual / seed risk acknowledged
    "g7_established",       # seer-stable: longitudinal consistency
]


@dataclass
class SpeechSample:
    pause_ratio: float
    speech_rate: float          # syllables / min, ~90–160 typical
    type_token: float
    informativeness: float      # 0–1 content-word density proxy
    task_complete: float        # 0–1 protocol finished
    residual_seed: float        # 0–1 latent risk after coloring
    longitudinal_cv: float      # week-to-week score CV (lower is stabler)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def grade_scores(s: SpeechSample) -> dict[str, float]:
    """Heuristic per-grade risk (higher = more concerning)."""
    fluency_risk = _clip(0.55 * s.pause_ratio + 0.45 * (1.0 - min(s.speech_rate, 160) / 160))
    return {
        "g1_known_enough": _clip(1.0 - s.informativeness),
        "g2_pain_absent": _clip(0.4 * fluency_risk + 0.6 * (1.0 - s.task_complete)),
        "g3_full_knowledge": _clip(0.5 * (1.0 - s.type_token) + 0.5 * (1.0 - s.informativeness)),
        "g4_duty_complete": _clip(1.0 - s.task_complete),
        "g5_chitta_free": fluency_risk,
        "g6_chitta_dissolves": _clip(s.residual_seed),
        "g7_established": _clip(s.longitudinal_cv),
    }


def generate(sample: SpeechSample, mode: str = "binary") -> dict[str, Any]:
    """Generator: candidate seven-grade (or collapsed) flag."""
    raw = grade_scores(sample)
    if mode == "binary":
        weights = {g: (1.0 if g == "g5_chitta_free" else 0.0) for g in GRADES}
        weights["g5_chitta_free"] = 1.0
    elif mode == "partial":
        weights = {g: 0.2 for g in GRADES}
        weights["g5_chitta_free"] = 0.40
        weights["g1_known_enough"] = 0.25
        weights["g6_chitta_dissolves"] = 0.05
        weights["g7_established"] = 0.05
        z = sum(weights.values())
        weights = {k: v / z for k, v in weights.items()}
    else:
        weights = {g: 1.0 / 7.0 for g in GRADES}

    score = sum(weights[g] * raw[g] for g in GRADES)
    band = "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
    return {
        "mode": mode,
        "weights": weights,
        "per_grade": raw,
        "score": round(score, 3),
        "band": band,
        "populated": [g for g in GRADES if weights[g] >= 0.08],
    }


def verify(out: dict[str, Any]) -> dict[str, Any]:
    """Verifier success criterion (falsifiable):

    PASS iff ALL of:
      1. Every grade has weight >= 0.08 (sevenfold ground, not a binary dump).
      2. At least 5 grades are 'populated' at that threshold.
      3. Mid-path grades g3–g6 together carry >= 0.40 of total weight
         (discrimination is a path, not a single fluency snapshot).
      4. Score is in (0.20, 0.85) — not a collapsed 0/1.
    """
    w = out["weights"]
    reasons: list[str] = []
    min_w = min(w[g] for g in GRADES)
    if min_w < 0.08:
        reasons.append(f"min_weight={min_w:.3f} < 0.08 — collapsed ladder")
    populated = [g for g in GRADES if w[g] >= 0.08]
    if len(populated) < 5:
        reasons.append(f"populated={len(populated)} < 5")
    mid = sum(w[g] for g in GRADES[2:6])
    if mid < 0.40:
        reasons.append(f"mid_path_weight={mid:.3f} < 0.40")
    if not (0.20 < out["score"] < 0.85):
        reasons.append(f"score={out['score']} outside (0.20, 0.85)")
    ok = len(reasons) == 0
    return {
        "pass": ok,
        "reasons": reasons or ["sevenfold discrimination ladder satisfied"],
        "min_weight": round(min_w, 3),
        "populated_n": len(populated),
        "mid_path_weight": round(mid, 3),
    }


def update(prev: dict[str, Any], critique: dict[str, Any]) -> str:
    joined = " ".join(critique["reasons"]).lower()
    if "collapsed" in joined or "populated" in joined:
        return "partial" if prev["mode"] == "binary" else "sevenfold"
    if "mid_path" in joined:
        return "sevenfold"
    return "sevenfold"


def run_gvu(sample: SpeechSample, max_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    mode = "binary"
    out = generate(sample, mode=mode)
    for i in range(1, max_passes + 1):
        crit = verify(out)
        log.append({"pass": i, "output": out, "verify": crit})
        if crit["pass"]:
            break
        mode = update(out, crit)
        out = generate(sample, mode=mode)
    return log


SAMPLE = SpeechSample(
    pause_ratio=0.38,
    speech_rate=98.0,
    type_token=0.42,
    informativeness=0.48,
    task_complete=0.70,
    residual_seed=0.55,
    longitudinal_cv=0.31,
)


def main() -> None:
    log = run_gvu(SAMPLE)
    print("=== SMOKE 2026-09-26 seven-grade viveka flag ===")
    for row in log:
        o, v = row["output"], row["verify"]
        print(
            f"pass{row['pass']} mode={o['mode']} score={o['score']} "
            f"band={o['band']} populated={len(o['populated'])} "
            f"verify={'PASS' if v['pass'] else 'FAIL'} :: {v['reasons']}"
        )
    first, last = log[0]["output"], log[-1]["output"]
    print("--- before ---")
    print(json.dumps({"mode": first["mode"], "score": first["score"], "band": first["band"], "weights": first["weights"]}, indent=2))
    print("--- after ---")
    print(json.dumps({"mode": last["mode"], "score": last["score"], "band": last["band"], "weights": last["weights"]}, indent=2))
    with open("run.json", "w", encoding="utf-8") as f:
        json.dump({"sample": asdict(SAMPLE), "log": log}, f, indent=2)
    print("wrote run.json")


if __name__ == "__main__":
    main()
