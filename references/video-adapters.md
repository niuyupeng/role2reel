# Provider-neutral video task adaptation

The adapter converts locked scene, storyboard, continuity, and asset revisions into one generation task. It does not repair weak character logic by adding prompt detail and it does not rewrite upstream meaning.

## Confirm capabilities at execution time

Model names, interfaces, input types, limits, and operation names change. When they matter:

1. identify the exact provider, model version, interface, and verification date;
2. inspect the current interface or authoritative provider documentation;
3. record the evidence under `capability_verification` separately from creative choices;
4. map one provider-neutral mode to a currently supported provider operation;
5. label an unsupported or unverified assumption instead of inventing a capability.

Repository examples are routing contracts, not current product documentation. A provider-specific task cannot pass the structural audit merely by naming a model; the record must show a current capability check.

## Select exactly one primary mode

Use one provider-neutral `primary_mode` and exactly one matching entry under `mode_contracts`:

| Mode | Use when | Required control |
|---|---|---|
| `generation` | create a new clip from text and/or authorized media | conditioning origin, observable ending state |
| `exact` | create a new clip with an exact requested duration | exact duration equal to the output timeline |
| `long` | create a longer result through planned sections or provider-native long generation | section boundaries and continuity handoffs |
| `extension` | generate before or after one supplied clip | direction, source boundary, generated boundary, seam event, preserved properties |
| `edit` | change a bounded part of a supplied clip | source, target, operation, interval, and protected elements |
| `transition` | bridge supplied source A into supplied source B | protected A span, bridge window, protected B span, endpoint states, causal bridge, and separate preserve sets |
| `multi_panel` | animate or assemble a mapped multi-panel plan | stable panel IDs, exact panel-to-shot/time roles, binding/excluded properties, and explicit addition bans |

Do not combine generation, editing, extension, and transition instructions unless the current provider explicitly supports a composed operation. If several operations are required, create several versioned tasks with state handoffs.

Stylized rendering is not automatically a separate mode. With no source clip it is usually a `generation` style constraint; when changing a supplied clip it is usually an `edit` operation. The actual provider operation must still be verified.

## Bind upstream artifacts

A professional `video-task.yaml` binds exact revisions and SHA-256 values for:

- storyboard;
- continuity ledger;
- visual bible;
- reference-asset contract.

When the task also consumes a scene or screenplay directly, add it as another bound source rather than pasting an unversioned passage. If a bound artifact changes, invalidate the dependent task. Provider syntax remains downstream and may be regenerated without changing the locked creative sources.

The executable audit receives all four actual upstream documents, not only their declared hashes. It compares each bound artifact ID, revision, and file SHA-256 to the supplied storyboard, continuity ledger, visual bible, and asset contract. It also opens the supplied continuity ledger and requires its own storyboard and visual-bible bindings to match those same actual files; a continuity ledger from another visual/storyboard revision cannot be mixed in. A declaration with a hash-shaped string is not evidence that the task consumed that file.

When those upstream files or exact revisions were not supplied, do not silently drop the required schema fields and call the remainder executable. Return a clearly labeled planning draft, keep unresolved bindings visible, and list what must be resolved before `scripts/audit_video_task.py` can pass. Concise presentation may hide repetition; it may not invent hashes, provider verification, revisions, or authorization records.

## Deny reference inheritance by default

`asset-contract.yaml` uses `default_borrow_policy: deny`. A reference is usable only through a named authorization and a task-local `reference_uses[]` entry. The authorization declares the maximum permitted scope; the use declares what this exact task consumes:

| Field | Meaning |
|---|---|
| Source | Stable asset ID and revision |
| Borrow | Exact properties allowed to transfer |
| Target | Character, prop, location, shot, layer, or time segment affected |
| Interval | When the authorization applies |
| Preserve | Source or target features that must remain stable |
| Exclude | Features that must not leak from the reference |

Each task-local use has a stable `use_id`, points to the authorization and exact `asset_id`/`revision`, targets `OUTPUT`, and covers the complete output interval consumed by that mode source. Every media reference inside the active mode contract includes that same `use_id`; an asset ID alone is not executable. Its `borrow` list includes the exact literal role required by the mode:

| Mode source | Required role |
|---|---|
| generation/exact conditioning media | `conditioning` |
| extension source | `extension_source` |
| edit source | `edit_source` |
| transition A / B | `transition_source_a` / `transition_source_b` |
| each multi-panel source | `panel_source` |

Identity, wardrobe, setting, performance, camera, timing, voice, music, text, and style remain excluded unless named. “Use video 2 as reference” grants nothing. A motion reference must not silently import the actor, costume, background, voice, or camera grammar.

### Bind the bytes or an immutable provider revision

Every `asset-contract.source_assets[]` entry is executable only with exactly one immutable media binding:

- `local_file` plus its SHA-256, where the file is relative to the asset-contract directory (or the explicit `--asset-media-root`), is a regular non-symlink file below that root, and its bytes match the recorded hash; or
- `provider_asset_id` plus `provider_asset_version`, where the provider version is immutable for the attached source.

