# 2026-09-13 — Night-time ambient safety flag (GVU)

Routine-aware night-risk score from door + motion + mattress signals.

- Pass 1 (naive, routine_w=0.20): score 0.703 high, alert True — fails verifier (routine ignored)
- Pass 2 (routine_w=0.60): score 0.647 medium, alert True — verified

```
python3 gvu_night_ambient.py
```
