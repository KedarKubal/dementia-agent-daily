#!/usr/bin/env python3
"""Day 2026-09-12 — Rtambhara fusion speech+fluid risk flag (GVU)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


THRESH = {"low": 0.33, "medium": 0.55, "high": 0.75}


@dataclass
class Sample:
    pause_silence_pct: float
    linguistic_informativeness: float
    gfap_z: float | None
    ptau217_z: float | None
    age: int
    label: str


def band(score: float) -> str:
    if score >= THRESH["high"]:
        return "high"
    if score >= THRESH["medium"]:
        return "medium"
    if score >= THRESH["low"]:
        return "low"
    return "watch"


def speech_score(s: Sample) -> float:
    return max(0.0, min(1.0, 0.55 * s.pause_silence_pct + 0.45 * (1.0 - s.linguistic_informativeness)))


def fluid_score(s: Sample) -> float | None:
    if s.gfap_z is None and s.ptau217_z is None:
        return None
    parts = []
    if s.gfap_z is not None:
        parts.append(max(0.0, min(1.0, (s.gfap_z + 1.0) / 3.0)))
    if s.ptau217_z is not None:
        parts.append(max(0.0, min(1.0, (s.ptau217_z + 1.0) / 3.0)))
    return sum(parts) / len(parts)


def generate(s: Sample, fluid_w: float, force_clinical: bool) -> dict[str, Any]:
    sp = speech_score(s)
    fl = fluid_score(s)
    if fl is None:
        score = sp
        grade = "clinical_grade" if force_clinical else "screening_only"
        used_w = 0.0
    else:
        used_w = fluid_w
        score = (1.0 - used_w) * sp + used_w * fl
        grade = "clinical_grade" if used_w >= 0.35 else "screening_only"
    score = round(max(0.0, min(1.0, score)), 3)
    return {
        "sample": s.label,
        "speech": round(sp, 3),
        "fluid": None if fl is None else round(fl, 3),
        "fluid_w": used_w,
        "score": score,
        "band": band(score),
        "grade": grade,
    }


def verify(out: dict[str, Any], has_fluids: bool) -> tuple[bool, str]:
    reasons = []
    if not (0.0 <= out["score"] <= 1.0):
        reasons.append("score out of [0,1]")
    if out["band"] != band(out["score"]):
        reasons.append("band mismatch")
    if has_fluids and out["fluid_w"] < 0.35:
        reasons.append("fluids present but fluid_w < 0.35 (rtambhara: common-object speech must not dominate)")
    if not has_fluids and out["grade"] == "clinical_grade":
        reasons.append("speech-only cannot be clinical_grade (testimony/inference only)")
    if has_fluids and out["grade"] != "clinical_grade" and out["fluid_w"] >= 0.35:
        reasons.append("fusion weight sufficient but grade not clinical")
    if reasons:
        return False, "; ".join(reasons)
    return True, "pass: fusion/grade consistent with rtambhara criterion"


def update(fluid_w: float, force_clinical: bool, critique: str) -> tuple[float, bool]:
    if "fluid_w < 0.35" in critique:
        fluid_w = 0.55
    if "speech-only cannot be clinical" in critique:
        force_clinical = False
    return fluid_w, force_clinical


def run_gvu(s: Sample, max_passes: int = 3) -> list[dict[str, Any]]:
    has_fluids = fluid_score(s) is not None
    fluid_w, force_clinical = 0.15, True
    log = []
    for i in range(1, max_passes + 1):
        out = generate(s, fluid_w, force_clinical)
        ok, reason = verify(out, has_fluids)
        rec = {"pass": i, "ok": ok, "reason": reason, **out}
        log.append(rec)
        if ok:
            break
        fluid_w, force_clinical = update(fluid_w, force_clinical, reason)
    return log


SAMPLE = Sample(
    pause_silence_pct=0.42,
    linguistic_informativeness=0.38,
    gfap_z=1.4,
    ptau217_z=1.1,
    age=71,
    label="story-recall-01",
)


def main() -> None:
    log = run_gvu(SAMPLE)
    print("=== smoke sample story-recall-01 ===")
    for rec in log:
        print(
            f"pass {rec['pass']}: score={rec['score']} band={rec['band']} "
            f"grade={rec['grade']} fluid_w={rec['fluid_w']} ok={rec['ok']} | {rec['reason']}"
        )
    print("BEFORE:", {k: log[0][k] for k in ("score", "band", "grade", "fluid_w")})
    print("AFTER :", {k: log[-1][k] for k in ("score", "band", "grade", "fluid_w")})


if __name__ == "__main__":
    main()
