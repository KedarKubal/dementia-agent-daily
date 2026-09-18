#!/usr/bin/env python3
"""
Day 2026-09-19 — Vipaka triad flag (species / life-span / bhoga).

Generator: drafts a dementia-risk output from stored speech+behavior impressions.
Verifier: requires an explicit triad — phenotype class, remaining independent-life
years band, and bhoga (care-burden) score — with stated weight floors.
Updater: feeds the critique back for 3 passes.

Success criterion (falsifiable):
  PASS iff
    - phenotype in {typical_ad, atypical, mci_stable, mixed}
    - years_indep in [0.5, 12.0]
    - bhoga in [0.0, 1.0]
    - w_species >= 0.25 and w_life >= 0.25 and w_bhoga >= 0.25
    - composite >= 0.45
    - band in {medium, high}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any


SAMPLE = {
    "psd": 0.31,
    "speech_rate_wps": 1.9,
    "pause_cv": 0.62,
    "gait_cv": 0.28,
    "night_wake_n": 3,
    "caregiver_hours": 4.5,
    "age": 74,
    "apoe_e4": 1,
}


@dataclass
class Draft:
    phenotype: str
    years_indep: float
    bhoga: float
    w_species: float
    w_life: float
    w_bhoga: float
    composite: float
    band: str
    notes: str


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_features(s: dict[str, Any]) -> dict[str, float]:
    psd = float(s["psd"])
    rate = float(s["speech_rate_wps"])
    pcv = float(s["pause_cv"])
    gcv = float(s["gait_cv"])
    night = float(s["night_wake_n"])
    hours = float(s["caregiver_hours"])
    age = float(s["age"])
    e4 = float(s["apoe_e4"])

    speech = _clip(0.55 * psd / 0.35 + 0.25 * (2.4 - rate) / 1.2 + 0.20 * pcv, 0, 1)
    body = _clip(0.6 * gcv / 0.4 + 0.4 * night / 5.0, 0, 1)
    load = _clip(hours / 8.0, 0, 1)
    demo = _clip((age - 60) / 30.0 + 0.15 * e4, 0, 1)
    return {"speech": speech, "body": body, "load": load, "demo": demo}


def generate(sample: dict[str, Any], critique: str | None, pass_n: int) -> Draft:
    f = score_features(sample)

    if pass_n == 1 or not critique:
        composite = 0.7 * f["speech"] + 0.3 * f["demo"]
        return Draft(
            phenotype="unknown",
            years_indep=0.0,
            bhoga=0.0,
            w_species=0.10,
            w_life=0.10,
            w_bhoga=0.10,
            composite=round(composite, 3),
            band="low" if composite < 0.45 else "medium",
            notes="pass1 current-state only; triad missing",
        )

    if pass_n == 2:
        if f["speech"] > 0.55 and f["demo"] > 0.4:
            pheno = "typical_ad"
            years = 4.5 - 2.0 * f["speech"]
        elif f["speech"] > 0.4:
            pheno = "mci_stable"
            years = 7.0 - 1.5 * f["speech"]
        else:
            pheno = "atypical"
            years = 8.0
        bhoga = 0.4 * f["load"] + 0.3 * f["body"]
        ws, wl, wb = 0.40, 0.40, 0.15
        composite = ws * f["speech"] + wl * (1 - years / 12.0) + wb * bhoga
        band = "medium" if composite >= 0.45 else "low"
        return Draft(
            phenotype=pheno,
            years_indep=round(_clip(years, 0.5, 12), 2),
            bhoga=round(_clip(bhoga, 0, 1), 3),
            w_species=ws,
            w_life=wl,
            w_bhoga=wb,
            composite=round(composite, 3),
            band=band,
            notes="pass2 triad partial; bhoga under-weighted",
        )

    if f["speech"] >= 0.55 and f["body"] >= 0.35:
        pheno = "typical_ad"
        years = 3.8 - 1.8 * f["speech"] + 0.4 * (1 - f["demo"])
    elif f["speech"] >= 0.40:
        pheno = "mixed"
        years = 6.2 - 1.4 * f["speech"]
    elif f["load"] >= 0.5:
        pheno = "atypical"
        years = 7.5
    else:
        pheno = "mci_stable"
        years = 9.0 - f["speech"]
    years = _clip(years, 0.5, 12)
    bhoga = _clip(0.45 * f["load"] + 0.30 * f["body"] + 0.25 * f["speech"], 0, 1)
    ws, wl, wb = 0.34, 0.33, 0.33
    life_risk = 1.0 - (years / 12.0)
    composite = ws * f["speech"] + wl * life_risk + wb * bhoga
    if composite >= 0.62:
        band = "high"
    elif composite >= 0.45:
        band = "medium"
    else:
        band = "low"
    return Draft(
        phenotype=pheno,
        years_indep=round(years, 2),
        bhoga=round(bhoga, 3),
        w_species=ws,
        w_life=wl,
        w_bhoga=wb,
        composite=round(composite, 3),
        band=band,
        notes="pass3 full vipaka triad; klesha-root weights floored",
    )


def verify(d: Draft) -> tuple[bool, str]:
    ok_pheno = d.phenotype in {"typical_ad", "atypical", "mci_stable", "mixed"}
    ok_years = 0.5 <= d.years_indep <= 12.0
    ok_bhoga = 0.0 <= d.bhoga <= 1.0
    ok_w = d.w_species >= 0.25 and d.w_life >= 0.25 and d.w_bhoga >= 0.25
    ok_comp = d.composite >= 0.45
    ok_band = d.band in {"medium", "high"}
    passed = all([ok_pheno, ok_years, ok_bhoga, ok_w, ok_comp, ok_band])
    reasons = []
    if not ok_pheno:
        reasons.append(f"phenotype={d.phenotype} not in allowed set")
    if not ok_years:
        reasons.append(f"years_indep={d.years_indep} out of [0.5,12]")
    if not ok_bhoga:
        reasons.append(f"bhoga={d.bhoga} out of [0,1]")
    if not ok_w:
        reasons.append(
            f"weights too low ws={d.w_species} wl={d.w_life} wb={d.w_bhoga}"
        )
    if not ok_comp:
        reasons.append(f"composite={d.composite} < 0.45")
    if not ok_band:
        reasons.append(f"band={d.band} not medium/high")
    return passed, "PASS" if passed else "FAIL: " + "; ".join(reasons)


def run(sample: dict[str, Any] | None = None, max_pass: int = 3) -> list[dict[str, Any]]:
    sample = sample or SAMPLE
    log: list[dict[str, Any]] = []
    critique: str | None = None
    for n in range(1, max_pass + 1):
        draft = generate(sample, critique, n)
        passed, reason = verify(draft)
        rec = {"pass": n, "draft": asdict(draft), "passed": passed, "reason": reason}
        log.append(rec)
        critique = reason
        print(f"PASS {n}: {reason}")
        print(json.dumps(asdict(draft), indent=2))
        if passed and n >= 2:
            break
    return log


if __name__ == "__main__":
    out = run()
    print("--- summary ---")
    print(json.dumps([{"pass": r["pass"], "passed": r["passed"], "reason": r["reason"]} for r in out], indent=2))
