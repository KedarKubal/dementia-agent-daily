# 2026-09-16 — Asmita/Raga seer-vs-instrument speech flag

Diagnostics angle. Naive speech models identify the *person* with fluent speech (asmita) and treat pleasant fluency as health (raga). GVU separates seer (self-rating + caregiver concern) from instrument (WPM/pauses) and refuses fluency-as-protection when semantics are thin.

```
python gvu_asmita_raga.py
```

Smoke: pass1 fused=0.354 FAIL (inst_w=0.85) → pass2 fused=0.592 PASS (inst_w=0.40).
