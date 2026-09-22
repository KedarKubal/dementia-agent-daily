# 2026-09-23 — Coloring-corrected residual speech flag

Aphorisms II.20–21: the seer is pure intelligence seeing through intellect-coloring; the experienced exists for the seer.

Naive raw pause/fluency scores treat polished intellect as health. GVU subtracts education+lexical coloring and scores the residual.

```
python gvu_coloring_residual.py
```

Smoke: pass1 raw-heavy 0.597 high FAIL → pass3 coloring_w=0.50 residual 0.436 medium PASS.
