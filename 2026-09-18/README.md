# 2026-09-18 — MCI→AD 6-year pause-aware speech progression flag

Diagnostics angle. Prototypes Amini et al. 2024 (Framingham speech → 6-year MCI-to-AD) plus PREPARE finding that pause annotation lifts text models.

```bash
python gvu_mci_progress.py
```

Smoke: pass1 low 0.388 FAIL (1y, pause_w=0.10) → pass3 medium 0.532 PASS (horizon=6, pause_w=0.304, demo_w=0.222).
