# Character judgment engine

A long biography is useful only when it can change what the character notices, recalls, concludes, wants, or risks in the current moment. Compile character material into a scene-usable model.

## Character runtime

For each consequential character, maintain the smallest useful set of fields:

- stable drives, values, contradictions, and shame or pride triggers;
- learned interpretation rules: what they treat as evidence and how they assign cause;
- decision rules: how quickly they conclude, what changes their mind, and when they refuse judgment;
- episodic memories with subjective meaning, not only objective events;
- relationship ledger: trust, debt, resentment, intimacy, leverage, promises, and prohibited topics;
- knowledge boundary: known, inferred, suspected, mistaken, and unknown;
- second-order belief when useful: what A believes B knows, wants, or suspects;
- expression resources: vocabulary, syntax, humor, evasion, status behavior, and register by relationship;
- current body, emotion, need, risk, and public mask.

Do not infer sensitive biography merely to make the profile longer. Unknowns may remain unknown.

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

This separation creates plausible error, surprise, suspicion, and revision without arbitrary inconsistency.

## Retrieve in two stages

First retrieve resources that help the character **understand** the cue: similar experiences, relationship history, domain knowledge, fears, and active misconceptions.

Then retrieve resources that help the character **respond**: past wording, familiar tactics, social register, habitual defenses, and actions available in this setting.

Prefer a small scene-local set that changes the current judgment. A common working range is three to seven memories, but relevance matters more than a fixed count. Rank by situational relevance, unresolved emotional force, relationship relevance, and recency.

## Turn-state contract

Before a consequential response, track compact fields rather than writing a hidden essay:

| Field | Content |
|---|---|
| Cue | What the character actually perceived |
| Literal read | What the words or action directly mean |
| Retrieved factors | Relevant memory, knowledge, or relationship entries |
| Attribution | Why the character thinks the other person did this |
| Judgment | Current conclusion, question, or refusal to conclude |
| Stance | Agree, oppose, doubt, reserve, conceal, or undecided |
| Confidence | Low, medium, or high, with the evidence boundary |
| Social objective | What change they want in the other person this turn |
| Strategy | Ask, test, reassure, accuse, deflect, bargain, joke, lie, act, or remain silent |
| Surface | The selected line, action, or silence |

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

Use `assets/templates/character.yaml`, `cognitive-resources.yaml`, `memories.yaml`, and `relationship-ledger.yaml` when persistent production files are useful.
