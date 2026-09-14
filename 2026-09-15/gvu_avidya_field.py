#!/usr/bin/env python3
"""Day 2026-09-15 — Four-state avidya-field dementia risk flag.

Patanjali II.4 (Vivekananda): Ignorance is the productive field of those
that follow, whether dormant, attenuated, overpowered, or expanded.

Generator starts with a binary 'fine vs sick' label (the avidya of taking
transient speech change as a stable identity).
Verifier requires a four-state field with explicit rules.
Updater redistributes mass across dormant / attenuated / interrupted / expanded.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict, List


STATES = ("dormant", "attenuated", "interrupted", "expanded")


@dataclass
class Sample:
    """Synthetic connected-speech + denial features."""

    speech_rate_z: float  # negative = slower than age-norm
    pause_ratio: float  # 0-1 fraction of silence
    informativeness: float  # 0-1 lexical content density
    denial: float  # 0-1 self-report "I am fine / just aging"


@dataclass
class Output:
    pass_id: int
    mode: str
    states: Dict[str, float]
    label: str
    follow_up: str
    notes: str


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _norm(states: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, states[s]) for s in STATES) or 1.0
    return {s: round(max(0.0, states[s]) / total, 4) for s in STATES}


def generate(sample: Sample, critique: str | None, prior: Output | None) -> Output:
    """Pass 1 is binary-collapsed. Later passes open the four-state field."""
    impairment = _clip01(
        0.45 * max(0.0, -sample.speech_rate_z) / 2.0
        + 0.35 * sample.pause_ratio
        + 0.20 * (1.0 - sample.informativeness)
    )
    seed = _clip01(0.5 * impairment + 0.5 * sample.denial)

    if prior is None:
        if impairment >= 0.45:
            states = {"dormant": 0.0, "attenuated": 0.0, "interrupted": 0.0, "expanded": 1.0}
            label = "sick"
        else:
            states = {"dormant": 1.0, "attenuated": 0.0, "interrupted": 0.0, "expanded": 0.0}
            label = "fine"
        follow_up = "none" if label == "fine" else "clinic"
        return Output(1, "binary_collapse", states, label, follow_up, "collapsed field")

    expanded = _clip01(impairment * (0.55 + 0.45 * sample.pause_ratio) * (1.0 if sample.speech_rate_z < -0.6 else 0.6))
    interrupted = _clip01((1.0 - sample.informativeness) * 0.7 * (1.0 - expanded))
    attenuated = _clip01(impairment * 0.5 * (1.0 - sample.denial))
    dormant = _clip01(seed * 0.8 if expanded < 0.35 else 0.12)
    states = _norm(
        {
            "dormant": dormant + 0.08,
            "attenuated": attenuated + 0.08,
            "interrupted": interrupted + 0.08,
            "expanded": expanded + 0.05,
        }
    )
    top = max(states, key=states.get)
    follow_up = {
        "expanded": "clinic",
        "interrupted": "repeat_speech_48h",
        "attenuated": "home_monitor",
        "dormant": "seed_watch",
    }[top]
    return Output(
        prior.pass_id + 1,
        "four_state_field",
        states,
        top,
        follow_up,
        critique or "opened field",
    )


def verify(out: Output, sample: Sample) -> tuple[bool, str]:
    reasons: List[str] = []
    s = out.states
    if set(s) != set(STATES):
        reasons.append("missing_states")
    total = sum(s.get(k, 0.0) for k in STATES)
    if abs(total - 1.0) > 0.01:
        reasons.append(f"mass={total:.3f}_not_1")
    if s.get("expanded", 0) >= 0.35:
        if not (sample.speech_rate_z < -0.5 and sample.pause_ratio >= 0.22):
            reasons.append("expanded_without_dual_acoustic")
    residual = _clip01(0.4 * max(0.0, -sample.speech_rate_z) / 2 + 0.6 * sample.denial)
    if out.label == "dormant" and out.follow_up == "none" and residual > 0.15:
        reasons.append("dormant_dismissed_with_seed")
    if out.label in {"fine", "sick"}:
        reasons.append("binary_label_is_avidya")
    if out.follow_up == "none":
        reasons.append("none_followup_forbidden")
    ok = len(reasons) == 0
    return ok, "PASS" if ok else "FAIL: " + ",".join(reasons)


def run(sample: Sample, max_passes: int = 3) -> List[Output]:
    log: List[Output] = []
    critique: str | None = None
    prior: Output | None = None
    for _ in range(max_passes):
        out = generate(sample, critique, prior)
        ok, reason = verify(out, sample)
        out.notes = reason
        log.append(out)
        if ok:
            break
        critique = reason
        prior = out
    return log


SAMPLE = Sample(speech_rate_z=-1.15, pause_ratio=0.31, informativeness=0.58, denial=0.72)


if __name__ == "__main__":
    passes = run(SAMPLE)
    print("SAMPLE", asdict(SAMPLE))
    for p in passes:
        print(
            f"pass={p.pass_id} mode={p.mode} label={p.label} "
            f"follow_up={p.follow_up} states={p.states} {p.notes}"
        )
    print("BEFORE", asdict(passes[0]))
    print("AFTER", asdict(passes[-1]))
    with open("run.json", "w", encoding="utf-8") as fh:
        json.dump([asdict(p) for p in passes], fh, indent=2)
