---
name: role2reel
description: Turn raw story material into causally grounded character life histories, human-sounding dialogue, playable scenes, purposeful storyboards, and model-ready video prompts while preserving meaning and knowledge boundaries. Use for 人物小传或人生轨迹推演、影视文本润色、人物塑造、剧本或对白改写、分镜、连续性审校, and video-generation prompt adaptation; not for generic copyediting unrelated to narrative performance.
---

# Role2Reel

Build the person before the line, the scene before the shot, and the shot before the model prompt.

## Route the request

Do only the stages needed for the requested deliverable. Do not force a full production pipeline onto a narrow rewrite.

- For transcripts, notes, treatments, narration, or AI drafts that must retain the speaker's meaning, read [references/humanization.md](references/humanization.md).
- For a substantial character biography, pre-story life trajectory, sparse-label character repair, or category-stereotype failure, read [references/life-paths.md](references/life-paths.md), then [references/character-engine.md](references/character-engine.md).
- For character-only construction from already established canon, read [references/character-engine.md](references/character-engine.md).
- For scene or dialogue writing, read [references/scene-dialogue.md](references/scene-dialogue.md). Also read [references/character-engine.md](references/character-engine.md) when the request requires building, repairing, or checking character state, knowledge, memory, relationships, or decision rules.
- For shot lists or storyboards, read [references/storyboard.md](references/storyboard.md).
- For image/video-model prompts, reference media, extensions, edits, or transitions, read [references/video-adapters.md](references/video-adapters.md).
- For a specified output format, read [references/output-contracts.md](references/output-contracts.md).
- For audits, blind tests, or calibration against human edits, read [references/quality-gates.md](references/quality-gates.md).
- Read [references/life-path-staged-example.md](references/life-path-staged-example.md) when a compact example of candidate-to-biography-to-runtime flow would resolve ambiguity. Read [references/end-to-end-example.md](references/end-to-end-example.md) only when a scene-to-shot example is more useful.

## Preserve the dependency order

For end-to-end work, use this dependency order and skip irrelevant stages:

1. Establish the deliverable, audience, language, duration, and supplied facts. Ask only when a missing choice would materially change the result.
2. Build a meaning ledger before rewriting. Preserve claim ownership, uncertainty, chronology, and emotional function.
3. When character history is underdetermined and consequential, establish a stable character ID and character-package context plus a versioned fact boundary; generate at least three causally distinct life-path candidates; let the author select, edit, compose, reject, or regenerate them; and bind the author decision to that character package, exact fact snapshot, candidate hash, branch, and lock revision before expansion. A path lock authorizes expansion only. A `deep` character is not complete until the locked-path biography passes the default 30,000-countable-Chinese-character mechanical contract and the author separately approves its exact character package, path context, revision, and body hash.
4. Compile only the locked candidate and exact author-approved biography into a runnable state: knowledge boundary, relevant memories, shared context, learned expectations, value order, first impulses, relationship history, current need, risk, and available strategies. Bind each compiled file's hash and source closure to the character and package ID, fact snapshot, candidate, path revision, and biography. Invalidate and regenerate downstream artifacts if any bound value changes.
5. Review the outline against the locked life. Surface incompatibilities and offer author-controlled repair options; do not silently rewrite canon or force the person to serve a beat. Then define the scene contract and information asymmetry, keeping objective events separate from what each character remembers or believes.
6. Simulate consequential exchanges. A cue activates locked memory and relationship residue; appraisal selects a first impulse and social tactic; the other person's response updates the scene. Let occupational expertise supply means only after this human appraisal.
7. Surface only what this person would actually say, do, look at, withhold, misdirect, or leave silent.
8. Map beats as changes in information, emotion, power, intention, or physical state.
9. Design shots around audience need and beat duty, then preserve geography, performance causality, sound, physics, and continuity.
10. Translate the locked scene and shots into one provider/task mode. The adapter must not rewrite the upstream story.
11. Audit the requested deliverable at its own level. Do not claim that linting proves artistic quality or adoption rate.

## Non-negotiable invariants

Apply each invariant only to the stage named. A narrow fidelity task such as typo-only correction does not inherit scene-generation requirements.