`file_or_slot`, attachment position, filename, or an asset ID/revision alone can describe a workflow but cannot bind media. A mode source can consume only a source asset whose immutable binding passed audit; changing a local file after its contract was written or replacing a provider slot without a new immutable version fails the task.

## Lock continuity explicitly

For each of `identity`, `wardrobe`, `space`, and `voice`, declare either:

- `status: locked` with at least one exact lock entry; or
- `status: not_applicable` with a reason.

Do not use an empty list to mean both “unchanged” and “forgotten.” Lock entries point to stable asset revisions and name the property/value held. Other categories may cover prop ownership, light, text, style, camera grammar, and sound environment.

## Build one exact causal timeline

Timeline segments start at zero, do not overlap or leave hidden gaps, and end at `output.duration_s`. Each segment contains an observable event and its `state_in`/`state_out`. A professional task also declares camera, performance, sound, and asset references per segment.

Place dialogue or sound at the point its source can produce it. Allow comprehension, travel, contact, force, and residual time. If the provider accepts only one prompt block, preserve this internal structure when rendering it into prose:

```text
[verified provider operation]
[bound source revisions]
[identity / wardrobe / space / voice locks]
[exact causal timeline]
[authorized reference roles]
[mode-specific seam, edit, bridge, or panel contract]
[targeted exclusions]
[final state or next-task handoff]
```

## Mode-specific invariants

### Generation and exact duration

Declare whether conditioning is text-only, image-conditioned, video-conditioned, or mixed. Every non-text conditioning asset uses `{asset_id, revision, use_id}` and an authorized `conditioning` role covering the generated output span. In `exact`, the requested duration, output duration, and final timeline endpoint must agree; do not solve a mismatch by squeezing physically necessary action without flagging it.

### Long work

Break the result into ordered sections with explicit boundary states. A section boundary is not permission to reset wardrobe, geography, voice, prop ownership, or emotional residue. If the provider requires several calls, materialize each call as a separate task and carry the approved handoff state.

### Extension

Name one source clip revision and `before` or `after`. Its ref includes a valid `use_id` authorized for `extension_source` over the generated output span. Record the relevant source boundary state and the first/last generated boundary state. The seam declares a causal bridge event and properties preserved across it. Do not hide an identity, camera-axis, light, motion, or audio discontinuity with a generic “seamless” adjective.

### Edit

Every edit target names an object/layer/time interval, the exact operation, and what must remain unchanged. The source ref includes a valid `use_id` authorized for `edit_source` over the consumed output span. A global `protected_elements` list is mandatory. An edit request without a bounded target is a new generation request or an unresolved instruction, not an executable edit.

### Transition

Bind distinct source A and source B revisions. Their refs include different `use_id` values authorized respectively for `transition_source_a` and `transition_source_b`, each covering the protected output span it supplies. Declare three output-time spans separately: `source_a_protected_interval`, `bridge_window`, and `source_b_protected_interval`. They must be contiguous, non-overlapping, start at zero, and end at the requested duration. A single endpoint timestamp or still description does not substitute for either protected interval.

Describe A's ending state, B's starting state, and a bridge with observable cause and effect. Preserve sets for A and B remain separate; blending two sources never grants cross-inheritance of identities, wardrobes, settings, voices, or text. If only a source-local trim is known, record it in the bound media record as well, but do not confuse that trim with the output-time protection spans.

### Multi-panel

Give every panel a stable ID, source revision, `use_id` authorized for `panel_source`, order, role, exact target shot and time interval, non-empty `binding_properties`, and non-empty `excluded_properties`. The target shot IDs and intervals must agree with the actual supplied storyboard, and the panels must cover the intended output without hidden gaps or overlap. Layout position alone is not temporal mapping. Do not let the model guess which panel supplies identity, action, composition, or final state.

Set `unrequested_additions.policy: deny`. Its categories must explicitly include `cta`, `logo`, and `decorative_effects`; add input-specific bans such as dialogue, narration, music, extra sound, or camera movement whenever they were not requested. This explicit list is required even though reference borrowing is generally deny-by-default: one controls what may be inherited from sources, while the other controls what the generator may add on its own.

## Diagnose conflicts and repair structure first

Audits return localized conflict codes. Repair the smallest governing record:

- rebind a stale source instead of rewriting the creative content;
- reconcile adjacent state IDs instead of inserting an unplanned event;
- remove an unauthorized borrowed property or add a deliberate authorization;
- correct the active mode contract instead of mixing mode instructions;
- retime segments without changing their causal order;
- fix an extension seam, edit target, transition bridge, or panel mapping without regenerating unaffected sections.

After repair, rerun the audit and then inspect the rendered result. Structural validity cannot prove visual quality, identity fidelity, physical realism, or performance truth.

Use `assets/templates/video-task.yaml`, `asset-contract.yaml`, `visual-bible.yaml`, and `video-prompt.md`. For Seedance, additionally use `references/providers/seedance.md` and verify the current interface before rendering provider syntax.
