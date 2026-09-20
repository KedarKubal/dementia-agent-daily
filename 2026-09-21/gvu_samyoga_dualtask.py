#!/usr/bin/env python3
"""
Day 2026-09-21 — Samyoga dual-task cost flag (Generator–Verifier–Updater).

Insight prototyped: future dementia/fall risk is carried in the *junction*
of talking and walking (dual-task cost), not in either channel alone.
Naive generators overweight gait OR speech; the updater must raise the
weaker channel until both weights >= 0.30 and dual_task_cost >= 0.20.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Candidate:
    speech_slowing: float  # 0-1, higher = slower / more pause
    gait_variability: float  # 0-1, higher = more stride CV
    speech_w: float
    gait_w: float
    dual_task_cost: float
    band: str
    notes: str

    def score(self) -> float:
        wsum = max(self.speech_w + self.gait_w, 1e-9)
        fused = (
            self.speech_w * self.speech_slowing + self.gait_w * self.gait_variability
        ) / wsum
        return 0.50 * fused + 0.50 * self.dual_task_cost


def band_for(score: float) -> str:
    if score >= 0.70:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def generate(features: dict[str, float], critique: str | None) -> Candidate:
    speech = features["speech_slowing"]
    gait = features["gait_variability"]
    dtc = features["dual_task_cost"]
    sw, gw = 0.80, 0.20  # naive: speech-heavy "seer only"
    notes = "pass1-naive-speech-dominant"
    if critique:
        sw, gw = 0.50, 0.50
        notes = "pass2-balanced-junction"
        if "raise gait" in critique.lower() or "gait_w" in critique:
            sw, gw = 0.45, 0.55
            notes = "pass3-gait-lifted-to-meet-floor"
    cand = Candidate(speech, gait, sw, gw, dtc, "", notes)
    cand.band = band_for(cand.score())
    return cand


def verify(cand: Candidate) -> dict[str, Any]:
    """
    Explicit success criterion (falsifiable):
      PASS iff
        - dual_task_cost >= 0.20
        - speech_w >= 0.30 and gait_w >= 0.30
        - band in {medium, high}
        - score >= 0.50
    """
    reasons: list[str] = []
    if cand.dual_task_cost < 0.20:
        reasons.append(f"dual_task_cost {cand.dual_task_cost:.3f} < 0.20")
    if cand.speech_w < 0.30:
        reasons.append(f"speech_w {cand.speech_w:.2f} < 0.30 (seer channel dropped)")
    if cand.gait_w < 0.30:
        reasons.append(f"gait_w {cand.gait_w:.2f} < 0.30 — raise gait")
    if cand.band == "low":
        reasons.append("band is low; future-suffering signal under-called")
    if cand.score() < 0.50:
        reasons.append(f"score {cand.score():.3f} < 0.50")
    ok = not reasons
    return {
        "pass": ok,
        "reason": "PASS: junction-aware dual-task flag" if ok else "; ".join(reasons),
        "score": round(cand.score(), 3),
        "band": cand.band,
    }


def update_loop(features: dict[str, float], max_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    critique: str | None = None
    for i in range(1, max_passes + 1):
        cand = generate(features, critique)
        verdict = verify(cand)
        row = {"pass": i, "candidate": asdict(cand), "verify": verdict}
        log.append(row)
        if verdict["pass"]:
            break
        critique = verdict["reason"]
    return log


SAMPLE = {
    "speech_slowing": 0.72,
    "gait_variability": 0.68,
    "dual_task_cost": 0.41,  # 41% extra cost when talking+walking
}


def main() -> None:
    log = update_loop(SAMPLE)
    print("=== SMOKE SAMPLE (talk-while-walk) ===")
    print("input:", json.dumps(SAMPLE))
    for row in log:
        c = row["candidate"]
        v = row["verify"]
        print(
            f"pass{row['pass']}: band={c['band']} score={v['score']} "
            f"sw={c['speech_w']:.2f} gw={c['gait_w']:.2f} "
            f"dtc={c['dual_task_cost']:.2f} notes={c['notes']}"
        )
        print(f"         verify: {v['pass']} | {v['reason']}")
    before = log[0]
    after = log[-1]
    print("\nBEFORE:", json.dumps(before["verify"]))
    print("AFTER: ", json.dumps(after["verify"]))
    with open("run.json", "w", encoding="utf-8") as f:
        json.dump({"sample": SAMPLE, "log": log}, f, indent=2)
    print("wrote run.json")


if __name__ == "__main__":
    main()
