# 2026-09-25 — CharMark residual speech flag (GVU)

Self-improving Generator–Verifier–Updater loop for a character-level Markov speech biomarker.

## Run

```bash
python3 gvu_charmark.py
```

No extra deps (Python 3.11 stdlib only).

## Smoke

Pass 1 (word-length proxy dominates): score 0.429 / medium / FAIL  
Pass 2 (char-Markov weight 0.80): score 0.710 / high / PASS
