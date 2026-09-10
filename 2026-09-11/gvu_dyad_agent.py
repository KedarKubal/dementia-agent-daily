#!/usr/bin/env python3
"""Day 2026-09-11 GVU: dyadic wearable proximity + caregiver movement → burden/ADL flag.

Underexploited insight (Chen et al., 2023, Alz & Dem): increases in PWD–CG
proximity predict CG burden (r=0.57) and increases in CG (not PWD) movement
predict ADL decline (r=-0.55). Most products score the patient alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SAMPLE = {
    "id": "dyad-014",
    "weeks": 8,
    "proximity_hours_week0": 3.2,
    "proximity_hours_week8": 6.8,
    "cg_steps_week0": 4200,
    "cg_steps_week8": 7100,
    "pwd_steps_week0": 2100,
    "pwd_steps_week8": 1900,
    "zbi_week0": 28,
}


@dataclass
class Draft:
    burden_delta_pred: float
    adl_risk: str
    flag: str
    rationale: str
    features_used: list[str]
    pass_n: int = 0
    notes: str = ""


def deltas(s: dict[str, Any]) -> dict[str, float]:
    return {
        "d_prox": s["proximity_hours_week8"] - s["proximity_hours_week0"],
        "d_cg": s["cg_steps_week8"] - s["cg_steps_week0"],
        "d_pwd": s["pwd_steps_week8"] - s["pwd_steps_week8"] if False else s["pwd_steps_week8"] - s["pwd_steps_week0"],
    }


def generate(sample: dict[str, Any], critique: str | None, prior: Draft | None) -> Draft:
    d = deltas(sample)
    if prior is None:
        score = 0.2 if d["d_pwd"] < 0 else 0.0
        return Draft(
            burden_delta_pred=score,
            adl_risk="unknown",
            flag="watch",
            rationale=f"PWD step change only ({d['d_pwd']:.0f}). Predicted burden delta={score}.",
            features_used=["pwd_steps"],
            pass_n=0,
            notes="patient-only baseline",
        )

    burden = 0.15 * d["d_prox"] + 0.00004 * max(d["d_cg"], 0)
    adl = "high" if d["d_cg"] > 1500 and d["d_pwd"] <= 0 else ("moderate" if d["d_cg"] > 500 else "low")
    flag = "high" if burden >= 0.45 and adl == "high" else ("moderate" if burden >= 0.25 else "low")
    feats = ["d_proximity_hours", "d_cg_steps", "d_pwd_steps"]
    rationale = (
        f"d_proximity={d['d_prox']:.1f}h, d_cg_steps={d['d_cg']:.0f}, d_pwd_steps={d['d_pwd']:.0f}. "
        f"Predicted ZBI rise={burden:.3f}; ADL risk={adl}; flag={flag}."
    )
    return Draft(burden, adl, flag, rationale, feats, prior.pass_n + 1, critique or "")


def verify(draft: Draft, sample: dict[str, Any]) -> tuple[bool, str]:
    d = deltas(sample)
    reasons = []
    if "d_proximity_hours" not in draft.features_used:
        reasons.append("missing d_proximity_hours")
    if "d_cg_steps" not in draft.features_used:
        reasons.append("missing d_cg_steps")
    if d["d_prox"] > 2.0 and d["d_cg"] > 1500 and d["d_pwd"] <= 0:
        if draft.flag != "high" or draft.adl_risk != "high":
            reasons.append(
                f"dyadic high-risk pattern (d_prox={d['d_prox']:.1f}, d_cg={d['d_cg']:.0f}, "
                f"d_pwd={d['d_pwd']:.0f}) but flag={draft.flag} adl={draft.adl_risk}"
            )
    if "d_proximity" not in draft.rationale:
        reasons.append("rationale missing proximity delta")
    if "d_cg_steps" not in draft.rationale:
        reasons.append("rationale missing CG movement delta")
    if reasons:
        return False, "FAIL: " + "; ".join(reasons) + ". Rebuild using dyadic proximity+CG-movement, not PWD-only."
    return True, "PASS: dyadic proximity+CG-movement rule satisfied."


def run_gvu(sample: dict[str, Any], max_passes: int = 3) -> list[Draft]:
    log: list[Draft] = []
    critique = None
    draft = None
    for i in range(max_passes):
        draft = generate(sample, critique, draft)
        ok, critique = verify(draft, sample)
        draft.notes = critique
        log.append(draft)
        print(f"\n=== PASS {i} ===")
        print(f"burden_pred={draft.burden_delta_pred:.3f} adl={draft.adl_risk} flag={draft.flag}")
        print(f"features={draft.features_used}")
        print(f"rationale: {draft.rationale}")
        print(f"verifier: {critique}")
        if ok:
            print("Stopping: verifier passed.")
            break
    return log


if __name__ == "__main__":
    print("SAMPLE", SAMPLE)
    history = run_gvu(SAMPLE, 3)
    print("\n--- BEFORE (pass 0) ---")
    print(history[0])
    print("--- AFTER (last pass) ---")
    print(history[-1])
