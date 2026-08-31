# Purpose-driven storyboard design

Translate the scene's state changes into shots. A shot exists because the audience must perceive, infer, anticipate, or temporarily miss something.

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

For a short scene, also compare shot boundaries with spoken-unit boundaries. If nearly every line starts a new shot, treat the draft as line-count-driven and rebuild it from the fewest continuous views that preserve the real state changes. When the user explicitly asks not to cut by dialogue and does not impose a shot count, default to strictly fewer shots than spoken units: let one shot carry several lines and combine a silent opening or reaction with an adjacent view whenever its duty remains legible. Exceed that diagnostic only for a genuinely non-interchangeable audience task, and make that exception visible in the requested shot-duty field.

When silence is itself a requested or useful shot duty, keep at least one chosen silent shot wholly free of dialogue; a spoken shot with a quiet tail is a silent beat, not a silent shot. In a minimal exchange, concentrate the spoken units into a continuous master and reserve the second view for the silent state change instead of creating one shot per line.

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

## Design the shot

Use only fields that help production, but retain these core decisions:

| Field | Purpose |
|---|---|
| Shot ID and time | Ordering and duration |
| Duty | Why the shot exists |
| Visual event | Observable action, not abstract mood alone |
| Framing and angle | Information, relation, and emphasis |
| Camera behavior | Static or motivated movement with start/end states |
| Blocking | Subject positions, eyelines, entrances, exits, and action paths |
| Performance cause | Cue, understanding, first response, chosen mask, residue |
| Dialogue and sound | Spoken line, off-screen sound, ambience, music function, or silence |
| Continuity | Identity, wardrobe, props, light, screen direction, state, and match points |
| Transition | Cut, hold, dissolve, match, or provider-specific handoff when justified |

## Motivate camera and composition

- Use camera movement when following action, revealing information, changing allegiance, or altering felt distance.
- Keep the camera static when observation, tension, geometry, or performance benefits from stability.
- Use negative space, occlusion, or partial framing intentionally; do not fill the frame by default.
- Select shot scale and lens behavior from story distance and spatial truth, not from a checklist of cinematic words.
- Preserve eyeline, screen direction, and action axis unless a break has a legible purpose.

## Preserve performance and physical causality

For performance:

```text
stimulus -> comprehension beat -> first involuntary response -> chosen mask or tactic -> visible action -> residual state
```

For contact or object motion:

```text
cause -> approach -> contact -> force direction -> body or object response -> result
```

Do not make a character react before receiving the cue or an object move before force is applied.

## Time from action

Estimate duration from dialogue breath, movement distance, comprehension, holds, and transitions. There is no universal maximum shot length and no requirement that adjacent shots use different movements. When a fixed total duration is required, reconcile every shot on one continuous timeline and flag compression that makes performance implausible.

## Use sound narratively

Specify sound when it establishes space, bridges a cut, precedes a reveal, masks information, carries off-screen action, or changes emotional interpretation. Do not add background music or effects merely to populate fields.

Use `assets/templates/storyboard.yaml`, `storyboard.csv`, and `continuity.yaml` when a persistent production artifact is needed.
