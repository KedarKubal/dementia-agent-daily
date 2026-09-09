#!/usr/bin/env python3
"""Day 2026-09-10 — Sabija (with-seed) latent residual risk flag.

Aphorism I.45–46: finer objects end in Pradhana; those concentrations are with seed.
Surface cognitive scores can look calm while a shared latent (prakriti) still holds seeds
of decline. Generator drafts a risk from surface + latent; Verifier rejects any LOW
label when latent_seed >= 0.55 (seeds remain). Updater raises latent weight.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Features:
    delayed_recall: float
    fluency: float
    sleep_fragment: float
    activity_drop: float
    speech_pause_residual: float


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def band(score: float) -> str:
    if score >= 0.62:
        return "high"
    if score >= 0.38:
        return "medium"
    return "low"


def latent_seed(f: Features) -> float:
    return clamp(0.40 * f.sleep_fragment + 0.30 * f.activity_drop + 0.30 * f.speech_pause_residual)


def surface_impair(f: Features) -> float:
    return clamp(0.5 * (1.0 - f.delayed_recall) + 0.5 * (1.0 - f.fluency))


def generate(f: Features, latent_w: float) -> dict:
    seed = latent_seed(f)
    surf = surface_impair(f)
    w = clamp(latent_w)
    score = clamp((1.0 - w) * surf + w * seed)
    return {
        "score": round(score, 3),
        "band": band(score),
        "latent_seed": round(seed, 3),
        "surface_impair": round(surf, 3),
        "latent_w": round(w, 3),
        "rationale": (
            f"surface={surf:.3f} latent_seed={seed:.3f} w={w:.2f} "
            f"→ {band(score)} {score:.3f}"
        ),
    }


def verify(out: dict) -> dict:
    reasons = []
    ok = True
    w = out["latent_w"]
    seed = out["latent_seed"]
    if not (0.45 <= w <= 0.80):
        ok = False
        reasons.append(f"latent_w {w} outside [0.45, 0.80]")
    if seed >= 0.55 and out["band"] == "low":
        ok = False
        reasons.append(f"sabija violation: latent_seed={seed} but band=low")
    expected = band(out["score"])
    if expected != out["band"]:
        ok = False
        reasons.append(f"band mismatch {out['band']} vs {expected}")
    if not (0.0 <= out["score"] <= 1.0):
        ok = False
        reasons.append("score out of range")
    if ok:
        reasons.append("pass: seed-aware weights and sabija rule held")
    return {"pass": ok, "reasons": reasons}


def update(latent_w: float, critique: dict) -> float:
    if critique["pass"]:
        return latent_w
    text = " ".join(critique["reasons"])
    w = latent_w
    if "latent_w" in text:
        w = 0.62
    if "sabija" in text:
        w = max(w, 0.70)
    return clamp(w)


def run_loop(f: Features, start_w: float = 0.20, max_pass: int = 3) -> List[dict]:
    log = []
    w = start_w
    for i in range(1, max_pass + 1):
        out = generate(f, w)
        crit = verify(out)
        log.append({"pass": i, "output": out, "verify": crit})
        if crit["pass"]:
            break
        w = update(w, crit)
    return log


SAMPLE = Features(
    delayed_recall=0.82,
    fluency=0.78,
    sleep_fragment=0.74,
    activity_drop=0.61,
    speech_pause_residual=0.58,
)


def main() -> None:
    log = run_loop(SAMPLE)
    print("=== SMOKE SAMPLE (surface-ok, seeded latent) ===")
    for row in log:
        print(f"\nPASS {row['pass']}")
        print("  gen:", row["output"]["rationale"])
        print("  verify:", row["verify"])
    first, last = log[0]["output"], log[-1]["output"]
    print("\nBEFORE:", first)
    print("AFTER: ", last)
    result = {"sample": asdict(SAMPLE), "log": log, "before": first, "after": last}
    print("\nJSON")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
