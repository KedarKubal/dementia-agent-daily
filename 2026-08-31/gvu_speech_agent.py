#!/usr/bin/env python3
"""
Day 2026-08-31 — Pause-Aware Speech Risk Flag (GVU)
Opportunity: non-semantic pause features + ASR-style timing improve ADRD flags
beyond lexical text alone (Li et al., 2025, arXiv:2506.11119).

Generator → Verifier → Updater, 3 passes. No LLM required.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Literal

Risk = Literal["low", "medium", "high"]


SAMPLE_TRANSCRIPT = (
    "I went to the ... store yesterday and then I ... um ... I forgot why I "
    "went there. The ... the bread was ... I think on sale. My daughter said "
    "I should ... write a list but I ... I didn't."
)


@dataclass
class SpeechFeatures:
    word_count: int
    pause_count: int
    filled_pause_count: int
    speech_rate_wpm_proxy: float
    pause_ratio: float
    mean_pause_tokens: float


@dataclass
class Candidate:
    risk: Risk
    score: float
    rationale: str
    features: dict
    pass_index: int


@dataclass
class Critique:
    passed: bool
    reasons: list[str]


def extract_features(transcript: str, duration_sec: float = 28.0) -> SpeechFeatures:
    pause_tokens = re.findall(r"\.\.\.|\u2026", transcript)
    filled = re.findall(r"\b(um|uh|er|ah)\b", transcript, flags=re.I)
    words = re.findall(r"[A-Za-z']+", transcript)
    word_count = len(words)
    pause_count = len(pause_tokens)
    filled_count = len(filled)
    minutes = max(duration_sec / 60.0, 1e-6)
    speech_rate = word_count / minutes
    pause_ratio = (pause_count + filled_count) / max(word_count, 1)
    return SpeechFeatures(
        word_count=word_count,
        pause_count=pause_count,
        filled_pause_count=filled_count,
        speech_rate_wpm_proxy=round(speech_rate, 1),
        pause_ratio=round(pause_ratio, 3),
        mean_pause_tokens=float(pause_count),
    )


def generate(transcript: str, critique: Critique | None, prev: Candidate | None) -> Candidate:
    feats = extract_features(transcript)
    score = min(1.0, feats.pause_ratio * 1.8 + max(0, (110 - feats.speech_rate_wpm_proxy) / 200))
    if score >= 0.55:
        risk: Risk = "high"
    elif score >= 0.30:
        risk = "medium"
    else:
        risk = "low"

    # First pass often under-uses pause evidence (the paper's core gap).
    if critique is None:
        risk = "medium"
        rationale = (
            f"Lexical content mentions forgetting a list. Draft risk={risk}. "
            "Pause structure not yet weighted."
        )
        pass_index = 1
    else:
        missing = "; ".join(critique.reasons)
        rationale = (
            f"Revised after verifier: {missing}. "
            f"pause_ratio={feats.pause_ratio}, speech_rate={feats.speech_rate_wpm_proxy} wpm, "
            f"pauses={feats.pause_count}, filled={feats.filled_pause_count}."
        )
        if any("pause_ratio" in r or "speech_rate" in r for r in critique.reasons):
            if feats.pause_ratio >= 0.18 or feats.speech_rate_wpm_proxy < 100:
                risk = "high"
                score = max(score, 0.72)
        pass_index = (prev.pass_index + 1) if prev else 2

    return Candidate(
        risk=risk,
        score=round(score, 3),
        rationale=rationale,
        features=asdict(feats),
        pass_index=pass_index,
    )


def verify(candidate: Candidate) -> Critique:
    """
    Explicit, falsifiable success criterion:
    1. risk in {low, medium, high}
    2. rationale cites pause_ratio AND speech_rate with numeric values
    3. if pause_ratio >= 0.18 or speech_rate < 100, risk must be high
    4. if pause_ratio < 0.08 and speech_rate >= 130, risk must be low
    """
    reasons: list[str] = []
    f = candidate.features
    if candidate.risk not in ("low", "medium", "high"):
        reasons.append("risk label invalid")

    cites_pause = "pause_ratio" in candidate.rationale and re.search(
        r"pause_ratio\s*=\s*\d", candidate.rationale
    )
    cites_rate = "speech_rate" in candidate.rationale and re.search(
        r"speech_rate\s*=\s*\d", candidate.rationale
    )
    if not cites_pause:
        reasons.append("rationale must cite numeric pause_ratio")
    if not cites_rate:
        reasons.append("rationale must cite numeric speech_rate")

    if f["pause_ratio"] >= 0.18 or f["speech_rate_wpm_proxy"] < 100:
        if candidate.risk != "high":
            reasons.append(
                "pause_ratio>=0.18 or speech_rate<100 requires risk=high"
            )
    if f["pause_ratio"] < 0.08 and f["speech_rate_wpm_proxy"] >= 130:
        if candidate.risk != "low":
            reasons.append(
                "fluent speech (pause_ratio<0.08 and rate>=130) requires risk=low"
            )

    return Critique(passed=len(reasons) == 0, reasons=reasons or ["ok"])


def run_gvu(transcript: str, max_passes: int = 3) -> list[dict]:
    log = []
    critique: Critique | None = None
    cand: Candidate | None = None
    for i in range(1, max_passes + 1):
        cand = generate(transcript, critique, cand)
        critique = verify(cand)
        log.append(
            {
                "pass": i,
                "candidate": asdict(cand),
                "verifier_passed": critique.passed,
                "verifier_reasons": critique.reasons,
            }
        )
        if critique.passed:
            break
    return log


def main() -> None:
    print("=== SAMPLE (before / pass 1 is the naive draft) ===")
    print(SAMPLE_TRANSCRIPT)
    print()
    log = run_gvu(SAMPLE_TRANSCRIPT, max_passes=3)
    print(json.dumps(log, indent=2))
    final = log[-1]
    print()
    print(
        f"SMOKE: passes={len(log)} final_risk={final['candidate']['risk']} "
        f"verified={final['verifier_passed']}"
    )


if __name__ == "__main__":
    main()
