#!/usr/bin/env python3
"""GVU Day 2026-09-24 — Common-field residual speech flag (YS 2.22).

Nature is destroyed for the one who has reached the goal, yet remains
common to others. Score pause-load against the still-living matched
cohort, not a universal cutoff.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


COMMON_FIELD = {
    (60, 69): 0.18,
    (70, 79): 0.24,
    (80, 89): 0.31,
}


def common_mean(age: int) -> float:
    for (lo, hi), mu in COMMON_FIELD.items():
        if lo <= age <= hi:
            return mu
    return 0.22


@dataclass
class Sample:
    age: int
    pause_pct: float
    sentence_len: float
    noun_count: float


@dataclass
class Draft:
    score: float
    band: str
    residual_w: float
    raw_w: float
    residual: float
    notes: str
    pass_n: int = 1


def band_of(score: float) -> str:
    if score >= 0.62:
        return "high"
    if score >= 0.42:
        return "medium"
    return "low"


def generator(sample: Sample, residual_w: float, pass_n: int) -> Draft:
    raw_w = max(0.0, 1.0 - residual_w)
    mu = common_mean(sample.age)
    residual = max(0.0, sample.pause_pct - mu) / max(0.12, 1.0 - mu)
    lex = max(0.0, min(1.0, (12.0 - sample.sentence_len) / 8.0))
    raw = max(0.0, min(1.0, sample.pause_pct / 0.45))
    score = residual_w * (0.7 * residual + 0.3 * lex) + raw_w * raw
    score = max(0.0, min(1.0, score))
    return Draft(
        score=round(score, 3),
        band=band_of(score),
        residual_w=round(residual_w, 2),
        raw_w=round(raw_w, 2),
        residual=round(residual, 3),
        notes=f"mu={mu:.2f} pause={sample.pause_pct:.2f} lex={lex:.2f}",
        pass_n=pass_n,
    )


def verifier(draft: Draft) -> dict[str, Any]:
    """Success criterion (falsifiable):
    1. residual_w >= 0.55 (common-field residual dominates raw cutoff)
    2. residual itself >= 0.15 (true excess vs matched others)
    3. band is medium or high when residual >= 0.15
    """
    reasons: list[str] = []
    ok_w = draft.residual_w >= 0.55
    ok_r = draft.residual >= 0.15
    ok_b = draft.band in {"medium", "high"} if ok_r else True
    if not ok_w:
        reasons.append(
            f"residual_w {draft.residual_w} < 0.55 (still using destroyed-for-one cutoff)"
        )
    if not ok_r:
        reasons.append(f"residual {draft.residual} < 0.15 (no excess vs common field)")
    if ok_r and draft.band == "low":
        reasons.append("excess vs others present but band collapsed to low")
    passed = ok_w and ok_r and ok_b
    return {"pass": passed, "reasons": reasons or ["meets common-field residual criteria"]}


def updater(draft: Draft, critique: dict[str, Any]) -> float:
    w = draft.residual_w
    if not critique["pass"]:
        if draft.residual_w < 0.55:
            w = min(0.80, w + 0.25)
        if draft.residual < 0.15:
            w = min(0.80, w + 0.10)
    return w


def run_loop(sample: Sample, max_passes: int = 3) -> list[dict[str, Any]]:
    w = 0.20
    log: list[dict[str, Any]] = []
    draft = generator(sample, w, 1)
    for i in range(1, max_passes + 1):
        crit = verifier(draft)
        log.append({"draft": asdict(draft), "verify": crit})
        if crit["pass"]:
            break
        w = updater(draft, crit)
        draft = generator(sample, w, i + 1)
    return log


SMOKE = Sample(age=76, pause_pct=0.38, sentence_len=7.5, noun_count=9.0)


def main() -> None:
    log = run_loop(SMOKE)
    print(json.dumps(log, indent=2))
    first, last = log[0], log[-1]
    print("\n--- smoke ---")
    print(
        f"before: score={first['draft']['score']} band={first['draft']['band']} "
        f"rw={first['draft']['residual_w']} pass={first['verify']['pass']}"
    )
    print(
        f"after:  score={last['draft']['score']} band={last['draft']['band']} "
        f"rw={last['draft']['residual_w']} pass={last['verify']['pass']}"
    )


if __name__ == "__main__":
    main()
