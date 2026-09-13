#!/usr/bin/env python3
"""
Day 2026-09-14 — Klesha-Attenuating Personalized Risk-Reduction Planner
Generator–Verifier–Updater loop (Stanford CS329A GVU).

Insight prototype: SMARRT-style personalized multidomain plans work only when
≥2 active risk factors get a measurable weekly dose. Maps Patanjali's kleshas
(ignorance, egoism, attachment, aversion, clinging-to-life) onto dementia
modifiable risks so the plan is falsifiable, not generic wellness copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


KLESHA_MAP = {
    "cognitive_inactivity": "avidya",
    "physical_inactivity": "abhinivesha",
    "poor_diet": "raga",
    "depression_anxiety": "dvesha",
    "social_isolation": "asmita",
    "sleep_disruption": "abhinivesha",
    "unmanaged_hypertension": "avidya",
    "hearing_loss_untreated": "avidya",
}

DOSE_RULES = {
    "cognitive_inactivity": ("sessions", 3, "cognitive sessions / week"),
    "physical_inactivity": ("minutes", 150, "minutes moderate walk / week"),
    "poor_diet": ("meals", 10, "Mediterranean-pattern meals / week"),
    "depression_anxiety": ("sessions", 2, "brief behavioral sessions / week"),
    "social_isolation": ("contacts", 3, "planned social contacts / week"),
    "sleep_disruption": ("nights", 5, "protected 7h sleep nights / week"),
    "unmanaged_hypertension": ("checks", 3, "home BP checks / week"),
    "hearing_loss_untreated": ("hours", 20, "aided listening hours / week"),
}


@dataclass
class Plan:
    weights: Dict[str, float]
    doses: Dict[str, float]
    notes: List[str] = field(default_factory=list)

    def score(self) -> float:
        active = [k for k, v in self.weights.items() if v >= 0.4]
        if not active:
            return 0.0
        hits = 0.0
        for k in active:
            unit, target, _ = DOSE_RULES[k]
            given = self.doses.get(k, 0.0)
            hits += min(1.0, given / target)
        return hits / len(active)


def generate(profile: Dict[str, float], critique: str | None = None) -> Plan:
    """Draft a 2-week plan. First pass is naive (treats only the top factor)."""
    ranked = sorted(profile.items(), key=lambda kv: kv[1], reverse=True)
    doses: Dict[str, float] = {k: 0.0 for k in profile}
    notes: List[str] = []

    if critique is None:
        top, _ = ranked[0]
        unit, target, label = DOSE_RULES[top]
        doses[top] = target * 0.5
        notes.append(f"naive: only {top} at 50% of {label}")
    else:
        for k, v in profile.items():
            if v >= 0.4:
                _, target, label = DOSE_RULES[k]
                doses[k] = float(target)
                notes.append(f"updated: {k} full {label}")
        notes.append(f"applied critique: {critique[:160]}")
    return Plan(weights=dict(profile), doses=doses, notes=notes)


def verify(plan: Plan) -> Tuple[bool, str]:
    """
    Success criterion (falsifiable):
      1. At least 2 profile factors with weight >= 0.4 receive a dose.
      2. Each of those doses meets 100% of the published weekly target.
      3. Composite coverage score >= 0.90.
    """
    active = [k for k, v in plan.weights.items() if v >= 0.4]
    covered = [k for k in active if plan.doses.get(k, 0) >= DOSE_RULES[k][1] - 1e-9]
    reasons = []
    if len(covered) < 2:
        reasons.append(f"need >=2 covered active domains, got {len(covered)}/{len(active)}")
    for k in active:
        need = DOSE_RULES[k][1]
        got = plan.doses.get(k, 0)
        if got < need:
            reasons.append(f"{k} dose {got} < target {need}")
    sc = plan.score()
    if sc < 0.90:
        reasons.append(f"coverage {sc:.3f} < 0.90")
    ok = not reasons
    return ok, "PASS" if ok else "; ".join(reasons)


def updater_loop(profile: Dict[str, float], max_passes: int = 3) -> List[dict]:
    log: List[dict] = []
    critique = None
    for i in range(1, max_passes + 1):
        plan = generate(profile, critique)
        ok, reason = verify(plan)
        log.append(
            {
                "pass": i,
                "ok": ok,
                "reason": reason,
                "score": round(plan.score(), 3),
                "doses": dict(plan.doses),
                "notes": list(plan.notes),
            }
        )
        if ok:
            break
        critique = reason
    return log


SAMPLE = {
    "cognitive_inactivity": 0.8,
    "physical_inactivity": 0.7,
    "poor_diet": 0.3,
    "depression_anxiety": 0.55,
    "social_isolation": 0.2,
    "sleep_disruption": 0.15,
    "unmanaged_hypertension": 0.1,
    "hearing_loss_untreated": 0.0,
}


def main() -> None:
    print("=== SAMPLE PROFILE (active if weight>=0.4) ===")
    for k, v in SAMPLE.items():
        flag = "ACTIVE" if v >= 0.4 else "quiet"
        print(f"  {k:28s} {v:.2f}  {flag}  klesha={KLESHA_MAP[k]}")

    log = updater_loop(SAMPLE, max_passes=3)
    print("\n=== GVU PASSES ===")
    for row in log:
        print(
            f"pass {row['pass']}: ok={row['ok']} score={row['score']} "
            f"| {row['reason']}"
        )
        print(f"  doses={row['doses']}")
        print(f"  notes={row['notes']}")

    print("\nBEFORE (pass 1) vs AFTER (last pass)")
    print("  before doses:", log[0]["doses"])
    print("  after  doses:", log[-1]["doses"])
    print("  before score:", log[0]["score"], "after score:", log[-1]["score"])


if __name__ == "__main__":
    main()
