# 2026-09-01 — Noun imageability / concreteness-reversal speech flag

Self-improving GVU prototype of Cao & Bao 2024 (Alzheimer's & Dementia: DADM):
amnestic MCI speakers produce *fewer but more abstract nouns*; verbs spared.

## Run

```bash
python gvu_concreteness.py
```

No API keys. Rule-based Generator / Verifier / Updater, 2–3 loops.

## Verifier criterion (falsifiable)

PASS iff: ≥3 nouns, numeric mean concreteness + abstract ratio, risk in {low,medium,high},
high risk only when abstract_ratio ≥ 0.50 AND noun_density < 12/100w,
low risk only when the opposite pair holds.

## Smoke test

- Abstract-heavy sample: pass1 high (restricted lexicon) → pass2 medium (full harvest).
- Concrete-heavy sample: pass1 FAIL unknown → pass2 low + verified.
