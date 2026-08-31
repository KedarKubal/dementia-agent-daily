#!/usr/bin/env python3
"""Day 2026-09-01 — Noun-imageability / concreteness-reversal GVU agent.

Generator drafts a speech-biomarker flag from noun concreteness.
Verifier checks an explicit, falsifiable criterion.
Updater feeds critique back for 3 passes.

Insight prototyped: Cao & Bao 2024 — amnestic MCI speakers produce fewer
but more abstract nouns; verbs are spared. Distinct from pause-ratio work.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import date
from typing import Any

CONCRETENESS: dict[str, float] = {
    "table": 4.8, "chair": 4.9, "cup": 4.9, "water": 4.7, "house": 4.8,
    "dog": 4.9, "cat": 4.9, "bread": 4.8, "phone": 4.7, "car": 4.8,
    "garden": 4.6, "kitchen": 4.7, "window": 4.7, "door": 4.8, "shoe": 4.8,
    "tea": 4.6, "rice": 4.7, "market": 4.3, "bus": 4.7, "park": 4.5,
    "memory": 2.1, "thing": 2.0, "stuff": 2.2, "idea": 1.8, "feeling": 2.0,
    "time": 2.3, "life": 2.2, "problem": 2.1, "situation": 1.9, "matter": 2.0,
    "way": 2.2, "part": 2.4, "kind": 2.0, "sense": 2.1, "mind": 2.2,
    "thought": 1.9, "nature": 2.5, "world": 2.6, "system": 2.0, "process": 1.8,
    "change": 2.3, "reason": 1.9, "truth": 1.7, "freedom": 1.8, "love": 2.1,
    "peace": 2.0, "hope": 1.9, "fear": 2.2, "energy": 2.4, "spirit": 1.8,
    "quality": 1.9, "aspect": 1.6, "concept": 1.5, "issue": 2.0, "case": 2.3,
    "point": 2.4, "fact": 2.1, "experience": 2.2, "knowledge": 2.0,
    "information": 2.3, "relationship": 2.4, "community": 3.0, "family": 3.8,
    "mother": 4.4, "father": 4.4, "daughter": 4.5, "son": 4.5, "friend": 3.9,
    "doctor": 4.3, "hospital": 4.6, "medicine": 4.2, "breakfast": 4.5,
    "walk": 3.8, "sleep": 3.7, "work": 3.2, "home": 4.2, "food": 4.4,
}

STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "for",
    "with", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been",
    "being", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his",
    "her", "our", "their", "this", "that", "these", "those", "there", "here",
    "not", "no", "yes", "so", "then", "than", "too", "very", "just", "about",
    "into", "over", "after", "before", "because", "when", "while", "who",
    "what", "which", "how", "do", "does", "did", "have", "has", "had", "will",
    "would", "can", "could", "should", "may", "might", "must", "me", "him",
    "us", "them", "am",
}

ABSTRACT_CUTOFF = 2.6
MIN_NOUNS = 3
HIGH_ABSTRACT_RATIO = 0.50
LOW_NOUN_DENSITY = 12.0


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def extract_nouns(tokens: list[str], extra_hints: set[str] | None = None) -> list[str]:
    hints = extra_hints or set()
    nouns: list[str] = []
    for t in tokens:
        if t in STOP or len(t) < 3:
            continue
        stem = t[:-1] if t.endswith("s") and t[:-1] in CONCRETENESS else t
        if stem in CONCRETENESS or stem in hints or t in CONCRETENESS:
            nouns.append(stem if stem in CONCRETENESS else t)
    return nouns


@dataclass
class Draft:
    pass_id: int
    word_count: int
    nouns: list[str]
    noun_density_per_100: float
    mean_concreteness: float | None
    abstract_ratio: float | None
    risk: str
    rationale: str
    notes: str = ""


def generate(transcript: str, critique: str | None, pass_id: int) -> Draft:
    tokens = tokenize(transcript)
    extra: set[str] = set()
    restricted = {"thing", "stuff", "idea", "time", "life", "way"}
    if critique:
        extra = {w for w in tokenize(critique) if w not in STOP and len(w) > 3}
        extra |= set(CONCRETENESS)
        notes = f"revised after critique: full lexicon + hints={sorted(extra)[:8]}"
        nouns = extract_nouns(tokens, extra)
    else:
        nouns = [t for t in tokens if t in restricted]
        notes = "restricted first-pass lexicon (self-improvement target)"
    wc = max(len(tokens), 1)
    density = 100.0 * len(nouns) / wc
    scores = [CONCRETENESS[n] for n in nouns if n in CONCRETENESS]
    mean_c = sum(scores) / len(scores) if scores else None
    abstract_n = sum(1 for n in nouns if CONCRETENESS.get(n, 3.0) <= ABSTRACT_CUTOFF)
    abs_ratio = abstract_n / len(nouns) if nouns else None
    if abs_ratio is None or mean_c is None:
        risk = "unknown"
        rationale = "Insufficient scored nouns to estimate concreteness reversal."
    elif abs_ratio >= HIGH_ABSTRACT_RATIO and density < LOW_NOUN_DENSITY:
        risk = "high"
        rationale = (
            f"Reversal pattern: abstract_ratio={abs_ratio:.2f} "
            f"(>={HIGH_ABSTRACT_RATIO}) and noun_density={density:.1f}/100w "
            f"(<{LOW_NOUN_DENSITY}). Matches Cao & Bao 2024 aMCI signature."
        )
    elif abs_ratio >= HIGH_ABSTRACT_RATIO or density < LOW_NOUN_DENSITY:
        risk = "medium"
        rationale = (
            f"Partial signature: abstract_ratio={abs_ratio:.2f}, "
            f"noun_density={density:.1f}/100w."
        )
    else:
        risk = "low"
        rationale = (
            f"Concrete-leaning nouns (ratio={abs_ratio:.2f}, "
            f"density={density:.1f}/100w)."
        )
    return Draft(
        pass_id=pass_id,
        word_count=wc,
        nouns=nouns,
        noun_density_per_100=round(density, 2),
        mean_concreteness=round(mean_c, 3) if mean_c is not None else None,
        abstract_ratio=round(abs_ratio, 3) if abs_ratio is not None else None,
        risk=risk,
        rationale=rationale,
        notes=notes,
    )


def verify(draft: Draft) -> dict[str, Any]:
    reasons: list[str] = []
    ok = True
    if len(draft.nouns) < MIN_NOUNS:
        ok = False
        reasons.append(f"need >={MIN_NOUNS} nouns, got {len(draft.nouns)}")
    if draft.mean_concreteness is None or draft.abstract_ratio is None:
        ok = False
        reasons.append("missing numeric concreteness / abstract_ratio")
    if draft.risk not in {"low", "medium", "high"}:
        ok = False
        reasons.append(f"risk '{draft.risk}' not in low|medium|high")
    if draft.risk == "high":
        if draft.abstract_ratio is None or draft.abstract_ratio < HIGH_ABSTRACT_RATIO:
            ok = False
            reasons.append("high risk requires abstract_ratio >= 0.50")
        if draft.noun_density_per_100 >= LOW_NOUN_DENSITY:
            ok = False
            reasons.append("high risk requires noun_density < 12 /100w")
    if draft.risk == "low":
        if draft.abstract_ratio is None or draft.abstract_ratio >= HIGH_ABSTRACT_RATIO:
            ok = False
            reasons.append("low risk cannot have abstract_ratio >= 0.50")
        if draft.noun_density_per_100 < LOW_NOUN_DENSITY:
            ok = False
            reasons.append("low risk cannot have sparse nouns")
    if ok:
        reasons.append("all five verifier rules satisfied")
    return {"pass": ok, "reasons": reasons}


def run_gvu(transcript: str, loops: int = 3) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    critique: str | None = None
    for i in range(1, loops + 1):
        draft = generate(transcript, critique, i)
        verdict = verify(draft)
        log.append({"draft": asdict(draft), "verifier": verdict})
        if verdict["pass"]:
            critique = (
                "PASS but harvest any remaining concrete household nouns "
                "missed in first pass: table chair cup water house dog bread phone"
            )
        else:
            critique = (
                "FAIL: " + "; ".join(verdict["reasons"]) +
                ". Re-scan content words; treat thing/stuff/idea/situation/problem as nouns."
            )
    return log


SAMPLE_ABSTRACT = (
    "Well I don't know, the thing is the situation has a kind of quality, "
    "a sense of the process of life and time, some idea about the nature of "
    "the problem, the way the mind holds a thought or a concept, the aspect "
    "of freedom and truth, that sort of stuff, a matter of experience and "
    "knowledge more than anything I can point to."
)

SAMPLE_CONCRETE = (
    "This morning I sat at the table with a cup of tea and bread. "
    "The dog waited by the door. I put on my shoe, locked the house, "
    "took the bus to the market, bought rice, walked in the park, "
    "called my daughter on the phone, and came home to the kitchen window."
)


def main() -> None:
    print("=== SAMPLE A (abstract-heavy) ===")
    log_a = run_gvu(SAMPLE_ABSTRACT, loops=3)
    for rec in log_a:
        d, v = rec["draft"], rec["verifier"]
        print(f"pass {d['pass_id']}: risk={d['risk']} nouns={d['nouns']} density={d['noun_density_per_100']} abs={d['abstract_ratio']} verify={v['pass']} :: {v['reasons']}")
    print("\n=== SAMPLE B (concrete-heavy) ===")
    log_b = run_gvu(SAMPLE_CONCRETE, loops=2)
    for rec in log_b:
        d, v = rec["draft"], rec["verifier"]
        print(f"pass {d['pass_id']}: risk={d['risk']} nouns={d['nouns']} density={d['noun_density_per_100']} abs={d['abstract_ratio']} verify={v['pass']} :: {v['reasons']}")
    out = {"date": str(date(2026, 9, 1)), "opportunity": "Noun imageability / concreteness-reversal speech flag", "sample_abstract": log_a, "sample_concrete": log_b}
    path = "run.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
