# Video-model adaptation

The adapter converts a locked dramatic and visual plan into the syntax and constraints of one generation task. It does not repair weak character logic by adding prompt detail.

## Confirm capabilities at execution time

Model names, input limits, duration limits, and modes change. When they matter:

1. identify the exact provider, model version, interface, and date;
2. inspect the current tool or authoritative provider documentation;
3. record verified constraints separately from creative choices;
4. label unsupported assumptions instead of inventing a capability.

Repository examples may illustrate a mode but are not current product documentation.

## Select one primary task mode

Choose one main operation, such as:

- text/image/video-conditioned generation;
- exact-duration generation;
- long-form generation;
- extend before or after a source clip;
- edit a supplied clip;
- transform layout or render style;
- transition between two clips;
- animate a multi-panel storyboard.

Do not mix generation, editing, extension, and transition commands unless the actual interface explicitly composes them.

## Bind every reference asset

For each image, video, audio, or storyboard source, specify:

| Field | Meaning |
|---|---|
| Source | Stable identifier for the supplied asset |
| Borrow | Identity, wardrobe, motion, composition, timing, texture, voice, sound, or another exact role |
| Target | Character, prop, location, shot, layer, or time segment affected |
| Interval | When the binding applies |
| Preserve | Features that must remain stable |
| Exclude | Features that must not leak from the reference |

“Use video 2 as reference” is insufficient. A motion reference should not silently import the actor, wardrobe, or background.

## Lock continuity globally

State global locks once, then write temporal changes:

- identity and count of characters;
- wardrobe and prop ownership;
- location geometry and time of day;
- screen direction and starting positions;
- visual medium, aspect ratio, and camera grammar;
- voice ownership and sound environment;
- states that may change and the event that changes them.

Negative constraints should prevent likely leakage or discontinuity, not become a generic list of every possible defect.

## Build a causal timeline

Use non-overlapping segments that cover the required duration. Each segment should contain observable action and its result. Place dialogue or sound at the point its source can produce it. Allow comprehension and physical travel time.

Example structure:

```text
[task mode and verified constraints]
[global identity, space, style, and audio locks]
00.0-03.5  observable action + camera + sound
03.5-07.0  cue -> comprehension -> response
07.0-10.0  action consequence + ending state
[asset role contracts]
[targeted exclusions]
```

## Seedance-family projects

Some community adapters distinguish multimodal generation, exact-duration or long-video work, extension, editing, stylized rendering, two-video transitions, and multi-panel storyboard animation. Treat those as routing concepts only. Confirm which modes and limits exist in the user's current Seedance interface before emitting model-specific syntax.

Use `assets/templates/asset-contract.yaml` and `video-prompt.md` for persistent work.
