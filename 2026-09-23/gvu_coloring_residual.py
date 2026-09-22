#!/usr/bin/env python3
"""
Day 2026-09-23 — Coloring-corrected residual speech risk (GVU).

Insight (II.20–21 + García-Gutiérrez / Favaro line of work):
the "experienced" speech stream is for the seer, but the seer sees
through the coloring of intellect (education, lexical polish, prompt
form). A raw fluency/pause score confounds instrument coloring with
true residual decline. Correct coloring, then score the residual.

Success criterion (falsifiable):
  PASS iff
    - coloring_w >= 0.35
    - residual_w >= 0.45
    - residual = clip(raw - coloring_w * coloring, 0, 1)
    - band is medium or high when residual >= 0.45
    - education and lexical features both used in coloring
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class Sample:
    """Toy features from a 60s picture-description."""

    pause_ratio: float  # 0-1
    pause_speech_ratio: float
    sentence_len: float  # words
    noun_count: float
    education_years: float
    type_token_ratio: float
    label_hint: str = "unknown"


def coloring_score(s: Sample) -> float:
    """Intellect coloring: education + lexical polish (higher = more coloring)."""
    edu = clip01((s.education_years - 8.0) / 12.0)
    lex = clip01(s.type_token_ratio / 0.75)
    sent = clip01(s.sentence_len / 18.0)
    return clip01(0.45 * edu + 0.35 * lex + 0.20 * sent)


def raw_impairment(s: Sample) -> float:
    pause = clip01(s.pause_ratio / 0.45)
    psr = clip01(s.pause_speech_ratio / 1.2)
    short = clip01(1.0 - s.sentence_len / 16.0)
    sparse_n = clip01(1.0 - s.noun_count / 25.0)
    return clip01(0.35 * pause + 0.25 * psr + 0.20 * short + 0.20 * sparse_n)


def band(score: float) -> str:
    if score < 0.33:
        return "low"
    if score < 0.55:
        return "medium"
    return "high"


@dataclass
class Draft:
    coloring_w: float
    residual_w: float
    coloring: float
    raw: float
    residual: float
    score: float
    band: str
    notes: str


def generate(sample: Sample, coloring_w: float, residual_w: float) -> Draft:
    col = coloring_score(sample)
    raw = raw_impairment(sample)
    residual = clip01(raw - coloring_w * col)
    score = clip01(residual_w * residual + (1.0 - residual_w) * raw)
    return Draft(
        coloring_w=coloring_w,
        residual_w=residual_w,
        coloring=round(col, 3),
        raw=round(raw, 3),
        residual=round(residual, 3),
        score=round(score, 3),
        band=band(score),
        notes="naive raw-heavy" if coloring_w < 0.35 else "coloring-corrected residual",
    )


def verify(draft: Draft, sample: Sample) -> tuple[bool, str]:
    reasons: list[str] = []
    if draft.coloring_w < 0.35:
        reasons.append(f"coloring_w {draft.coloring_w:.2f} < 0.35 (intellect coloring ignored)")
    if draft.residual_w < 0.45:
        reasons.append(f"residual_w {draft.residual_w:.2f} < 0.45")
    expected = clip01(draft.raw - draft.coloring_w * draft.coloring)
    if abs(expected - draft.residual) > 0.02:
        reasons.append("residual formula mismatch")
    if sample.education_years >= 16 and sample.pause_ratio >= 0.28 and draft.band == "low":
        reasons.append("high-edu + elevated pauses scored low — coloring swallowed the seer")
    if draft.residual >= 0.45 and draft.band == "low":
        reasons.append("residual>=0.45 but band=low")
    if reasons:
        return False, "; ".join(reasons)
    return True, "PASS: coloring subtracted; residual dominates; band consistent"


def update(draft: Draft, critique: str) -> tuple[float, float]:
    cw, rw = draft.coloring_w, draft.residual_w
    if "coloring_w" in critique:
        cw = min(0.55, cw + 0.20)
    if "residual_w" in critique or "coloring swallowed" in critique:
        rw = min(0.75, rw + 0.25)
    if "band=low" in critique:
        rw = min(0.80, rw + 0.15)
    return round(cw, 3), round(rw, 3)


def run_gvu(sample: Sample, max_passes: int = 3) -> list[dict[str, Any]]:
    cw, rw = 0.10, 0.20
    log: list[dict[str, Any]] = []
    draft = generate(sample, cw, rw)
    for i in range(1, max_passes + 1):
        ok, reason = verify(draft, sample)
        log.append({"pass": i, "ok": ok, "reason": reason, **asdict(draft)})
        if ok:
            break
        cw, rw = update(draft, reason)
        draft = generate(sample, cw, rw)
    return log


SAMPLE = Sample(
    pause_ratio=0.34,
    pause_speech_ratio=0.95,
    sentence_len=11.0,
    noun_count=14.0,
    education_years=18.0,
    type_token_ratio=0.62,
    label_hint="high-edu MCI-like pauses under polished lexicon",
)


def main() -> None:
    print("Sample:", SAMPLE)
    log = run_gvu(SAMPLE)
    for row in log:
        print(
            f"pass{row['pass']} ok={row['ok']} score={row['score']} "
            f"band={row['band']} raw={row['raw']} coloring={row['coloring']} "
            f"residual={row['residual']} cw={row['coloring_w']} rw={row['residual_w']}"
        )
        print("  ", row["reason"])
    print("BEFORE:", log[0]["score"], log[0]["band"], "AFTER:", log[-1]["score"], log[-1]["band"])


if __name__ == "__main__":
    main()
