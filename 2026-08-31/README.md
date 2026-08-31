# 2026-08-31 — Pause-Aware Speech Risk Flag (GVU)

Self-improving Generator–Verifier–Updater loop that drafts an ADRD speech-biomarker flag, then revises until pause_ratio and speech_rate heuristics are cited and consistent with the risk label.

Paper seed: Li et al., 2025. *Benchmarking Foundation Speech and Language Models for Alzheimer's Disease and Related Dementia Detection from Spontaneous Speech*. arXiv:2506.11119. Pause annotation improved text models; ASR embeddings beat lexical-only.

## Run

```bash
python3 gvu_speech_agent.py
```

No API key. Heuristic GVU so the loop is falsifiable.

## Verifier criterion

- risk ∈ {low, medium, high}
- rationale cites numeric `pause_ratio` and `speech_rate`
- if pause_ratio ≥ 0.18 or speech_rate < 100 → risk must be high
- if pause_ratio < 0.08 and speech_rate ≥ 130 → risk must be low
