# Purpose-driven storyboard design

Translate a bound scene revision into shots. A shot exists because the audience must perceive, infer, anticipate, or temporarily miss something. Do not let the storyboard quietly repair or reinterpret upstream meaning.

## Pass the upstream binding gate

Before choosing a frame, bind the storyboard to the exact upstream revisions it is translating:

- `meaning`: the meaning ledger, approved screenplay, or other artifact that owns claim and emotional intent;
- `scene`: the scene contract or equivalent dramatic-state source;
- `beats`: the approved beat/state-change map;
- `visual_bible`: the exact visual-asset registry used by the shots.

Each binding carries a stable artifact ID, revision, and SHA-256. If any bound source changes, mark the storyboard stale and review the affected shots. Do not silently copy a changed line, beat, or ending state into an old storyboard. The binding proves document identity, not artistic fidelity; a person still checks that the shots preserve the intended meaning.

For a modern board, pass the actual four files to the audit rather than copying
hash-shaped strings into the storyboard:

`python scripts/audit_storyboard.py <storyboard.yaml> --meaning <meaning-ledger-or-approved-draft> --scene <scene-contract.yaml> --beats <beat-map.yaml> --visual-bible <visual-bible.yaml>`

The meaning ledger uses `ledger_id` plus `revision`; an approved Markdown draft
uses `draft_id` plus `draft_revision`; a scene contract uses `scene.id` plus
`scene.revision`; and a beat map uses `beat_map_id` plus `revision`. The audit opens
each supplied file and compares its actual SHA-256. Legacy v0.1 row boards keep
their structural-only behavior.

Use one of two declared depths:

- `concise` is an author-review shot list: duty, observable event, timing, state in/out, dialogue mode, sound, asset references, and handoff remain explicit, while lens and production detail may be compact.
- `professional` is a production contract: add exact blocking, framing, motivated camera behavior, performance cause, continuity match points, and transition details.

Depth changes detail, not story. A concise board must not invent facts that a professional board would have to retract.

## Start from beat duty

For every proposed shot, write one duty before choosing a lens or movement. Useful duties include:

- establish geography, distance, or screen direction;
- identify who owns information or power;
- reveal or conceal a reaction;
- let a listener complete understanding;
- isolate a decisive object or action;
- redirect attention;
- make a misunderstanding legible;
- preserve contact, force, and physical result;
- establish a sound source or use off-screen sound;
- close on a changed relationship or unresolved image.

Merge or remove a shot whose duty duplicates its neighbors without adding timing, contrast, or continuity value.

Before finalizing, compare every pair of adjacent shots. If one continuous view can show both the first reaction and the held ending state without a new reveal, spatial relation, sound source, or audience task, merge them. Do not add a separate closing hold merely to create a final shot.

For a short scene, also compare shot boundaries with spoken-unit boundaries. If nearly every line starts a new shot, treat the draft as line-count-driven and rebuild it from the fewest continuous views that preserve the real state changes. When the user explicitly asks not to cut by dialogue and does not impose a shot count, default to strictly fewer shots than spoken units. Exceed that diagnostic only for a genuinely non-interchangeable audience task, and make the exception visible in `duty`.

## Choose the cut point

Cut when the audience's perceptual task changes, not automatically at punctuation or speaker changes. Consider:

- new evidence entering the frame;
- a reaction becoming more important than the speaker;
- a power shift requiring a new spatial relation;
- an action needing causal clarity;
- intentional concealment or reveal;
- a sound changing its source or meaning;
- a meaningful temporal compression.

Key dialogue may remain on the listener. A shot may contain no dialogue. A fixed frame may carry several exchanges.

When silence is itself a requested or useful shot duty, keep at least one chosen silent shot wholly free of dialogue. A spoken shot with a quiet tail is a silent beat, not a silent shot. In a minimal exchange, concentrate spoken units into a continuous view and reserve another view only for a genuine silent state change.

## Separate performance from audio

Declare one `dialogue.mode` per shot:

