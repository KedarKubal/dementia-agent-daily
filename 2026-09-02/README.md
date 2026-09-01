# 2026-09-02 — Composite Six-Biomarker Speech Risk Flag (GVU)

Diagnostics angle. Prototypes the underexploited insight from conversational
speech-biomarker work + Lima-style risk stratification: a **composite of six
conversational markers** (grammar, pragmatics, anomia, turn-taking, slurred
proxy, prosody proxy) plus an explicit low/medium/high triage band.

```
python3 gvu_composite_speech.py
```

Smoke (sample of fragmented, pronoun-heavy speech):

- pass 1 FAIL — composite from 3/6 markers only, risk hardcoded `medium` (0.73)
- pass 2 PASS — mean-of-six composite `0.63`, risk `high`

Verifier criterion is in `SUCCESS` inside the script (falsifiable thresholds).
