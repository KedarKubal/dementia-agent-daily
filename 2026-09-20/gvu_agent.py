#!/usr/bin/env python3
"""
Day 2026-09-20 — Two-stage PSD + fluid biomarker stage flag (GVU).

Insight from speech digital biomarker + fluid biomarkers (Alz Res Ther 2025):
percentage of silence duration (PSD) co-moves with GFAP / p-Tau217
in a *two-stage* pattern as amyloid deposition progresses — a single
linear risk score hides the inflection.

Generator drafts a stage estimate.
Verifier requires:
  - both acoustic (psd) and fluid (gfap or ptau217) channels used
  - stage in {pre_inflection, inflection, post_inflection}
  - stage_confidence >= 0.60
  - weights: acoustic_w >= 0.25 and fluid_w >= 0.25
Updater raises the under-weighted channel and re-bins the stage.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

Stage = Literal["pre_inflection", "inflection", "post_inflection"]


@dataclass
class Features:
    psd: float
    gfap_pg_ml: float
    ptau217_pg_ml: float
    age: int


@dataclass
class Draft:
    stage: Stage
    score: float
    confidence: float
    acoustic_w: float
    fluid_w: float
    reason: str


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def acoustic_load(psd: float) -> float:
    return _clip((psd - 0.18) / 0.28)


def fluid_load(gfap: float, ptau: float) -> float:
    g = _clip((gfap - 80.0) / 160.0)
    t = _clip((ptau - 0.20) / 0.80)
    return 0.55 * g + 0.45 * t


def bin_stage(combo: float) -> Stage:
    if combo < 0.35:
        return "pre_inflection"
    if combo < 0.62:
        return "inflection"
    return "post_inflection"


def generate(feat: Features, acoustic_w: float, fluid_w: float) -> Draft:
    a = acoustic_load(feat.psd)
    f = fluid_load(feat.gfap_pg_ml, feat.ptau217_pg_ml)
    s = acoustic_w + fluid_w
    acoustic_w, fluid_w = acoustic_w / s, fluid_w / s
    combo = acoustic_w * a + fluid_w * f
    stage = bin_stage(combo)
    agree = 1.0 - abs(a - f)
    conf = _clip(0.35 + 0.45 * agree + 0.20 * min(acoustic_w, fluid_w) * 4)
    reason = (
        f"psd={feat.psd:.3f}->a={a:.3f}; "
        f"gfap={feat.gfap_pg_ml:.1f},ptau={feat.ptau217_pg_ml:.3f}->f={f:.3f}; "
        f"combo={combo:.3f} aw={acoustic_w:.2f} fw={fluid_w:.2f}"
    )
    return Draft(stage=stage, score=round(combo, 3), confidence=round(conf, 3),
                 acoustic_w=round(acoustic_w, 3), fluid_w=round(fluid_w, 3),
                 reason=reason)


def verify(draft: Draft) -> tuple[bool, str]:
    reasons = []
    if draft.acoustic_w < 0.25:
        reasons.append(f"acoustic_w {draft.acoustic_w:.2f} < 0.25")
    if draft.fluid_w < 0.25:
        reasons.append(f"fluid_w {draft.fluid_w:.2f} < 0.25")
    if draft.stage not in ("pre_inflection", "inflection", "post_inflection"):
        reasons.append("invalid stage")
    if draft.confidence < 0.60:
        reasons.append(f"confidence {draft.confidence:.3f} < 0.60")
    if not reasons:
        return True, "PASS: two-stage dual-channel criterion met"
    return False, "FAIL: " + "; ".join(reasons)


def update_weights(draft: Draft, ok: bool) -> tuple[float, float]:
    if ok:
        return draft.acoustic_w, draft.fluid_w
    aw, fw = draft.acoustic_w, draft.fluid_w
    if aw < 0.25:
        aw = 0.40
    if fw < 0.25:
        fw = 0.45
    if draft.confidence < 0.60:
        aw, fw = 0.50, 0.50
    return aw, fw


def gvu_loop(feat: Features, passes: int = 3) -> list[dict]:
    aw, fw = 0.85, 0.15
    log = []
    for i in range(1, passes + 1):
        draft = generate(feat, aw, fw)
        ok, critique = verify(draft)
        log.append({"pass": i, "ok": ok, "critique": critique, **asdict(draft)})
        print(f"--- pass {i} ---")
        print(f"  stage={draft.stage} score={draft.score} conf={draft.confidence}")
        print(f"  aw={draft.acoustic_w} fw={draft.fluid_w}")
        print(f"  {critique}")
        print(f"  {draft.reason}")
        if ok:
            break
        aw, fw = update_weights(draft, ok)
    return log


def main() -> None:
    sample = Features(psd=0.41, gfap_pg_ml=210.0, ptau217_pg_ml=0.72, age=74)
    print("SAMPLE", sample)
    log = gvu_loop(sample)
    print("BEFORE", {k: log[0][k] for k in ("pass", "stage", "score", "ok", "acoustic_w", "fluid_w")})
    print("AFTER ", {k: log[-1][k] for k in ("pass", "stage", "score", "ok", "acoustic_w", "fluid_w")})


if __name__ == "__main__":
    main()
