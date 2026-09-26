#!/usr/bin/env python3
"""Day 2026-09-27 — Ashtanga-gated digital therapeutic planner (GVU).

Generator drafts an 8-limb daily protocol for MCI / early-dementia risk reduction.
Verifier checks an explicit, falsifiable criterion (not vibes).
Updater feeds the critique back for 3 passes and logs deltas.

Success criterion (all must hold):
  1. Exactly the eight limbs in canonical order:
     yama, niyama, asana, pranayama, pratyahara, dharana, dhyana, samadhi
  2. Each limb has: minutes (int > 0), impurity_target (non-empty), measurable_check
  3. Total minutes in [20, 40]
  4. At least 4 limbs map to a known cognitive / lifestyle domain
     (sleep, gait, speech, attention, memory, social, breath, mood)
  5. No limb is a no-op placeholder ("tbd", "skip", "none")
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any

LIMBS = (
    "yama",
    "niyama",
    "asana",
    "pranayama",
    "pratyahara",
    "dharana",
    "dhyana",
    "samadhi",
)

DOMAIN_TOKENS = {
    "sleep",
    "gait",
    "speech",
    "attention",
    "memory",
    "social",
    "breath",
    "mood",
}

PLACEHOLDERS = {"tbd", "skip", "none", "", "n/a", "placeholder"}


@dataclass
class LimbBlock:
    name: str
    minutes: int
    impurity_target: str
    measurable_check: str
    domain: str = ""


@dataclass
class Plan:
    limbs: list[LimbBlock] = field(default_factory=list)
    notes: str = ""

    @property
    def total_minutes(self) -> int:
        return sum(b.minutes for b in self.limbs)


def generate(seed: dict[str, Any] | None = None, critique: str = "") -> Plan:
    """Draft (or revise) an 8-limb protocol.

    Pass 1 is intentionally incomplete so the loop is visible.
    Later passes repair whatever the verifier flagged.
    """
    seed = seed or {}
    pass_hint = seed.get("pass", 1)

    if pass_hint == 1 and not critique:
        return Plan(
            notes="naive first draft — only the obvious wellness bits",
            limbs=[
                LimbBlock("asana", 5, "stiffness", "stand up twice", "gait"),
                LimbBlock("pranayama", 3, "tbd", "breathe", "breath"),
                LimbBlock("dhyana", 4, "none", "sit quietly", ""),
                LimbBlock("memory_game", 8, "forgetfulness", "word list", "memory"),
                LimbBlock("samadhi", 0, "skip", "n/a", ""),
            ],
        )

    blocks = [
        LimbBlock(
            "yama",
            3,
            "harmful over-cueing / agitation from rushed prompts",
            "zero raised-voice events in the session window",
            "social",
        ),
        LimbBlock(
            "niyama",
            3,
            "inconsistent sleep hygiene (avidya of schedule)",
            "lights-out within 30 min of pledged bedtime",
            "sleep",
        ),
        LimbBlock(
            "asana",
            6,
            "sedentary gait variability",
            "2 sit-to-stand sets; note sway",
            "gait",
        ),
        LimbBlock(
            "pranayama",
            4,
            "sympathetic spike before cognitive load",
            "4-0-4 breath x8, HR drop >= 3 bpm or subjective 1-point calm",
            "breath",
        ),
        LimbBlock(
            "pratyahara",
            3,
            "sensory flooding that collapses attention",
            "60s eyes-soft, one sound tracked, phone face-down",
            "attention",
        ),
        LimbBlock(
            "dharana",
            6,
            "working-memory drift",
            "single-object hold: name 1 household object for 90s without switch",
            "attention",
        ),
        LimbBlock(
            "dhyana",
            5,
            "fragmented narrative / anomia under dual task",
            "90s continuous story about yesterday; count mid-sentence stops",
            "speech",
        ),
        LimbBlock(
            "samadhi",
            3,
            "residual rumination after practice",
            "30s silent settle; mood 0-10 logged; no new task launched",
            "mood",
        ),
    ]

    if "too long" in critique.lower():
        for b in blocks:
            b.minutes = max(2, b.minutes - 1)

    return Plan(
        notes="ashtanga-gated DTx: each limb removes one impurity before the next loads cognition",
        limbs=blocks,
    )


def verify(plan: Plan) -> dict[str, Any]:
    reasons: list[str] = []

    names = [b.name for b in plan.limbs]
    if names != list(LIMBS):
        reasons.append(
            f"limbs must be exactly {list(LIMBS)} in order; got {names}"
        )

    if not (20 <= plan.total_minutes <= 40):
        reasons.append(
            f"total minutes {plan.total_minutes} outside [20, 40]"
        )

    domain_hits = 0
    for b in plan.limbs:
        if b.minutes <= 0:
            reasons.append(f"{b.name}: minutes must be > 0")
        if b.impurity_target.strip().lower() in PLACEHOLDERS:
            reasons.append(f"{b.name}: impurity_target is a placeholder")
        if b.measurable_check.strip().lower() in PLACEHOLDERS:
            reasons.append(f"{b.name}: measurable_check is a placeholder")
        blob = (b.domain + " " + b.impurity_target + " " + b.measurable_check).lower()
        if any(tok in blob for tok in DOMAIN_TOKENS):
            domain_hits += 1

    if names == list(LIMBS) and domain_hits < 4:
        reasons.append(
            f"only {domain_hits} limbs map to a cognitive/lifestyle domain; need >= 4"
        )

    passed = len(reasons) == 0
    return {
        "pass": passed,
        "reasons": reasons,
        "total_minutes": plan.total_minutes,
        "limb_count": len(plan.limbs),
        "domain_hits": domain_hits,
    }


def updater(max_passes: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    critique = ""
    seed: dict[str, Any] = {"pass": 1}

    for i in range(1, max_passes + 1):
        seed["pass"] = i
        plan = generate(seed=seed, critique=critique)
        verdict = verify(plan)
        log.append(
            {
                "pass": i,
                "plan": {
                    "notes": plan.notes,
                    "total_minutes": plan.total_minutes,
                    "limbs": [asdict(b) for b in plan.limbs],
                },
                "verdict": verdict,
            }
        )
        if verdict["pass"]:
            break
        critique = "; ".join(verdict["reasons"])
        seed["last_fail"] = critique

    return log


def main() -> None:
    log = updater(max_passes=3)
    print(json.dumps(log, indent=2))
    first = log[0]["verdict"]
    last = log[-1]["verdict"]
    print("\n=== SMOKE ===")
    print(f"pass1 pass={first['pass']} minutes={first['total_minutes']} reasons={first['reasons']}")
    print(f"final pass={last['pass']} minutes={last['total_minutes']} reasons={last['reasons']}")


if __name__ == "__main__":
    main()
