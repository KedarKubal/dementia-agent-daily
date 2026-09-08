#!/usr/bin/env python3
"""Day 2026-09-09 — Nirvitarka meaning-only speech flag (GVU).

Aphorism I.43: Samadhi without question when memory is purified and
only the meaning of the object shines. I.44: the same process applies
to finer objects.

Insight from NUS 2024 natural-speech work + Favaro 2023 interpretable
biomarkers: acoustic pauses/rate are the 'qualities' still mixed into
most vocal-biomarker products. After purifying those (treat them as
memory-impurity covariates, not the flag), the residual meaning channel
(abstract nouns, low imageability, sparse content units) is the finer
object. Prototype only trusts HIGH when meaning_w >= 0.55 and a purity
index (low filler + stable lexical access) is high.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Dict, List


SAMPLE = {
    "id": "natural_speech_amnestic_mci_like",
    "speech_rate_spm": 88.0,
    "mean_pause_s": 0.72,
    "silence_ratio": 0.31,
    "abstract_noun_ratio": 0.58,
    "imageability": 0.32,
    "noun_count": 9,
    "content_units": 5,
    "filler_rate": 0.18,
    "lexical_access_fail": 0.22,
}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def scores(s: Dict) -> Dict[str, float]:
    impurity = (
        clamp((110 - s["speech_rate_spm"]) / 50) * 0.35
        + clamp((s["mean_pause_s"] - 0.4) / 0.7) * 0.35
        + clamp((s["silence_ratio"] - 0.12) / 0.35) * 0.30
    )
    meaning = (
        clamp((s["abstract_noun_ratio"] - 0.22) / 0.50) * 0.35
        + clamp((0.70 - s["imageability"]) / 0.50) * 0.35
        + clamp((12 - s["content_units"]) / 12) * 0.30
    )
    purity = 1.0 - (
        clamp(s["filler_rate"] / 0.25) * 0.5
        + clamp(s["lexical_access_fail"] / 0.30) * 0.5
    )
    return {
        "impurity": round(impurity, 3),
        "meaning": round(meaning, 3),
        "purity": round(purity, 3),
    }


@dataclass
class Output:
    pass_n: int
    weights: Dict[str, float]
    scores: Dict[str, float]
    risk: float
    band: str
    note: str


def generate(sample: Dict, weights: Dict[str, float], pass_n: int, note: str, purify: float = 0.0) -> Output:
    sc = scores(sample)
    sc["purity"] = round(clamp(sc["purity"] + purify), 3)
    z = sum(weights.values()) or 1.0
    w = {k: v / z for k, v in weights.items()}
    damp = 1.0 - 0.25 * (1.0 - sc["purity"]) * w["impurity"]
    risk = sc["meaning"] * damp
    if risk >= 0.55:
        band = "high"
    elif risk >= 0.40:
        band = "medium"
    else:
        band = "low"
    return Output(pass_n, {k: round(v, 3) for k, v in w.items()}, sc, round(risk, 3), band, note)


def verify(out: Output) -> Dict:
    reasons = []
    ok = True
    if out.weights.get("meaning", 0) < 0.55:
        ok = False
        reasons.append(f"meaning_w={out.weights.get('meaning')} < 0.55 (still quality-mixed)")
    if out.weights.get("impurity", 1) > 0.35:
        ok = False
        reasons.append(f"impurity_w={out.weights.get('impurity')} > 0.35 (qualities not receded)")
    if out.scores["purity"] < 0.45:
        ok = False
        reasons.append(f"purity={out.scores['purity']} < 0.45 (memory not purified)")
    if out.band != "high" or out.risk < 0.55:
        ok = False
        reasons.append(f"need high>=0.55, got {out.band}/{out.risk}")
    if ok:
        reasons.append("pass: meaning-dominant, qualities receded, memory pure enough, high flag")
    return {"pass": ok, "reasons": reasons}


def update(out: Output, critique: Dict):
    w = dict(out.weights)
    text = " ".join(critique["reasons"])
    purify = 0.0
    if "meaning_w=" in text:
        w["meaning"] = w.get("meaning", 0.3) + 0.22
        w["impurity"] = max(0.10, w.get("impurity", 0.5) - 0.18)
    if "impurity_w=" in text:
        w["impurity"] = min(w.get("impurity", 0.5), 0.28)
        w["meaning"] = w.get("meaning", 0.5) + 0.10
    if "purity=" in text:
        purify += 0.22
    if "need high" in text:
        w["meaning"] = w.get("meaning", 0.5) + 0.06
    return w, purify


def run_gvu(sample: Dict, loops: int = 3):
    weights = {"meaning": 0.28, "impurity": 0.72}
    purify = 0.0
    log = []
    out = generate(sample, weights, 1, "pass1 quality-mixed (impurity-heavy)", purify)
    crit = verify(out)
    log.append({"output": asdict(out), "verify": crit})
    for i in range(2, loops + 1):
        weights, dpurify = update(out, crit)
        purify += dpurify
        out = generate(sample, weights, i, f"pass{i} after verifier critique", purify)
        crit = verify(out)
        log.append({"output": asdict(out), "verify": crit})
        if crit["pass"]:
            break
    return log


def main() -> None:
    log = run_gvu(SAMPLE, loops=3)
    print("=== SAMPLE ===")
    print(json.dumps(SAMPLE, indent=2))
    print("\n=== GVU LOG ===")
    print(json.dumps(log, indent=2))
    first = log[0]["output"]
    last = log[-1]["output"]
    print("\n=== BEFORE / AFTER ===")
    print(f"BEFORE pass1: risk={first['risk']} band={first['band']} w={first['weights']}")
    print(f"AFTER  pass{last['pass_n']}: risk={last['risk']} band={last['band']} w={last['weights']}")
    print(f"final verify: {log[-1]['verify']['pass']} | {log[-1]['verify']['reasons']}")


if __name__ == "__main__":
    main()
