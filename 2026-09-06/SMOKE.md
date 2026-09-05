# Smoke test 2026-09-06

Sample: gait_speed=0.72 m/s, step_time_cv=0.11, dual_task_slowing=22%, last fall 12 days ago.

Pass 1 (Generator naive, speed-heavy): score 0.626 medium — FAIL (cv weight 0.10 < 0.20)
Pass 2 (Updater raised cv weight to 0.45): score 0.776 high — PASS

Run: `python3 gvu_fall_risk.py`
