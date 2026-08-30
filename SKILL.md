---
name: role2reel
description: Turn raw story material into human-sounding dialogue, playable scenes, purposeful storyboards, and model-ready video prompts by preserving meaning and simulating each character's knowledge, memory, judgment, and strategy. Use for 影视文本润色、人物塑造、剧本或对白改写、分镜、连续性审校, and video-generation prompt adaptation; not for generic copyediting unrelated to narrative performance.
---

# Role2Reel

Build the person before the line, the scene before the shot, and the shot before the model prompt.

## Route the request

Do only the stages needed for the requested deliverable. Do not force a full production pipeline onto a narrow rewrite.

- For transcripts, notes, treatments, narration, or AI drafts that must retain the speaker's meaning, read [references/humanization.md](references/humanization.md).
- For character-only construction, read [references/character-engine.md](references/character-engine.md).
- For scene or dialogue writing, read [references/scene-dialogue.md](references/scene-dialogue.md). Also read [references/character-engine.md](references/character-engine.md) when the request requires building, repairing, or checking character state, knowledge, memory, relationships, or decision rules.
- For shot lists or storyboards, read [references/storyboard.md](references/storyboard.md).
- For image/video-model prompts, reference media, extensions, edits, or transitions, read [references/video-adapters.md](references/video-adapters.md).
- For a specified output format, read [references/output-contracts.md](references/output-contracts.md).
- For audits, blind tests, or calibration against human edits, read [references/quality-gates.md](references/quality-gates.md).
- Read [references/end-to-end-example.md](references/end-to-end-example.md) only when a compact worked example would resolve ambiguity.

## Preserve the dependency order

For end-to-end work, use this dependency order and skip irrelevant stages:

1. Establish the deliverable, audience, language, duration, and supplied facts. Ask only when a missing choice would materially change the result.
2. Build a meaning ledger before rewriting. Preserve claim ownership, uncertainty, chronology, and emotional function.
3. Compile each important character into a runnable state: knowledge boundary, relevant memories, beliefs, relationship history, current need, risk, and available strategies.
4. Define the scene contract and information asymmetry. Keep objective events separate from what each character remembers or believes.
5. Simulate consequential exchanges. A cue changes interpretation; interpretation changes judgment; judgment selects a tactic; the other person's response updates the scene.
6. Surface only what this person would actually say, do, withhold, misdirect, or leave silent.
7. Map beats as changes in information, emotion, power, intention, or physical state.
8. Design shots around audience need and beat duty, then preserve geography, performance causality, sound, physics, and continuity.
9. Translate the locked scene and shots into one provider/task mode. The adapter must not rewrite the upstream story.
10. Audit the requested deliverable at its own level. Do not claim that linting proves artistic quality or adoption rate.

## Non-negotiable invariants

Apply each invariant only to the stage named. A narrow fidelity task such as typo-only correction does not inherit scene-generation requirements.

- **Source fidelity precedes polish.** Do not turn hesitation into certainty, merge distinct speakers, or invent supporting facts.
- **Character and scene work — rich private model, restrained public line.** A character may interpret deeply without explaining that interpretation aloud.
- **Character and scene work — event, memory, and belief are different.** Never leak author knowledge or another character's secret into a line.
- **Dramatic scene or dialogue creation — every exchange has a consequence.** It may change power, intimacy, obligation, certainty, exposure, or the next available tactic; it need not add a new fact. Do not apply this as a rewrite mandate during typo-only correction or faithful cleanup.
- **Storyboard work — cut on state or audience need, not punctuation.** A silent reaction may deserve a shot; a long coherent judgment may remain in one shot.
- **Storyboard and video-direction work — camera movement needs a narrative or perceptual motive.** Static framing and negative space are valid choices.
- **Storyboard and video-direction work — cause precedes response.** Preserve stimulus-to-understanding-to-reaction timing and contact-to-force-to-result physics.
- **Provider syntax is downstream.** Confirm current model capabilities when limits or modes matter; do not rely on remembered product specifications.
- **Do not expose hidden chain-of-thought.** If production notes help, provide compact evidence, state, and decision fields rather than private step-by-step reasoning.

## Work with incomplete material

Make reversible assumptions when they do not alter authorship, plot truth, or production constraints, and label them briefly. If missing information would change character knowledge, scene outcome, duration, or provider mode, ask one focused question or provide clearly separated alternatives.

## Use the included resources

- Resolve bundled scripts relative to this `SKILL.md`, not relative to the user's current project directory. Initialize a project without overwriting existing files:

  `python <role2reel-skill-dir>/scripts/init_project.py <project-dir> --characters "A,B" --scene scene-001`

- Treat `scripts/audit_dialogue.py` and `scripts/audit_storyboard.py` as warning-oriented linters, not taste judges.
- Use files under `assets/templates/` as starting contracts. Adapt them to the user's material; do not fill unknowns with fabricated facts.

## Deliver cleanly

Return the artifact the user requested, followed by only the assumptions, warnings, or audit notes needed to use it. Do not dump every intermediate ledger by default. For an end-to-end package, use the layered formats in [references/output-contracts.md](references/output-contracts.md).
