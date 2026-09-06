#!/usr/bin/env python3
"""Day 2026-09-07 — Linguistic-informativeness story-recall flag.

Insight from Voiceprints of cognitive impairment (npj Dementia, 2025):
reduced linguistic informativeness (not just pause/rate) is the key AD
indicator, and end-to-end models beat feature-only models at EOAD vs
EOnonAD. Generator drafts a risk flag; Verifier requires BOTH acoustic
AND informativeness features plus a 3-class band; Updater revises weights.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List


@dataclass
class Features:
    pause_ratio: float
    speech_rate_wpm: float
    content_units: float
    idea_density: float
    filler_ratio: float


SAMPLE = Features(
    pause_ratio=0.31,
    speech_rate_wpm=92.0,
    content_units=0.42,
    idea_density=0.55,
    filler_ratio=0.18,
)


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def generator(feat: Features, weights: dict) -> dict:
    pause_r = clamp(feat.pause_ratio / 0.40)
    rate_r = clamp((140 - feat.speech_rate_wpm) / 80)
    content_r = clamp((0.80 - feat.content_units) / 0.50)
    density_r = clamp((1.20 - feat.idea_density) / 0.80)
    filler_r = clamp(feat.filler_ratio / 0.20)
    ac_den = max(1e-6, weights["w_pause"] + weights["w_rate"])
    lg_den = max(1e-6, weights["w_content"] + weights["w_density"] + weights["w_filler"])
    acoustic = (weights["w_pause"] * pause_r + weights["w_rate"] * rate_r) / ac_den
    linguistic = (
        weights["w_content"] * content_r
        + weights["w_density"] * density_r
        + weights["w_filler"] * filler_r
    ) / lg_den
    mix_l = lg_den / (ac_den + lg_den)
    score = clamp((1 - mix_l) * acoustic + mix_l * linguistic)
    if score >= 0.62:
        band = "eoad_like"
    elif score >= 0.40:
        band = "eononad_or_mci"
    else:
        band = "unimpaired"
    return {
        "score": round(score, 3),
        "band": band,
        "acoustic": round(acoustic, 3),
        "linguistic": round(linguistic, 3),
        "weights": weights,
        "used_linguistic": weights["w_content"] + weights["w_density"] + weights["w_filler"] >= 0.45,
    }


def verifier(out: dict) -> dict:
    w = out["weights"]
    ling_w = w["w_content"] + w["w_density"] + w["w_filler"]
    ac_w = w["w_pause"] + w["w_rate"]
    reasons = []
    ok = True
    if ling_w < 0.45:
        ok = False
        reasons.append(f"linguistic weights too low ({ling_w:.2f} < 0.45)")
    if ac_w < 0.20:
        ok = False
        reasons.append(f"acoustic weights too low ({ac_w:.2f} < 0.20)")
    if SAMPLE.content_units < 0.50 and out["band"] != "eoad_like":
        ok = False
        reasons.append(f"sparse recall must be eoad_like, got {out['band']} score={out['score']}")
    if out["score"] < 0 or out["score"] > 1:
        ok = False
        reasons.append("score out of range")
    if out["band"] not in {"eoad_like", "eononad_or_mci", "unimpaired"}:
        ok = False
        reasons.append("illegal band")
    if ok:
        reasons.append("pass: dual-channel + sparse-recall → eoad_like")
    return {"pass": ok, "reasons": reasons, "ling_w": round(ling_w, 3), "ac_w": round(ac_w, 3)}


def updater(weights: dict, critique: dict) -> dict:
    w = dict(weights)
    if critique["ling_w"] < 0.45:
        w["w_content"] = min(0.40, w["w_content"] + 0.12)
        w["w_density"] = min(0.25, w["w_density"] + 0.06)
        w["w_filler"] = min(0.20, w["w_filler"] + 0.04)
    if critique["ac_w"] < 0.20:
        w["w_pause"] = max(0.12, w["w_pause"])
        w["w_rate"] = max(0.10, w["w_rate"])
    if not critique["pass"] and any("eoad_like" in r for r in critique["reasons"]):
        w["w_content"] = min(0.55, w["w_content"] + 0.18)
        w["w_density"] = min(0.30, w["w_density"] + 0.05)
    s = sum(w.values())
    return {k: round(v / s, 4) for k, v in w.items()}


def run_loop(passes: int = 3) -> List[dict]:
    weights = {
        "w_pause": 0.35,
        "w_rate": 0.30,
        "w_content": 0.15,
        "w_density": 0.12,
        "w_filler": 0.08,
    }
    log = []
    for i in range(1, passes + 1):
        out = generator(SAMPLE, weights)
        crit = verifier(out)
        log.append({"pass": i, "output": out, "verify": crit})
        if crit["pass"]:
            break
        weights = updater(weights, crit)
    return log


def main() -> None:
    log = run_loop()
    print(json.dumps(log, indent=2))
    first, last = log[0], log[-1]
    print("\n--- SMOKE ---")
    print("before:", first["output"]["score"], first["output"]["band"], "pass=", first["verify"]["pass"])
    print("after: ", last["output"]["score"], last["output"]["band"], "pass=", last["verify"]["pass"])


if __name__ == "__main__":
    main()
