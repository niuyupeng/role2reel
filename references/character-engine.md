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

## Separate cognition from expression

A **cognitive resource** helps the character comprehend or privately judge a cue. It may be knowledge, a belief, a value priority, an analogy, an attention rule, an attribution habit, an expertise boundary, or a misconception. It must not prescribe a convenient line.

A **speech-corpus entry** is approved evidence about how this character has expressed a particular kind of stance, tactic, uncertainty, repair, or relationship register under stated conditions. It must not grant knowledge, change a belief, or decide the character's current objective. Retrieve it only after the private judgment and social objective exist.

Keep the direction one way:

```text
cognitive resources -> private judgment -> expression retrieval
```

Never select a plausible-sounding line first and invent cognition to justify it. The existing `character.yaml.expression` fields and `speech-samples.md` remain valid compact evidence. `speech-corpus.yaml` is the normalized, provenance-bearing form for projects that need reliable retrieval; it is additive rather than a requirement for every narrow task.

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

## Track knowledge status and confidence

Use explicit knowledge status for consequential propositions:

- `known`: available to the character as a supported fact within the story's evidence boundary;
- `inferred`: a conclusion the character drew from available evidence;
- `suspected`: a live possibility they have not resolved;
- `mistaken`: a belief they hold that the story contract marks as partial or false;
- `unknown`: explicitly unavailable to this character, even if the author or audience knows it.

Record confidence separately from status. Confidence describes how strongly the character relies on the proposition; it does not turn an inference into knowledge. Keep its basis, limits, disconfirming evidence, and update trigger. A new cue may change confidence without changing status, or change status without settling every uncertainty.

Common ground is proposition-specific. For proposition `P`, record who knows or accepts `P`, who believes the others know or accept it, the provenance for that state, confidence by participant, and the last update. Several people independently knowing `P` is not automatically common ground. A compressed look, code, or silence may activate established common ground but cannot transmit a new proposition.

Second-order belief is directional: what A believes B knows, suspects, wants, or will infer. It may be wrong. Store the holder, target, proposition kind, status, confidence, evidence, source provenance, and update. Do not replace it with an omniscient group summary.

## Retrieve and decide in ordered stages

First retrieve locked resources that help the character **understand** the cue: similar experiences, relationship history, domain knowledge, common-ground propositions, second-order beliefs, fears, and active misconceptions. Open, rejected, or selected-but-unlocked life-path branches are not retrievable resources.

Then complete the private and pragmatic chain before selecting wording:

```text
perceived cue
-> comprehension retrieval
-> private interpretation
-> pragmatic attribution
-> inference and belief delta
-> first impulse, stance, and social objective
-> expression retrieval
-> suppression, redirection, or permission
-> action, spatial change, gaze, expression, silence, or line
-> observable consequence and state update
```

Expression retrieval may use approved speech-corpus entries, relationship register, familiar tactics, or physically available actions. It supplies options, not an answer. Reject an option if it exceeds the character's knowledge, externalizes private analysis without a tactic, recaps mutual knowledge, conflicts with the current relationship register, or does work that a simpler action or silence already performs. After choosing a surface, mute every proposed line once: if the action still produces the same consequence and leaves the same next choices, suppress the line. Do not mistake a line allowance for a quota or make a supposedly protective character verbally control the person whose agency the tactic is meant to restore.

Do not lose lexical evidence during the literal read. Words such as “this time,”
“again,” “already,” “still,” “we,” a repaired pronoun, an unexpected title, or a
change from singular to plural carry presuppositions and relationship pressure. They
may support an inference, competing explanations, or an explicit no-change record;
they must not disappear into a generic summary of the cue.

Run a cue-coverage check for compact runtime output. Every information-bearing word,
gesture, timing change, or spatial move is either cited by an inference, marked as
noticed but unresolved, marked as not noticed, or deliberately deferred. Do not
force it to mean something, but do not silently drop it.

The same cognitive rule in two relationships need not produce the same question.
Relationship evidence may already settle one uncertainty, change who must be tested,
permit a provisional action, or make silence more costly. Re-run appraisal and
strategy with that evidence before changing register. If two versions retain the
same tactic and differ only in contractions, politeness, or sentence length, the
relationship layer has not changed behavior.

Before wording a relationship comparison, hide the lines and compare only: what the
character wants the other person to do next, what risk the character accepts, what
minimum need or vulnerability is disclosed, whether personal assurance is tested,
and whether the response acts, delays, or withholds. If these are identical, rerun
one strategy before changing syntax. On the visible surface, expose only the one
lever the other person must answer in this beat; keep the remaining debt, evaluation,
knowledge, and delay model private for later beats.

Prefer a small scene-local set that changes the current judgment. A common working range is three to seven memories, but relevance matters more than a fixed count. Rank comprehension resources by cue relevance, unresolved force, relationship relevance, confidence, and recency. Rank expression evidence separately by relationship, register, context, pragmatic function, and provenance. A valid result may retrieve no line at all.

## Build the speech corpus from evidence

