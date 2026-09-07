#!/usr/bin/env python3
"""Day 2026-09-08 — Savitarka channel-disentangle speech flag (GVU).

Insight: papers mix sound (acoustics), meaning (lexicon), and knowledge
(content completeness) into one score. Aphorism I.42 says that mixture
is 'samadhi with question' — useful but coarse. The prototype separates
the three channels and only trusts a HIGH flag when they agree after
reweighting (crystal-like I.41).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Dict, List


# --- sample: impaired-like cookie-theft style speech ---
SAMPLE = {
    "id": "cookie_theft_mci_like",
    # SOUND channel (acoustics)
    "speech_rate_spm": 72.0,  # slower
    "mean_pause_s": 0.95,
    "silence_ratio": 0.42,
    # MEANING channel (lexicon)
    "abstract_noun_ratio": 0.62,
    "type_token_ratio": 0.26,
    "modal_particle_rate": 0.16,
    # KNOWLEDGE channel (content / reaction)
    "content_units_recalled": 4,  # of 12 expected
    "off_topic_ratio": 0.35,
    "pronoun_without_referent": 0.28,
}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def channel_scores(s: Dict, w: Dict[str, float] | None = None) -> Dict[str, float]:
    """Map raw features to 0-1 risk per channel (higher = more dementia-like)."""
    sound = (
        clamp((110 - s["speech_rate_spm"]) / 50)
        * 0.4
        + clamp((s["mean_pause_s"] - 0.4) / 0.6) * 0.3
        + clamp((s["silence_ratio"] - 0.15) / 0.35) * 0.3
    )
    meaning = (
        clamp((s["abstract_noun_ratio"] - 0.25) / 0.45) * 0.4
        + clamp((0.50 - s["type_token_ratio"]) / 0.30) * 0.35
        + clamp(s["modal_particle_rate"] / 0.20) * 0.25
    )
    knowledge = (
        clamp((12 - s["content_units_recalled"]) / 12) * 0.5
        + clamp(s["off_topic_ratio"] / 0.40) * 0.25
        + clamp(s["pronoun_without_referent"] / 0.30) * 0.25
    )
    return {
        "sound": round(sound, 3),
        "meaning": round(meaning, 3),
        "knowledge": round(knowledge, 3),
    }


@dataclass
class Output:
    pass_n: int
    weights: Dict[str, float]
    channels: Dict[str, float]
    risk: float
    band: str
    note: str


def generate(sample: Dict, weights: Dict[str, float], pass_n: int, note: str) -> Output:
    ch = channel_scores(sample)
    z = sum(weights.values()) or 1.0
    w = {k: v / z for k, v in weights.items()}
    risk = w["sound"] * ch["sound"] + w["meaning"] * ch["meaning"] + w["knowledge"] * ch["knowledge"]
    if risk >= 0.70:
        band = "high"
    elif risk >= 0.45:
        band = "medium"
    else:
        band = "low"
    return Output(pass_n, {k: round(v, 3) for k, v in w.items()}, ch, round(risk, 3), band, note)


def verify(out: Output) -> Dict:
    """Success criterion (falsifiable):
    1) Each channel weight >= 0.20 (no collapsed mixture — leave savitarka).
    2) For this impaired-like sample, band must be high AND risk >= 0.70.
    3) Max-min channel score spread after weighting contribution must be <= 0.25
       (crystal-like agreement across receiver/receiving/received).
    """
    reasons = []
    ok = True
    for k, v in out.weights.items():
        if v < 0.20:
            ok = False
            reasons.append(f"weight[{k}]={v} < 0.20 (still savitarka-mixed)")
    if out.band != "high" or out.risk < 0.70:
        ok = False
        reasons.append(f"impaired sample must be high>=0.70, got {out.band}/{out.risk}")
    contrib = {k: out.weights[k] * out.channels[k] for k in out.channels}
    spread = max(contrib.values()) - min(contrib.values())
    if spread > 0.25:
        ok = False
        reasons.append(f"weighted-contrib spread {spread:.3f} > 0.25 (channels disagree)")
    if ok:
        reasons.append("pass: balanced weights, high risk, channels agree")
    return {"pass": ok, "reasons": reasons, "contrib": {k: round(v, 3) for k, v in contrib.items()}}


def update(out: Output, critique: Dict) -> Dict[str, float]:
    w = dict(out.weights)
    text = " ".join(critique["reasons"])
    if "weight[" in text:
        for k in w:
            if f"weight[{k}]" in text:
                w[k] += 0.15
    contrib = critique.get("contrib") or {k: w[k] * out.channels[k] for k in w}
    weakest = min(contrib, key=contrib.get)
    strongest = max(contrib, key=contrib.get)
    w[weakest] += 0.10
    w[strongest] = max(0.15, w[strongest] - 0.05)
    if "high>=0.70" in text:
        peak = max(out.channels, key=out.channels.get)
        w[peak] += 0.08
    return w


def run_gvu(sample: Dict, loops: int = 3) -> List[Dict]:
    weights = {"sound": 0.80, "meaning": 0.15, "knowledge": 0.05}
    log = []
    out = generate(sample, weights, 1, "pass1 mixed-savitarka (sound-heavy)")
    crit = verify(out)
    log.append({"output": asdict(out), "verify": crit})
    for i in range(2, loops + 1):
        weights = update(out, crit)
        out = generate(sample, weights, i, f"pass{i} after verifier critique")
        crit = verify(out)
        log.append({"output": asdict(out), "verify": crit})
        if crit["pass"]:
            break
    return log


def main() -> None:
    log = run_gvu(SAMPLE, loops=3)
    print("=== SAMPLE ===")
    print(json.dumps(SAMPLE, indent=2))
    print("\n=== GVU LOG ===")
    print(json.dumps(log, indent=2))
    first = log[0]["output"]
    last = log[-1]["output"]
    print("\n=== BEFORE / AFTER ===")
    print(f"BEFORE pass1: risk={first['risk']} band={first['band']} w={first['weights']}")
    print(f"AFTER  pass{last['pass_n']}: risk={last['risk']} band={last['band']} w={last['weights']}")
    print(f"final verify: {log[-1]['verify']['pass']} | {log[-1]['verify']['reasons']}")


if __name__ == "__main__":
    main()
