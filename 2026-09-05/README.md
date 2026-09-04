# 2026-09-05 — Effort-conditioned vocal biomarker flag

GVU loop on rest vs high-mental-effort speech rate + pause duration.

- Pass 1 (rest-only): score 0.08 band=low FAIL
- Pass 2 (delta w=0.80): score 0.54 band=medium FAIL
- Pass 3 (delta w=0.95): score 0.626 band=high PASS

Run: `python3 gvu_effort_speech.py`
