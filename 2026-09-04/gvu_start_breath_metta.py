#!/usr/bin/env python3
"""
Day 2026-09-04 — START-length metta+breath cognitive micro-protocol
Generator–Verifier–Updater (GVU) loop.

Insight prototyped (Corbett et al., JAMDA 2024 START RCT):
a 3-minute computerized cognitive task can improve executive function
even in ApoE4 carriers. Combined with YS I.33 (maitri/karuna affect)
and I.34 (pranayama), the product seed is a *timed, affect-tagged,
breath-paced* micro-protocol — not another unbounded brain-game.

Rule-based slice only. No PHI, no model weights.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List


MIN_SEC = 150
MAX_SEC = 210
TARGET_SEC = 180


@dataclass
class PersonContext:
    person_id: str
    stage: str  # "at_risk" | "mci" | "early"
    fatigue: float  # 0-1
    caregiver_present: bool
    preferred_channel: str  # "voice" | "tablet"


@dataclass
class ProtocolDraft:
    person_id: str
    cognitive_task: str
    metta_phrase: str
    breath_pattern: str
    inhale: int
    hold: int
    exhale: int
    cycles: int
    duration_sec: int
    dual_tasks: int
    affect: str
    pass_n: int
    rationale: str


COG_BANK = {
    "at_risk": "Trail-switch: say the next letter then the next odd number (A-1, B-3…)",
    "mci": "Category fluency: name kitchen objects, one per exhale",
    "early": "Picture naming: name one familiar household object shown on tablet",
}

METTA_SELF = "May I be safe. May I be at ease."
METTA_OTHER = "May you be safe. May you be at ease."
METTA_PUNITIVE = "Stop failing. Try harder."


def generate(ctx: PersonContext, critique: str = "", pass_n: int = 1) -> ProtocolDraft:
    cog = COG_BANK[ctx.stage]
    metta = METTA_SELF
    affect = "friendly"
    inhale, hold, exhale, cycles = 4, 0, 4, 8
    dual = 0

    if pass_n == 1 and not critique:
        metta = METTA_PUNITIVE
        affect = "punitive"
        inhale, hold, exhale, cycles = 6, 7, 8, 12
        dual = 2
        cog = cog + " WHILE walking in place AND tracking a second list"
        duration = 260
        rationale = "Pass1 over-long stacked drill (punitive cue, dual-task, 4-7-8 x12)."
    else:
        if ctx.caregiver_present:
            metta = METTA_OTHER
        if ctx.fatigue > 0.6 or ctx.stage == "early":
            inhale, hold, exhale, cycles = 3, 0, 3, 12
            cog = COG_BANK["early"] if ctx.stage == "early" else COG_BANK["mci"]
        else:
            inhale, hold, exhale, cycles = 4, 0, 4, 12
        breath_sec = cycles * (inhale + hold + exhale)
        duration = 20 + breath_sec + 20
        if duration < MIN_SEC:
            duration = TARGET_SEC
        if duration > MAX_SEC:
            duration = TARGET_SEC
        dual = 1 if "per exhale" in cog else 0
        affect = "friendly"
        rationale = (
            f"Revised to START window after critique. "
            f"stage={ctx.stage} fatigue={ctx.fatigue:.2f} "
            f"critique={critique[:160]}"
        )

    breath = f"{inhale}-{hold}-{exhale} x{cycles}"
    return ProtocolDraft(
        person_id=ctx.person_id,
        cognitive_task=cog,
        metta_phrase=metta,
        breath_pattern=breath,
        inhale=inhale,
        hold=hold,
        exhale=exhale,
        cycles=cycles,
        duration_sec=duration,
        dual_tasks=dual,
        affect=affect,
        pass_n=pass_n,
        rationale=rationale,
    )


def verify(draft: ProtocolDraft, ctx: PersonContext) -> dict:
    reasons: List[str] = []
    ok = True

    if not (MIN_SEC <= draft.duration_sec <= MAX_SEC):
        ok = False
        reasons.append(
            f"duration {draft.duration_sec}s outside START window {MIN_SEC}-{MAX_SEC}s"
        )

    parts = [draft.cognitive_task, draft.metta_phrase, draft.breath_pattern]
    if any(not p.strip() for p in parts):
        ok = False
        reasons.append("missing cognitive, metta, or breath component")

    if draft.dual_tasks > 1:
        ok = False
        reasons.append(f"dual_tasks={draft.dual_tasks} > 1; MCI-safe max is 1")

    if ctx.stage == "early" and draft.dual_tasks > 0:
        ok = False
        reasons.append("early-stage protocol must be single-task")

    punitive_tokens = ("fail", "harder", "stupid", "wrong")
    if draft.affect != "friendly" or any(t in draft.metta_phrase.lower() for t in punitive_tokens):
        ok = False
        reasons.append("I.33 requires friendliness/mercy; punitive affect rejected")

    if draft.inhale < 1 or draft.exhale < 1 or draft.cycles < 4:
        ok = False
        reasons.append("I.34 requires explicit inhale/exhale counts and ≥4 cycles")

    if draft.hold > 4 and ctx.fatigue > 0.5:
        ok = False
        reasons.append("held breath too long for fatigued user")

    if ok and not reasons:
        reasons.append("all explicit criteria passed")

    return {
        "pass": ok,
        "reasons": reasons,
        "duration_sec": draft.duration_sec,
        "dual_tasks": draft.dual_tasks,
        "affect": draft.affect,
    }


def updater(ctx: PersonContext, max_passes: int = 3) -> List[dict]:
    log: List[dict] = []
    critique = ""
    for n in range(1, max_passes + 1):
        draft = generate(ctx, critique=critique, pass_n=n)
        verdict = verify(draft, ctx)
        log.append({"pass": n, "draft": asdict(draft), "verify": verdict})
        if verdict["pass"]:
            break
        critique = "; ".join(verdict["reasons"])
    return log


def main() -> None:
    sample = PersonContext(
        person_id="smoke-start-01",
        stage="mci",
        fatigue=0.4,
        caregiver_present=True,
        preferred_channel="voice",
    )
    log = updater(sample, max_passes=3)
    print(json.dumps({"sample": asdict(sample), "loop": log}, indent=2))
    final = log[-1]
    print(
        "\nSMOKE:",
        f"passes={len(log)}",
        f"first_dur={log[0]['draft']['duration_sec']} affect={log[0]['draft']['affect']}",
        f"final_dur={final['draft']['duration_sec']} affect={final['draft']['affect']}",
        f"final_verify={final['verify']['pass']}",
    )


if __name__ == "__main__":
    main()
