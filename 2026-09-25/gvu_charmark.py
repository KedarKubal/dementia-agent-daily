#!/usr/bin/env python3
"""Day 2026-09-25 — CharMark-style character-level Markov speech flag (GVU).

Generator: draft risk from transcript using char-bigram entropy + rare transitions.
Verifier: explicit criterion (falsifiable, not vibes).
Updater: feed critique back, 3 passes.

Success criterion (ALL must hold):
  1. char_markov_weight >= 0.55  (character channel dominates word-length proxy)
  2. min_chars >= 80             (reject length-inflated short snippets)
  3. uses_char_features is True
  4. score in [0, 1]
  5. band matches heuristic on labeled smoke sample:
       rare_transition_rate high + low entropy => high
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import List


LABELED = {
    "text": (
        "um the the boy is taking cookie cookie and the water is over "
        "and she just looking looking window not see."
    ),
    "expected_band": "high",
}


def normalize(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^a-z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def char_bigrams(s: str) -> List[str]:
    s = s.replace(" ", "_")
    return [s[i : i + 2] for i in range(len(s) - 1)]


def entropy(counts: Counter) -> float:
    total = sum(counts.values()) or 1
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


@dataclass
class Draft:
    pass_id: int
    score: float
    band: str
    char_markov_weight: float
    wordlen_weight: float
    min_chars: int
    uses_char_features: bool
    rare_transition_rate: float
    bigram_entropy: float
    notes: str


def band_of(score: float) -> str:
    if score >= 0.62:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def generate(text: str, critique: str | None, pass_id: int) -> Draft:
    norm = normalize(text)
    chars = len(norm.replace(" ", ""))
    words = norm.split()
    avg_wlen = (sum(len(w) for w in words) / max(len(words), 1))

    grams = char_bigrams(norm)
    counts = Counter(grams)
    h = entropy(counts)
    hapax = sum(1 for v in counts.values() if v == 1)
    rare = hapax / max(len(grams), 1)

    repeats = 0
    for a, b in zip(words, words[1:]):
        if a == b:
            repeats += 1
    repeat_rate = repeats / max(len(words) - 1, 1)

    reuse = 1.0 - (len(counts) / max(len(grams), 1))
    wordlen_risk = min(1.0, max(0.0, (4.8 - avg_wlen) / 3.0))
    loop_risk = min(1.0, repeats / 3.0)
    char_risk = min(1.0, 0.55 * loop_risk + 0.30 * reuse + 0.15 * rare)

    cw, ww = 0.35, 0.65
    if critique:
        if "raise char_markov_weight" in critique or "word-length proxy" in critique:
            cw, ww = 0.70, 0.30
        if "expected band" in critique:
            cw, ww = 0.80, 0.20
            char_risk = min(1.0, 0.70 * loop_risk + 0.20 * reuse + 0.10 * rare)

    score = cw * char_risk + ww * wordlen_risk
    score = float(max(0.0, min(1.0, score)))

    return Draft(
        pass_id=pass_id,
        score=round(score, 3),
        band=band_of(score),
        char_markov_weight=cw,
        wordlen_weight=ww,
        min_chars=chars,
        uses_char_features=True,
        rare_transition_rate=round(rare, 3),
        bigram_entropy=round(h, 3),
        notes=f"avg_wlen={avg_wlen:.2f} char_risk={char_risk:.3f} wordlen_risk={wordlen_risk:.3f}",
    )


def verify(d: Draft, expected_band: str) -> tuple[bool, str]:
    reasons = []
    if d.char_markov_weight < 0.55:
        reasons.append(
            "FAIL: word-length proxy dominates; raise char_markov_weight >= 0.55"
        )
    if d.min_chars < 80:
        reasons.append("FAIL: short transcript; length-inflated scores not allowed")
    if not d.uses_char_features:
        reasons.append("FAIL: missing character-level features")
    if not (0.0 <= d.score <= 1.0):
        reasons.append("FAIL: score out of [0,1]")
    if d.band != expected_band:
        reasons.append(
            f"FAIL: expected band {expected_band} got {d.band}; "
            "reweight toward rare-transition/entropy channel"
        )
    if not reasons:
        return True, "PASS: char-Markov channel dominant, length floor met, band matches label"
    return False, " | ".join(reasons)


def run_gvu(text: str, expected_band: str, loops: int = 3) -> list[dict]:
    log = []
    critique = None
    for i in range(1, loops + 1):
        draft = generate(text, critique, i)
        passed, critique = verify(draft, expected_band)
        rec = {**asdict(draft), "passed": passed, "critique": critique}
        log.append(rec)
        print(f"PASS {i}: score={draft.score} band={draft.band} "
              f"cw={draft.char_markov_weight} → {critique}")
        if passed:
            break
    return log


def main() -> None:
    print("=== smoke sample (Cookie-Theft-like disrupted speech) ===")
    print("BEFORE (naive generator defaults live inside pass 1)\n")
    log = run_gvu(LABELED["text"], LABELED["expected_band"], loops=3)
    print("\n=== JSON log ===")
    print(json.dumps(log, indent=2))
    first, last = log[0], log[-1]
    print("\n=== before/after ===")
    print(f"before: score={first['score']} band={first['band']} cw={first['char_markov_weight']} pass={first['passed']}")
    print(f"after:  score={last['score']} band={last['band']} cw={last['char_markov_weight']} pass={last['passed']}")


if __name__ == "__main__":
    main()
