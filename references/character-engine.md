# Character judgment engine

A long biography is useful only when it can change what the character notices, recalls, concludes, wants, or risks in the current moment. Compile character material into a scene-usable model.

When the past is not already established, do not fill this runtime directly from a current category or plot function. First use [multi-candidate life-path development](life-paths.md) to separate evidence, generate competing histories, obtain an author selection, and lock one revision. This runtime contains the compiled result, not rejected possibilities.

## Character runtime

For each consequential character, maintain the smallest useful set of fields:

- stable drives, values, contradictions, and shame or pride triggers;
- role context separated into demonstrated affordances, pressures, expertise, and what the role does not imply;
- the locked life-path branch and revision from which learned rules were compiled;
- learned interpretation rules: what they treat as evidence and how they assign cause;
- decision rules: how quickly they conclude, what changes their mind, and when they refuse judgment;
- episodic memories with subjective meaning, not only objective events;
- relationship ledger: trust, debt, resentment, intimacy, leverage, promises, and prohibited topics;
- knowledge boundary: known, inferred, suspected, mistaken, and unknown;
- second-order belief when useful: what A believes B knows, wants, or suspects;
- expression resources: vocabulary, syntax, humor, evasion, status behavior, and register by relationship;
- current body, emotion, need, risk, and public mask.

Every compiled expectation, strategy, impulse, relationship rule, or memory should retain a source reference to the locked path revision and relevant causal node. The `source_map` in `character.yaml` exists for this purpose. Without that dependency, node ablation and upstream revision invalidation cannot be tested reliably.

Do not infer sensitive biography merely to make the profile longer. Unknowns may remain unknown.

## Do not substitute a category for a person

Treat occupation, education, class, region, diagnosis, and other labels as possible constraints or access paths. They may explain which tools the character can use, what information they encounter, or which risks the institution creates. They do not by themselves explain what the character notices first, how they assign blame, what dignity they defend, whether they persist, or how they speak.

Run the locked life path and present relationship before professional competence:

```text
locked residue + current cue + relationship + need/risk
-> appraisal -> first impulse -> social strategy
-> feasible means, including occupational expertise
-> observable surface
```

If changing one role label to another plausible role rewrites the whole personality while the lived history remains fixed, the runtime is category-driven and must be rebuilt.

## Keep three realities separate

```text
objective event != remembered event != current belief
```

A useful memory entry therefore contains:

- what happened;
- what the character perceived;
- what they concluded then;
- what they feel or believe about it now;
- which present cues can retrieve it;
- whether the belief is accurate, partial, or false.
- provenance status, source references, and the locked life-path node when the memory came from authored prehistory.

This separation creates plausible error, surprise, suspicion, and revision without arbitrary inconsistency.

## Retrieve in two stages

First retrieve locked resources that help the character **understand** the cue: similar experiences, relationship history, domain knowledge, fears, and active misconceptions. Open, rejected, or selected-but-unlocked life-path branches are not retrievable resources.

Then retrieve resources that help the character **respond**: past wording, familiar tactics, social register, habitual defenses, and actions available in this setting.

Prefer a small scene-local set that changes the current judgment. A common working range is three to seven memories, but relevance matters more than a fixed count. Rank by situational relevance, unresolved emotional force, relationship relevance, and recency.

## Turn-state contract

Before a consequential response, track compact fields rather than writing a hidden essay:

| Field | Content |
|---|---|
| Cue | What the character actually perceived |
| Literal read | What the words or action directly mean |
| Retrieved factors | Relevant locked memory, knowledge, relationship, or `life-path:<branch>/<node>` references |
| Attribution | Why the character thinks the other person did this |
| Judgment | Current conclusion, question, or refusal to conclude |
| First impulse | The first bodily or relational move before suppression or social filtering |
| Modulation | What the character suppresses, redirects, or permits and why |
| Response decision | Whether to answer, act, delay, misdirect, or withhold |
| Stance | Agree, oppose, doubt, reserve, conceal, or undecided |
| Confidence | Low, medium, or high, with the evidence boundary |
| Social objective | What change they want in the other person this turn |
| Strategy | Ask, test, reassure, accuse, deflect, bargain, joke, lie, act, or remain silent |
| Surface | The selected action, spatial relation, gaze, expression, pause, silence, or line |

The surface should usually contain less than the private state.

## Update after every exchange

Update only what changed:

- new fact or new suspicion;
- belief confidence;
- perceived intention of the other person;
- power, trust, debt, exposure, or intimacy;
- available tactics;
- residual emotion entering the next beat.

If nothing changes across several exchanges, the scene is probably circling.

## Differentiate characters by judgment

Do not rely on catchphrases or adjective labels. Two characters may use similar vocabulary yet feel distinct because they:

- notice different evidence;
- retrieve different pasts;
- assign different causes;
- tolerate uncertainty differently;
- protect different forms of dignity;
- use different tactics with the same person;
- change their minds under different conditions.

Also run three counterfactuals from [life-path development](life-paths.md): change occupational context while preserving the path, switch the path while preserving the present and scene, and remove a causal node. The first should preserve core value order and relationship strategy except for genuinely role-dependent means; the latter two should produce an explainable difference. If they do not, the biography is decorative.

Use `assets/templates/life-path-workbench.yaml`, `life-path-biography.md`, `character.yaml`, `cognitive-resources.yaml`, `memories.yaml`, and `relationship-ledger.yaml` when persistent production files are useful.
