#!/usr/bin/env python3
"""
Day 2026-09-02 — Composite speech-biomarker risk flag (GVU).

Opportunity: risk-stratified composite of six conversational speech
biomarkers (Altered Grammar, Pragmatic Impairments, Anomia, Disrupted
Turn-Taking, Slurred Pronunciation proxy, Prosody Changes proxy),
inspired by conversational-robot speech systems + Lima et al. risk triage.

Generator: draft a per-biomarker score + composite + risk band.
Verifier: explicit, falsifiable criterion (see SUCCESS).
Updater: feed critique back; 3 passes max.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

SUCCESS = {
    "composite_rounding": 2,
    "low_max": 0.35,
    "high_min": 0.60,
    "anomia_pronoun_denom": 1.5,
    "turn_taking_tol": 0.08,
}

PRONOUNS = {
    "i", "me", "my", "mine", "we", "us", "our", "you", "your",
    "he", "him", "his", "she", "her", "hers", "they", "them", "their",
    "it", "its", "this", "that", "these", "those",
}
FILLERS = {"um", "uh", "er", "ah", "like", "youknow", "anyway"}
NOUN_HINTS = {
    "wife", "husband", "daughter", "son", "house", "kitchen", "car", "dog",
    "cat", "park", "store", "doctor", "hospital", "breakfast", "dinner",
    "coffee", "table", "window", "garden", "friend", "memory", "name",
    "picture", "book", "walk", "street", "phone", "keys", "bag", "water",
}


@dataclass
class BiomarkerDraft:
    altered_grammar: float
    pragmatic: float
    anomia: float
    turn_taking: float
    slurred_proxy: float
    prosody_proxy: float
    composite: float
    risk: str
    notes: str = ""
    pass_id: int = 0


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def sentences(text: str) -> List[str]:
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


def heuristic_features(transcript: str) -> Dict[str, float]:
    toks = tokenize(transcript)
    sents = sentences(transcript)
    n = max(len(toks), 1)
    pronouns = sum(1 for t in toks if t in PRONOUNS)
    nouns = sum(1 for t in toks if t in NOUN_HINTS)
    fillers = sum(1 for t in toks if t.replace("'", "") in FILLERS or t in FILLERS)
    short_sents = sum(1 for s in sents if len(tokenize(s)) <= 4)
    avg_len = (sum(len(tokenize(s)) for s in sents) / max(len(sents), 1))
    grammar = min(1.0, short_sents / max(len(sents), 1) * 0.7 + (0.3 if avg_len < 6 else 0.0))
    prag_cues = sum(1 for t in toks if t in {"anyway", "whatever", "thing", "stuff"})
    pragmatic = min(1.0, prag_cues / max(n / 12.0, 1.0))
    anomia_ratio = pronouns / max(nouns, 1)
    anomia = min(anomia_ratio / SUCCESS["anomia_pronoun_denom"], 1.0)
    turn = min(1.0, (fillers / max(n / 8.0, 1.0)) * 0.6 + (short_sents / max(len(sents), 1)) * 0.4)
    slur = min(1.0, sum(1 for t in toks if re.search(r"(.)\1\1", t) or t.endswith("'")) / max(n / 10.0, 1.0))
    punct = len(re.findall(r"[,;:—-]", transcript))
    prosody = min(1.0, 0.5 * (1.0 - min(punct / max(len(sents), 1) / 2.0, 1.0)) + 0.5 * (1.0 if avg_len < 5 else 0.2))
    return {
        "altered_grammar": round(grammar, 4),
        "pragmatic": round(pragmatic, 4),
        "anomia": round(anomia, 4),
        "turn_taking": round(turn, 4),
        "slurred_proxy": round(slur, 4),
        "prosody_proxy": round(prosody, 4),
        "pronouns": pronouns,
        "nouns": nouns,
        "fillers": fillers,
        "n_tokens": n,
        "n_sents": len(sents),
    }


def band(composite: float) -> str:
    if composite < SUCCESS["low_max"]:
        return "low"
    if composite < SUCCESS["high_min"]:
        return "medium"
    return "high"


def mean6(d: Dict[str, float]) -> float:
    keys = [
        "altered_grammar",
        "pragmatic",
        "anomia",
        "turn_taking",
        "slurred_proxy",
        "prosody_proxy",
    ]
    return round(sum(d[k] for k in keys) / 6.0, SUCCESS["composite_rounding"])


def generate(transcript: str, critique: str | None, prev: BiomarkerDraft | None) -> BiomarkerDraft:
    feat = heuristic_features(transcript)
    raw = {k: feat[k] for k in [
        "altered_grammar", "pragmatic", "anomia",
        "turn_taking", "slurred_proxy", "prosody_proxy",
    ]}
    if prev is None:
        sloppy_comp = round((raw["altered_grammar"] + raw["anomia"] + raw["turn_taking"]) / 3.0, 2)
        return BiomarkerDraft(
            altered_grammar=raw["altered_grammar"],
            pragmatic=raw["pragmatic"],
            anomia=raw["anomia"],
            turn_taking=raw["turn_taking"],
            slurred_proxy=raw["slurred_proxy"],
            prosody_proxy=raw["prosody_proxy"],
            composite=sloppy_comp,
            risk="medium",
            notes="pass1: composite from 3/6 markers only; risk hardcoded medium",
            pass_id=1,
        )
    comp = mean6(raw)
    return BiomarkerDraft(
        altered_grammar=raw["altered_grammar"],
        pragmatic=raw["pragmatic"],
        anomia=raw["anomia"],
        turn_taking=raw["turn_taking"],
        slurred_proxy=raw["slurred_proxy"],
        prosody_proxy=raw["prosody_proxy"],
        composite=comp,
        risk=band(comp),
        notes=f"revised after critique: {critique[:120] if critique else ''}",
        pass_id=prev.pass_id + 1,
    )


def verify(draft: BiomarkerDraft, transcript: str) -> Tuple[bool, List[str]]:
    feat = heuristic_features(transcript)
    reasons: List[str] = []
    raw = {
        "altered_grammar": draft.altered_grammar,
        "pragmatic": draft.pragmatic,
        "anomia": draft.anomia,
        "turn_taking": draft.turn_taking,
        "slurred_proxy": draft.slurred_proxy,
        "prosody_proxy": draft.prosody_proxy,
    }
    for k, v in raw.items():
        if not (0.0 <= v <= 1.0):
            reasons.append(f"{k}={v} outside [0,1]")
    expected_comp = mean6(raw)
    if draft.composite != expected_comp:
        reasons.append(f"composite {draft.composite} != mean-of-six {expected_comp}")
    if draft.risk != band(expected_comp):
        reasons.append(
            f"risk '{draft.risk}' inconsistent with true composite {expected_comp} (want {band(expected_comp)})"
        )
    if abs(draft.anomia - feat["anomia"]) > 1e-3:
        reasons.append(f"anomia {draft.anomia} != pronoun/noun heuristic {feat['anomia']}")
    if abs(draft.turn_taking - feat["turn_taking"]) > SUCCESS["turn_taking_tol"]:
        reasons.append(
            f"turn_taking {draft.turn_taking} off expected {feat['turn_taking']} by >{SUCCESS['turn_taking_tol']}"
        )
    return len(reasons) == 0, reasons


def run_gvu(transcript: str, max_passes: int = 3) -> Dict:
    log = []
    draft = None
    critique = None
    passed = False
    for _ in range(max_passes):
        draft = generate(transcript, critique, draft)
        ok, reasons = verify(draft, transcript)
        log.append({
            "pass": draft.pass_id,
            "output": asdict(draft),
            "pass_fail": "PASS" if ok else "FAIL",
            "reasons": reasons,
        })
        if ok:
            passed = True
            break
        critique = (
            "Fix: " + "; ".join(reasons)
            + ". Recompute composite as mean of all six; set risk from thresholds; "
            "use pronoun/noun anomia and filler/short-utterance turn-taking."
        )
    return {
        "transcript": transcript,
        "success_criterion": SUCCESS,
        "passed": passed,
        "passes": log,
    }


SAMPLE = (
    "Um I went to the uh thing with her. And then we. Anyway it was "
    "the place. I told her about the stuff. Uh you know we did that."
)


def main() -> None:
    result = run_gvu(SAMPLE, max_passes=3)
    print(json.dumps(result, indent=2))
    first = result["passes"][0]["output"]
    last = result["passes"][-1]["output"]
    print("\n--- smoke ---")
    print(f"BEFORE pass1  composite={first['composite']} risk={first['risk']} notes={first['notes']}")
    print(
        f"AFTER  pass{last['pass_id']} composite={last['composite']} "
        f"risk={last['risk']} {result['passes'][-1]['pass_fail']}"
    )
    print(f"loop passed={result['passed']} n_passes={len(result['passes'])}")


if __name__ == "__main__":
    main()
