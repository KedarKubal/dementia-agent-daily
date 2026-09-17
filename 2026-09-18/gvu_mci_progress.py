#!/usr/bin/env python3
"""Day 2026-09-18 — MCI→AD 6-year speech progression flag (GVU).

Insight prototyped (Amini et al. 2024 + PREPARE pause-annotated LMs):
binary "has dementia?" screens miss the product. The seed is a *horizon*
scorer: speech + pause annotation + age/sex/education → P(progress to AD
within 6 years). Generator drafts weights; Verifier enforces explicit
criteria; Updater revises 3 passes.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

# --- sample: transcribed cookie-theft-like utterance + demographics ---
SAMPLE = {
    "id": "fhs-mci-042",
    "transcript": (
        "the uh the mother is washing dishes and water is overflowing "
        "and the boy is ... standing on a stool reaching for the cookie "
        "jar and the girl is laughing and um I don't know the rest"
    ),
    "pause_ratio": 0.31,
    "speech_rate_wpm": 92.0,
    "idea_density": 0.38,
    "age": 74,
    "sex": "F",
    "education_years": 12,
}


@dataclass
class Candidate:
    pause_w: float
    rate_w: float
    idea_w: float
    demo_w: float
    horizon_years: int
    score: float = 0.0
    band: str = "unknown"
    notes: str = ""
    features: dict[str, float] = field(default_factory=dict)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def feature_pack(sample: dict[str, Any]) -> dict[str, float]:
    pause = _clip(sample["pause_ratio"] / 0.40)
    rate = _clip((120.0 - sample["speech_rate_wpm"]) / 50.0)
    idea = _clip((0.55 - sample["idea_density"]) / 0.35)
    age_r = _clip((sample["age"] - 60) / 30.0)
    edu_r = _clip((16 - sample["education_years"]) / 10.0)
    return {
        "pause_risk": round(pause, 4),
        "slow_rate_risk": round(rate, 4),
        "low_idea_risk": round(idea, 4),
        "age_risk": round(age_r, 4),
        "low_edu_risk": round(edu_r, 4),
    }


def generate(sample: dict[str, Any], prior: Candidate | None, critique: str) -> Candidate:
    """Generator: draft (or revise) a 6-year progression scorer."""
    feats = feature_pack(sample)
    if prior is None:
        cand = Candidate(
            pause_w=0.10,
            rate_w=0.40,
            idea_w=0.40,
            demo_w=0.10,
            horizon_years=1,
            notes="pass1 naive fluency-only 1-year screen",
        )
    else:
        pause_w = prior.pause_w
        rate_w = prior.rate_w
        idea_w = prior.idea_w
        demo_w = prior.demo_w
        horizon = prior.horizon_years
        note_bits: list[str] = []
        if "pause_w" in critique:
            pause_w = min(0.45, pause_w + 0.18)
            note_bits.append("raised pause_w")
        if "horizon" in critique:
            horizon = 6
            note_bits.append("set horizon=6y")
        if "demo_w" in critique:
            demo_w = min(0.30, demo_w + 0.12)
            note_bits.append("raised demo_w")
        s = pause_w + rate_w + idea_w + demo_w
        pause_w, rate_w, idea_w, demo_w = (
            pause_w / s,
            rate_w / s,
            idea_w / s,
            demo_w / s,
        )
        cand = Candidate(
            pause_w=round(pause_w, 3),
            rate_w=round(rate_w, 3),
            idea_w=round(idea_w, 3),
            demo_w=round(demo_w, 3),
            horizon_years=horizon,
            notes="; ".join(note_bits) or "tweaked",
        )
    speech = (
        cand.pause_w * feats["pause_risk"]
        + cand.rate_w * feats["slow_rate_risk"]
        + cand.idea_w * feats["low_idea_risk"]
    )
    demo = 0.6 * feats["age_risk"] + 0.4 * feats["low_edu_risk"]
    raw = speech + cand.demo_w * demo * 0.5
    if cand.horizon_years < 6:
        raw *= 0.75
    cand.score = round(_clip(raw), 3)
    cand.band = "high" if cand.score >= 0.62 else "medium" if cand.score >= 0.40 else "low"
    cand.features = feats
    return cand


def verify(cand: Candidate) -> tuple[bool, str]:
    """PASS iff horizon==6, pause_w>=0.25, demo_w>=0.18, score>=0.40."""
    fails: list[str] = []
    if cand.horizon_years != 6:
        fails.append(f"horizon={cand.horizon_years} (need 6)")
    if cand.pause_w < 0.25:
        fails.append(f"pause_w={cand.pause_w:.3f} < 0.25")
    if cand.demo_w < 0.18:
        fails.append(f"demo_w={cand.demo_w:.3f} < 0.18")
    if cand.score < 0.40:
        fails.append(f"score={cand.score} band={cand.band} (need >=0.40)")
    if fails:
        return False, "FAIL: " + "; ".join(fails)
    return True, (
        f"PASS: horizon=6 pause_w={cand.pause_w:.3f} "
        f"demo_w={cand.demo_w:.3f} score={cand.score} band={cand.band}"
    )


def run_gvu(sample: dict[str, Any], max_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    prior: Candidate | None = None
    critique = ""
    for i in range(1, max_passes + 1):
        cand = generate(sample, prior, critique)
        ok, reason = verify(cand)
        row = {
            "pass": i,
            "candidate": asdict(cand),
            "verified": ok,
            "reason": reason,
        }
        log.append(row)
        print(f"--- pass {i} ---")
        print(json.dumps(row, indent=2))
        if ok:
            break
        critique = reason
        prior = cand
    return log


if __name__ == "__main__":
    print("SAMPLE", SAMPLE["id"], "pause_ratio", SAMPLE["pause_ratio"])
    history = run_gvu(SAMPLE, max_passes=3)
    print("\nBEFORE (pass 1 band/score):", history[0]["candidate"]["band"], history[0]["candidate"]["score"])
    print("AFTER  (last band/score):", history[-1]["candidate"]["band"], history[-1]["candidate"]["score"])
    print("FINAL verified:", history[-1]["verified"], history[-1]["reason"])
