# 2026-09-03 — Wrist-sensor incident-dementia risk flag

Prototype of Brodie et al. 2025 (Watch Walk–UK Biobank): maximal walking speed, running duration, and bedtime from wrist accelerometry independently predict incident dementia.

## Run

```bash
python3 gvu_wrist_risk.py
```

Smoke sample `smoke-ukb-like-01` (0.98 m/s walk, 2 min running/week, 20:15 bedtime):
- pass 1: walk-heavy mix, band high / 0.68, **fail** verifier (walk-only shortcut)
- pass 2: 0.38/0.31/0.31 mix + step-time CV bump, band high / 0.744, **pass**
