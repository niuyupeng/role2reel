# Seedance downstream adapter

Use this reference only after the provider-neutral `video-task.yaml` is structurally complete. It maps a locked task into the user's current Seedance interface; it is not a frozen catalogue of Seedance capabilities or numeric limits.

## Verify the actual interface now

Before emitting provider syntax, record:

- the Seedance product surface or host application being used;
- the exact visible model/version label;
- the verification date and authoritative source or inspected interface;
- which input media and operation controls are currently available;
- the current duration, count, size, aspect-ratio, audio, and extension/edit constraints that affect this task;
- the provider operation selected for the one generic primary mode.

Do not copy remembered limits from a repository example, community post, or earlier session. If the current interface cannot be inspected, keep the task provider-neutral, mark capability verification unresolved, and do not claim that a mode is supported.

## Route one generic mode

The generic modes are stable creative contracts; Seedance labels may change.

| Generic mode | Current-interface question | Invariant to preserve |
|---|---|---|
| `generation` | Which visible action creates a new clip from the supplied conditioning media? | conditioning roles and final state |
| `exact` | Can the current action honor the required exact duration? | requested duration equals the task timeline |
| `long` | Is there a native long operation, or must the work be split into calls? | ordered section handoffs and continuity locks |
| `extension` | Does the interface extend before, after, or both, and what source boundary does it use? | direction, boundary state, seam cause, preserve set |
| `edit` | What regions, intervals, objects, or instructions can the current edit action target? | bounded target, operation, interval, protected elements |
| `transition` | Can the current action consume both supplied clips for one bridge? | protected A span, bridge window, protected B span, endpoint states, causal bridge, separate preserve sets |
| `multi_panel` | How are panels supplied and ordered in this interface? | stable panel-to-shot/time mapping, per-panel binding/exclusion scope, explicit addition bans |

If no current Seedance operation satisfies the chosen contract, stop at the provider-neutral task or split the work into separately auditable tasks. Do not disguise a mode change with prompt prose.

## Bind media tokens explicitly

Translate each authorized asset reference into the exact media token, slot, or attachment name visible in the current interface. For every token, retain:

- stable source asset ID and revision;
- authorization ID;
- task-local `use_id` resolving the active mode source to that authorization;
- borrowed properties;
- target subject/layer/time interval;
- properties preserved;
- properties excluded.

The neutral asset contract must bind the underlying media before a Seedance token is assigned: either a contract-local regular file and matching SHA-256, or a provider-issued immutable asset ID and version. A visible attachment slot or filename is only interface routing metadata; it cannot substitute for that binding.

The use must target `OUTPUT`, cover the exact output span consumed by the source, and carry the provider-neutral literal role (`conditioning`, `extension_source`, `edit_source`, `transition_source_a`, `transition_source_b`, or `panel_source`). Provider token names may change; these role bindings may not be replaced by positional guesses.

Attaching media does not authorize its identity, wardrobe, setting, motion, camera, voice, music, text, or style. The default remains deny. If Seedance implicitly conditions on an attached source more broadly than the contract permits, isolate the reference, mask/crop it when authorized, or choose another workflow; do not call the leakage acceptable by default.

## Render the task without flattening it

Keep this order even if the interface accepts one prose field:

1. selected current Seedance operation and verified constraints;
2. global identity, wardrobe, space, voice, style, and audio locks;
3. exact causal timeline with observable events and state handoffs;
4. media-token role authorizations;
5. the active mode contract;
6. targeted leakage and continuity exclusions;
7. final frame/state and next-task handoff.

Retain cause before response. A performance cue must arrive before comprehension and reaction; contact and force must precede physical result. Do not replace this order with stacks of mood adjectives.

## Apply mode-specific checks

- **Extension:** state `before` or `after`; match the relevant source boundary; name the first or last generated event that makes the seam causal; preserve identity, space, motion, light, and audio only as authorized.
- **Edit:** name the supplied target, operation, and interval; repeat protected elements near the edit command; keep unrelated shots and regions unchanged.
- **Transition:** keep A and B identities separate; carry the neutral task's protected A interval, bridge window, and protected B interval into the current operation; describe the observable bridge from A's end state to B's start state; do not let one source overwrite the other.
- **Multi-panel:** map every panel token to an order, role, shot, or interval; retain each panel's binding and excluded properties plus the task's unrequested-additions deny list; never rely on panel position alone to imply time.
- **Long work:** if several calls are required, create one task per call and carry the exact visual and dramatic handoff forward.

After generation, compare the result against the neutral task, not against whatever the provider happened to produce. Record capability surprises separately so they can change the adapter without rewriting the storyboard or scene.
