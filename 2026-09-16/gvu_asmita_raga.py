#!/usr/bin/env python3
"""Day 2026-09-16 — Asmita/Raga speech-risk GVU agent.

Core insight (YS II.6–II.7 + speech-biomarker literature):
  Asmita = identifying the *seer* (person / self-report / caregiver view)
  with the *instrument* (acoustic fluency). Raga = dwelling on pleasure:
  treating fluent, pleasant speech as proof of health.

Naive models collapse those channels. This loop refuses that collapse.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


# --- labeled toy sample (picture-description + 1-item self-rating) ---
SAMPLE = {
    "id": "pwd_asmita_01",
    "words_per_min": 118.0,  # fluent instrument
    "pause_ratio": 0.14,  # low pauses — sounds "pleasant"
    "semantic_units": 4,  # thin content (expected ~10 on cookie-theft analog)
    "pronoun_noun_ratio": 1.8,  # empty reference
    "self_rating_cognition": 9,  # seer: "I am fine" (0-10)
    "caregiver_concern": 7,  # 0-10
}


@dataclass
class Flag:
    fluency_score: float
    content_score: float
    seer_score: float
    instrument_weight: float
    seer_weight: float
    fused: float
    band: str
    identified_with_instrument: bool
    pleasure_dominated: bool

    def pretty(self) -> str:
        return (
            f"band={self.band} fused={self.fused:.3f} "
            f"fluency={self.fluency_score:.2f} content={self.content_score:.2f} "
            f"seer={self.seer_score:.2f} inst_w={self.instrument_weight:.2f} "
            f"seer_w={self.seer_weight:.2f} asmita={self.identified_with_instrument} "
            f"raga={self.pleasure_dominated}"
        )


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def generator(sample: dict[str, Any], instrument_weight: float) -> Flag:
    """Draft risk. High instrument_weight = asmita (seer collapsed into fluency)."""
    fluency = clip01((sample["words_per_min"] / 140.0) * (1.0 - sample["pause_ratio"]))
    content_risk = clip01(
        (1.0 - sample["semantic_units"] / 10.0) * 0.6
        + min(sample["pronoun_noun_ratio"] / 2.5, 1.0) * 0.4
    )
    seer_risk = clip01(
        (sample["self_rating_cognition"] / 10.0) * 0.4
        + (sample["caregiver_concern"] / 10.0) * 0.6
        + abs(sample["self_rating_cognition"] - (10 - sample["caregiver_concern"])) / 10.0 * 0.3
    )
    seer_w = 1.0 - instrument_weight
    instrument_protective = 1.0 - fluency
    fused = clip01(instrument_weight * instrument_protective + seer_w * (0.5 * content_risk + 0.5 * seer_risk))
    identified = instrument_weight >= 0.7
    pleasure = fluency >= 0.65 and content_risk >= 0.45 and instrument_weight >= 0.55
    if fused < 0.33:
        band = "low"
    elif fused < 0.60:
        band = "medium"
    else:
        band = "high"
    return Flag(
        fluency_score=fluency,
        content_score=content_risk,
        seer_score=seer_risk,
        instrument_weight=instrument_weight,
        seer_weight=seer_w,
        fused=fused,
        band=band,
        identified_with_instrument=identified,
        pleasure_dominated=pleasure,
    )


def verifier(flag: Flag) -> tuple[bool, str]:
    """Falsifiable criteria:
    1. Seer and instrument must both have weight >= 0.30 (no asmita collapse).
    2. Must not be pleasure-dominated (fluent + empty content must not read as safe via fluency).
    3. On this sample, fused must be >= 0.55.
    """
    reasons: list[str] = []
    if flag.instrument_weight > 0.70 or flag.seer_weight < 0.30:
        reasons.append(
            f"ASMITA: instrument_weight={flag.instrument_weight:.2f} "
            "collapses seer into speech instrument (need seer_w>=0.30)"
        )
    if flag.pleasure_dominated:
        reasons.append(
            "RAGA: fluency treated as pleasure/health despite thin semantics "
            f"(fluency={flag.fluency_score:.2f}, content_risk={flag.content_score:.2f})"
        )
    if flag.fused < 0.55:
        reasons.append(f"UNDERCALL: fused={flag.fused:.3f} < 0.55 on fluent-but-empty + seer-mismatch sample")
    if flag.identified_with_instrument:
        reasons.append("identified_with_instrument=True (seer == instrument)")
    ok = len(reasons) == 0
    return ok, "PASS" if ok else "FAIL: " + "; ".join(reasons)


def updater(flag: Flag, critique: str) -> float:
    w = flag.instrument_weight
    if "ASMITA" in critique or "identified_with_instrument" in critique:
        w = min(w, 0.45)
    if "RAGA" in critique or "UNDERCALL" in critique:
        w = min(w, 0.40)
    return w


def run_gvu(sample: dict[str, Any], passes: int = 3) -> list[dict[str, Any]]:
    w = 0.85
    log: list[dict[str, Any]] = []
    for i in range(1, passes + 1):
        flag = generator(sample, w)
        ok, reason = verifier(flag)
        row = {"pass": i, "ok": ok, "reason": reason, **asdict(flag)}
        log.append(row)
        print(f"PASS {i}: {flag.pretty()}")
        print(f"  verifier: {reason}")
        if ok:
            break
        w = updater(flag, reason)
        print(f"  updater → instrument_weight={w:.2f}")
    return log


if __name__ == "__main__":
    print("SAMPLE", SAMPLE["id"])
    print("BEFORE (pass 1 expected FAIL — asmita+raga)")
    log = run_gvu(SAMPLE, passes=3)
    print("AFTER", log[-1]["band"], f"{log[-1]['fused']:.3f}", "ok=" + str(log[-1]["ok"]))