- `spoken`: one or more audible character lines, with speaker ownership;
- `nonverbal`: meaning is carried by gaze, body, action, distance, or shared context and contains no spoken line;
- `silent`: no dialogue; sound may still exist unless the sound field explicitly declares acoustic silence.

Dialogue mode is not a sound mix. Keep ambience, effects, off-screen sources, room tone, music function, and acoustic silence under `sound`. A nonverbal or silent shot may be loud; a spoken shot may have no music.

## Bind visual assets per shot

Build `visual-bible.yaml` before a professional board. Give every recurring character look, wardrobe state, prop, location, voice, and reference source a stable `asset_id` and `revision`. A shot refers to those exact pairs; a name such as “the mother” is not a revision binding.

Each per-shot asset reference names:

- the visual-bible asset ID and revision;
- its role in this shot;
- the properties used by the shot;
- the target subject, layer, or interval.

Changing an asset revision makes only the dependent shots stale. Do not globally regenerate unrelated shots. Borrowing from supplied media is separately authorized in `asset-contract.yaml`; appearing in the visual bible does not grant permission to inherit every property of a source.

## Design state handoffs

Every shot declares `state_in`, `state_out`, and a handoff. Adjacent shots must agree on the handed state even when the cut changes angle, time scale, or point of view. The state can be a stable state ID or a compact mapping, but it must cover what the next shot depends on: position, prop ownership, information exposure, emotional residue, physical result, and active sound when relevant.

For performance:

```text
stimulus -> comprehension beat -> first involuntary response -> chosen mask or tactic -> visible action -> residual state
```

For contact or object motion:

```text
cause -> approach -> contact -> force direction -> body or object response -> result
```

Do not make a character react before receiving the cue or an object move before force is applied.

## Motivate camera and composition

- Use camera movement when following action, revealing information, changing allegiance, or altering felt distance.
- Keep the camera static when observation, tension, geometry, or performance benefits from stability.
- Use negative space, occlusion, or partial framing intentionally; do not fill the frame by default.
- Select shot scale and lens behavior from story distance and spatial truth, not from a checklist of cinematic words.
- Preserve eyeline, screen direction, and action axis unless a break has a legible purpose.

## Time from action

Estimate duration from dialogue breath, movement distance, comprehension, holds, and transitions. There is no universal maximum shot length and no requirement that adjacent shots use different movements. When a fixed total duration is required, reconcile every shot on one continuous timeline and flag compression that makes performance implausible.

For the full timing contract, keep performance, editorial, and provider clocks separate and record the five hard floors (dialogue, action, visual, camera, performance hold) in [dynamic-shot-timing.md](dynamic-shot-timing.md). When the delivery must be pasted into a video model, render each shot through [copy-paste-prompt-contract.md](copy-paste-prompt-contract.md) and audit the text export, not only the workbook formula.

## Use sound narratively

Specify sound when it establishes space, bridges a cut, precedes a reveal, masks information, carries off-screen action, or changes emotional interpretation. Do not add background music or effects merely to populate fields.

## Diagnose conflicts and repair narrowly

Treat the first failed invariant as the repair boundary:

- a source revision/hash mismatch invalidates the translation; rebind or review affected shots, not the source story;
- an unknown asset or revision is repaired in the visual bible or the affected shot reference, not by renaming the character throughout the project;
- a state-handoff mismatch is repaired at the cut or declared state change, not by inventing an unseen action;
- an unauthorized reference property is removed or explicitly authorized, not silently inherited;
- an impossible action or performance timeline is retimed while preserving shot duty and beat order.

After a repair, rerun the structural audit and then review meaning, playability, and cinematic value manually. Linters cannot decide whether the chosen shot is good.

Use `assets/templates/visual-bible.yaml`, `storyboard.yaml`, `storyboard.csv`, and `continuity.yaml` when persistent production artifacts are needed. Treat YAML as the authoritative professional contract; CSV is a flat review/export view and repeats binding fields where needed.