An entry is usable only when it is tied to the same character and compatible locked biography revision. Retain source references and relevant life-path nodes, then scope the evidence by:

- counterpart or relationship type, intimacy, power, and exclusions;
- register, address behavior, directness, and status behavior;
- situation, social objective, tactic, risk, body, and emotion;
- clause shape, subject omission, rhythm, breath, interruption, and length conditions;
- self-correction, backtracking, qualification, and uncertainty marking;
- pragmatic function, paired nonverbal options, and contexts to which it must not be generalized.

Maintain an explicit list of forbidden generic phrase families when a project has identified them. Give each ban a reason and scope; do not create a universal blacklist detached from character and context. A catchphrase is not individuality, and a sample approved in one relationship is not automatically valid in another. New wording may be drafted when no entry matches, but it stays provisional and must not be silently promoted into approved character evidence.

Corpus attributes are permissions and retrieval clues, not boxes to tick. An entry
that allows interruption, subject omission, correction, or complete conditional
questions does not require every feature in one line. Nor does a general shared
register authorize a new private code word. Use shorthand only when its meaning is
already established in common ground. In controlled comparisons, hold the incoming
cue fixed and compare the first response before inventing the other person's next
line.

When a controlled comparison continues beyond the first response, feed both branches
structurally equivalent new evidence or stop the comparison at the shared boundary.
Do not let an invented reply improve one branch while the other still answers only
the original cue.

## Turn-state contract

Before a consequential response, track compact fields rather than writing a hidden essay:

| Field | Content |
|---|---|
| Cue | What the character actually perceived |
| Literal read | What the words or action directly mean |
| Comprehension retrieval | Relevant cognitive-resource, memory, relationship-claim, common-ground, second-order-belief, or `life-path:<branch>/<node>` references, including checked unknowns |
| Retrieved factors | Backward-compatible compact summary of the relevant locked resources |
| Private interpretation | What the cue means to this person before they attribute an intention |
| Pragmatic attribution | Why the character thinks the other person did this here and now; legacy `attribution` is its compact projection |
| Inference and belief delta | What proposition, status, or confidence changed, and on which evidence |
| Judgment | Current conclusion, question, or refusal to conclude |
| First impulse | The first bodily or relational move before suppression or social filtering |
| Stance | Agree, oppose, doubt, reserve, conceal, or undecided |
| Confidence | Low, medium, or high, with the evidence boundary |
| Social objective | What change they want in the other person this turn |
| Strategy | Ask, test, reassure, accuse, deflect, bargain, joke, lie, act, or remain silent |
| Expression retrieval | Compatible speech-corpus entries, relationship register, wording options, and nonverbal options considered only after the objective exists |
| Modulation and suppression | What the character suppresses, redirects, or permits and why |
| Response decision | Whether to answer, act, delay, misdirect, or withhold |
| Surface | The selected action, spatial relation, gaze, expression, pause, silence, or line |

The surface should usually contain less than the private state.

When the requested deliverable is a compact runtime rather than only a screenplay,
do not shorten the trace by deleting the middle. Include, in order, the
comprehension resource refs, private interpretation, pragmatic attribution,
inference, belief or confidence delta, judgment, stance, social objective,
expression-corpus refs, suppression/output choice, observable surface, and
consequence. Write `no_change` with the checked proposition when a cue changes no
belief; absence is not an auditable no-change decision. If supplied resources lack
stable IDs, assign temporary scene-local refs such as `input:cognitive-01` and
`input:speech-close-01`, label them non-persistent, and use the same refs throughout
the trace. This exposes compact state and evidence, not private chain-of-thought.

`turn-state.yaml` retains the flattened v0.2 `turns` records and adds parallel `decision_traces` with dedicated comprehension, private-interpretation, pragmatic-attribution, inference, belief-update, and expression-retrieval fields. Existing files remain readable. When both forms are populated, bind each trace to its turn and character, treat the trace as the detailed reasoning record, and keep compact fields such as `retrieved_factors`, `attribution`, stance, objective, modulation, and surface consistent with it.

For a multi-character scene audit, supply each participant's cognitive, speech, and
memory file separately and the relevant relationship ledger. Resource IDs resolve
inside the current character's namespace; an ID found only in another participant's
library is an error, not a fallback. A claimed memory, relationship claim,
common-ground proposition, or second-order belief likewise requires its source
index. A nonverbal response may explicitly record `not_applicable_nonverbal` with
an action or silence option and no speech-corpus ID.

## Update after every exchange

Update only what changed:

- new fact or new suspicion;
- belief confidence;
- perceived intention of the other person;
- common-ground status or a directional second-order belief, but only when the turn supplies evidence for that update;
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

Use `assets/templates/life-path-workbench.yaml`, `life-path-biography.md`, `character.yaml`, `cognitive-resources.yaml`, `memories.yaml`, `relationship-ledger.yaml`, and, when normalized expression retrieval is needed, `speech-corpus.yaml`. Scene work may bind the relevant IDs in `scene-contract.yaml` and trace the ordered decision in `turn-state.yaml`.
