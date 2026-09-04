#!/usr/bin/env python3
"""GVU prototype: effort-conditioned vocal biomarker risk flag.

Insight prototyped (Larsen et al. 2024, Alz & Dem): speech rate and pause
duration shift more under high mental-effort tasks than at rest, and that
*delta* is the useful early-impairment signal — not the rest-only values.

Generator drafts a risk band from rest + effort features.
Verifier requires:
  (1) effort_delta_used is True (rest-only scores are rejected),
  (2) risk band matches explicit cutoffs on effort-adjusted score,
  (3) score is in [0, 1].
Updater raises the weight on the effort delta until the criterion passes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List


SAMPLE = {
    "id": "demo-effort-01",
    "rest_speech_rate_spm": 118.0,   # syllables / min
    "rest_pause_s": 0.48,
    "effort_speech_rate_spm": 92.0,  # high-load picture description
    "effort_pause_s": 0.81,
}


@dataclass
class Draft:
    pass_n: int
    effort_delta_used: bool
    delta_weight: float
    score: float
    band: str
    rationale: str


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def effort_features(sample: dict) -> dict:
    rate_drop = max(0.0, sample["rest_speech_rate_spm"] - sample["effort_speech_rate_spm"])
    pause_rise = max(0.0, sample["effort_pause_s"] - sample["rest_pause_s"])
    # Normalize against published-ish ranges (Larsen: ~25% rate variation under load).
    rate_drop_n = _clip(rate_drop / 40.0)
    pause_rise_n = _clip(pause_rise / 0.50)
    rest_slow_n = _clip((110.0 - sample["rest_speech_rate_spm"]) / 40.0)
    rest_pause_n = _clip((sample["rest_pause_s"] - 0.40) / 0.50)
    return {
        "rate_drop_n": round(rate_drop_n, 3),
        "pause_rise_n": round(pause_rise_n, 3),
        "rest_slow_n": round(rest_slow_n, 3),
        "rest_pause_n": round(rest_pause_n, 3),
    }


def band_from_score(score: float) -> str:
    if score >= 0.62:
        return "high"
    if score >= 0.38:
        return "medium"
    return "low"


def generate(sample: dict, pass_n: int, delta_weight: float, use_delta: bool) -> Draft:
    f = effort_features(sample)
    if use_delta:
        score = (
            delta_weight * 0.5 * (f["rate_drop_n"] + f["pause_rise_n"])
            + (1.0 - delta_weight) * 0.5 * (f["rest_slow_n"] + f["rest_pause_n"])
        )
        rationale = (
            f"effort-delta weighted {delta_weight:.2f}: "
            f"rate_drop={f['rate_drop_n']}, pause_rise={f['pause_rise_n']}; "
            f"rest mix={1-delta_weight:.2f}"
        )
    else:
        # Intentionally weak first draft: rest-only (what most consumer apps do).
        score = 0.5 * (f["rest_slow_n"] + f["rest_pause_n"])
        rationale = "rest-only (no mental-effort contrast)"
    score = round(_clip(score), 3)
    return Draft(
        pass_n=pass_n,
        effort_delta_used=use_delta,
        delta_weight=round(delta_weight, 3),
        score=score,
        band=band_from_score(score),
        rationale=rationale,
    )


def verify(draft: Draft) -> dict:
    reasons: List[str] = []
    if not draft.effort_delta_used:
        reasons.append("FAIL: effort_delta_used is False — rest-only scores are not the paper's signal")
    if draft.delta_weight < 0.70:
        reasons.append(f"FAIL: delta_weight {draft.delta_weight} < 0.70 (effort contrast under-weighted)")
    if not (0.0 <= draft.score <= 1.0):
        reasons.append(f"FAIL: score {draft.score} outside [0,1]")
    expected = band_from_score(draft.score)
    if draft.band != expected:
        reasons.append(f"FAIL: band {draft.band} != cutoff band {expected}")
    # Sample-specific: this demo has a large effort drop, so high band is required once delta is used.
    if draft.effort_delta_used and draft.delta_weight >= 0.70 and draft.band != "high":
        reasons.append("FAIL: large effort-delta sample must land in high band")
    ok = len(reasons) == 0
    if ok:
        reasons.append("PASS: effort delta used, weight>=0.70, band matches cutoffs, score in [0,1]")
    return {"pass": ok, "reasons": reasons}


def update(draft: Draft, critique: dict) -> tuple[bool, float]:
    """Return (use_delta, new_weight) for the next generate pass."""
    use_delta = True
    weight = draft.delta_weight
    joined = " ".join(critique["reasons"])
    if "effort_delta_used is False" in joined:
        use_delta = True
        weight = max(weight, 0.55)
    if "delta_weight" in joined:
        weight = min(0.95, max(0.80, weight + 0.25))
    if "must land in high band" in joined:
        weight = min(0.95, weight + 0.20)
    return use_delta, weight


def run(sample: dict, max_passes: int = 3) -> list[dict]:
    log = []
    use_delta, weight = False, 0.20  # start naive
    draft = generate(sample, 1, weight, use_delta)
    for i in range(1, max_passes + 1):
        critique = verify(draft)
        log.append({"draft": asdict(draft), "verify": critique})
        if critique["pass"]:
            break
        use_delta, weight = update(draft, critique)
        draft = generate(sample, i + 1, weight, use_delta)
    return log


def main() -> None:
    log = run(SAMPLE)
    print("SAMPLE", json.dumps(SAMPLE, indent=2))
    print("FEATURES", json.dumps(effort_features(SAMPLE), indent=2))
    print("--- GVU PASSES ---")
    for row in log:
        d, v = row["draft"], row["verify"]
        print(
            f"pass {d['pass_n']}: delta_used={d['effort_delta_used']} "
            f"w={d['delta_weight']} score={d['score']} band={d['band']} "
            f"| verify={'PASS' if v['pass'] else 'FAIL'} — {v['reasons'][0]}"
        )
        print(f"         rationale: {d['rationale']}")
    out = {
        "sample": SAMPLE,
        "features": effort_features(SAMPLE),
        "passes": log,
        "final_pass": log[-1]["draft"]["pass_n"],
        "final_band": log[-1]["draft"]["band"],
        "verified": log[-1]["verify"]["pass"],
    }
    with open("run.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote run.json")


if __name__ == "__main__":
    main()