- **Source fidelity precedes polish.** Do not turn hesitation into certainty, merge distinct speakers, or invent supporting facts.
- **Character construction — an endpoint is not a life path.** Occupation, education, status, awards, and identity categories may constrain access, expertise, resources, or pressure; they do not independently establish personality, morality, speech, or first response.
- **Life-path development — candidates are not canon.** Only an author-locked branch may enter character, memory, relationship, outline, scene, turn-state, or screenplay artifacts. Rejected or merely selected branches must not leak downstream.
- **Life-path development — lock records require an actual author decision.** Do not fill `author_decision`, `tier_author_decision`, or `author_lock` from model preference, scoring, or repeated use. Record the user's or project's explicit decision source and bind it to the exact character ID, stable package context, branch, fact-boundary hash, candidate hash, and lock revision; static validation can check consistency but cannot prove who made the decision.
- **Life-path development — path lock is not biography approval.** Expansion may add concrete facts that were absent from the causal skeleton. Do not compile them until the author approves the exact character/package identity, branch, fact snapshot, candidate hash, path revision, biography revision, and body hash; any bound change invalidates that approval.
- **Life-path development — depth cannot be claimed by length alone.** A consequential character marked `deep` defaults to at least 30,000 countable Han characters in the locked Chinese biography body plus the causal, temporal, relationship, evidence, and present-residue coverage in [references/life-paths.md](references/life-paths.md). Repetition, random trivia, source quotations, and rejected branches do not count.
- **Character and scene work — rich private model, restrained public line.** A character may interpret deeply without explaining that interpretation aloud.
- **Character and scene work — event, memory, and belief are different.** Never leak author knowledge or another character's secret into a line.
- **Scene work — test the body and relationship before dialogue.** Try action, distance, gaze, stopping, expression, pause, silence, and established shared context first. Write only the dialogue the current strategy still requires; do not impose a universal line-length limit.
- **Scene work — shared history is compressed, not recapped.** A nonverbal cue may retrieve only previously established mutual knowledge, and mutually informed characters do not explain it to one another for the audience.
- **Dramatic scene or dialogue creation — every exchange has a consequence.** It may change power, intimacy, obligation, certainty, exposure, or the next available tactic; it need not add a new fact. Do not apply this as a rewrite mandate during typo-only correction or faithful cleanup.
- **Storyboard work — cut on state or audience need, not punctuation.** A silent reaction may deserve a shot; a long coherent judgment may remain in one shot.
- **Storyboard and video-direction work — camera movement needs a narrative or perceptual motive.** Static framing and negative space are valid choices.
- **Storyboard and video-direction work — cause precedes response.** Preserve stimulus-to-understanding-to-reaction timing and contact-to-force-to-result physics.
- **Provider syntax is downstream.** Confirm current model capabilities when limits or modes matter; do not rely on remembered product specifications.
- **Do not expose hidden chain-of-thought.** If production notes help, provide compact evidence, state, and decision fields rather than private step-by-step reasoning.

## Work with incomplete material

Make reversible assumptions when they do not alter authorship, plot truth, or production constraints, and label them briefly. When a sparse endpoint admits several plausible histories, provide clearly separated candidates rather than silently choosing the stereotype. If missing information would change character knowledge, branch selection, scene outcome, duration, or provider mode, ask one focused question or preserve the alternatives.

## Use the included resources

- Resolve bundled scripts relative to this `SKILL.md`, not relative to the user's current project directory. Initialize a project without overwriting existing files:

  `python <role2reel-skill-dir>/scripts/init_project.py <project-dir> --characters "A,B" --scene scene-001`

- Treat `scripts/audit_dialogue.py` and `scripts/audit_storyboard.py` as warning-oriented linters, not taste judges.
- Use `scripts/audit_life_paths.py` to check fact-boundary records and hashes, branch-lock decision bindings, exact duplicate spines, separate biography approval, exact compiled-file hashes and provenance closure, conditional outline review, automatically declared shared-event ledgers, and the deep-biography mechanical contract. It cannot prove author identity, detect unmarked semantic leakage, judge causal density, or establish artistic truth.
- Use `scripts/audit_staged_eval.py` before changing an FT-14 result to `behavior_pass: true`. It re-runs the mechanical life-path audit and checks the exact files, hashes, task separation, variants, traceability, and review record; it cannot prove that the recorded tasks or reviews actually occurred.
- Use files under `assets/templates/` as starting contracts. Adapt them to the user's material; do not fill unknowns with fabricated facts.

## Deliver cleanly

Return the artifact the user requested, followed by only the assumptions, warnings, or audit notes needed to use it. Do not dump every intermediate ledger by default. For an end-to-end package, use the layered formats in [references/output-contracts.md](references/output-contracts.md).
