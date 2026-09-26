# 2026-09-27 — Ashtanga-gated DTx planner

Prevention / digital-therapeutics slice of II.28–II.29: impurities fall only when limbs are practised *in order*.

```
python3 gvu_ashtanga_dtx.py
```

Verifier (falsifiable):
- 8 limbs in order
- each has minutes > 0, impurity_target, measurable_check
- total 20–40 minutes
- ≥4 limbs map to sleep/gait/speech/attention/memory/social/breath/mood

Smoke: pass1 FAIL (5 disordered limbs, placeholders) → pass2 PASS (8 limbs, 33 min).
