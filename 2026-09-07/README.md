# 2026-09-07 — Informativeness-weighted story-recall flag

GVU prototype of the Voiceprints (npj Dementia, 2025) insight: reduced linguistic informativeness, not pause/rate alone, separates EOAD-like impairment from generic MCI/non-AD.

- Generator: dual-channel risk (acoustic + content-units / idea-density / fillers)
- Verifier: linguistic weights ≥ 0.45 AND acoustic ≥ 0.20 AND sparse-recall sample must be `eoad_like`
- Updater: boosts content-unit weight until the criterion holds

Run: `python3 gvu_informativeness.py`
