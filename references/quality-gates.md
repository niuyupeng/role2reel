# Quality gates and calibration

Automated checks catch omissions and contradictions. They do not prove that dialogue is human, acting is truthful, or a shot is good. Combine linting with blinded human comparison.

## Hard gates

Treat these as errors:

- a material source claim is fabricated, reassigned, or made more certain without authorization;
- an occupation, school, credential, award, diagnosis, or identity category is used as sufficient evidence for personality, morality, speech style, or first response;
- an open, rejected, or selected-but-unlocked life-path branch enters character, memory, relationship, outline, scene, turn-state, or screenplay artifacts;
- a fact snapshot, locked candidate, approved biography, exact compiled file, or formal outline review has a stale content hash or revision;
- an author path decision, biography approval, runtime ledger, or compiled asset is replayed against a different character/package identity, branch, fact-boundary hash, candidate hash, path-lock revision, biography revision, or body hash;
- a path lock is treated as author approval for concrete facts added during long-biography expansion;
- a shared event lacks an exact revision/hash author approval, reverses a comparable time window, or points to a missing, unlocked, unapproved, stale, contradictory, or body-hash-mismatched participant binding;
- a structured runtime artifact omits canonical source references, changes after its file hash is recorded, disagrees with its declared provenance closure, or uses a relationship-ledger/type declaration to evade the applicable audit;
- a formal scene consumes an absent, changed, symlinked, or out-of-project outline rather than the exact file and hash that were reviewed;
- fictional prehistory is presented as a discovered fact about a real person;
- a `deep` biography is below its 30,000-countable-Han-character default, or reaches it through rejected material, quotation, duplicated summaries, repeated padding, random trivia, résumé lists, adjective piles, or forced trauma;
- a character uses information outside their knowledge boundary;
- a character explains mutually known history to equally informed partners without a scene tactic that requires the explanation;
- generated dramatic dialogue merely verbalizes private analysis or repeats the visible image while changing no power, intimacy, risk, obligation, certainty, or available tactic;
- an effect precedes its perceptible cause;
- timeline segments overlap or reverse; when an exact duration is required, the timeline also fails if it has an unexplained gap, does not start at 0, or does not end at the requested duration;
- a shot lacks a discernible duty or contradicts locked continuity;
- a reference asset has no defined role or imports excluded identity, wardrobe, setting, or audio;
- provider-specific constraints are stated as verified when they were not checked.

## Warning gates

Review rather than automatically reject:

- long or syntactically complete dialogue under high emotion;
- repeated explanation of visible facts;
- every beat being given dialogue when established gaze, expression, action, or silence could perform the state change;
- consecutive exchanges that change no state;
- characters differentiated mainly by catchphrases;
- facial-part choreography without a preceding cue and decision;
- camera movement with no perceptual or narrative motive;
- a speaker close-up used when the listener's comprehension matters more;
- music, particles, transitions, slogans, logos, or calls to action added without a requested function.

## Dialogue review

Score each scene from 1 to 5 on:

- causal response;
- knowledge integrity;
- character-specific judgment;
- tactical interaction and consequence;
- subtext precision;
- speakability and breath;
- relationship movement;
- preservation of source intent.

A low score should point to a repairable cause, not produce vague “make it more natural” feedback.

## Life-path and deep-biography review

For a `deep` character, run `python scripts/audit_life_paths.py <workbench> --require-locked` and then review what a script cannot judge. A green audit proves configured mechanical contracts only; it does not prove that the author made the recorded choice, independently approve a biography revision, establish that candidates are semantically distinct, show that each cited source semantically supports its claim, or show that the biography has causal and artistic density:

- the locked-path biography contains at least 30,000 countable Han characters, passes the configured mechanical exclusions, and has separate author approval bound to its exact revision and body hash;
- stages form a continuous temporal account to the script opening, with unknown gaps labeled rather than invented invisibly;
- every consequential node changes knowledge, expectation, relationship, available strategy, debt, pride, shame, constraint, or unresolved pressure;
- at least three candidates are compatible with the hard facts yet differ in causal spine and creative consequence, not surface labels;
- rejected branches do not leak, and changing the lock invalidates downstream artifacts from the old revision.

Do not treat the character-count gate as evidence of artistic quality. Use a blinded reader for causal coherence, non-stereotyped individuality, ordinary-life texture, relationship truth, and dramatic usefulness.

Run these behavioral acceptance checks:

1. Lock different paths while preserving the same present facts; attention, private interpretation, first response, relationship move, or expression channel changes materially.
2. Preserve the path while changing occupational context; core value order and relationship strategy remain, while genuinely role-dependent knowledge or tools may change.
3. Remove a formative node; a downstream response changes for a traceable reason, or the node is decorative.
4. Confirm that rejected and unlocked branches have zero downstream references.
5. Activate a shared context; only participants with the relevant mutual knowledge understand the compressed cue, and nobody recaps it afterward.
6. Delete every line replaceable by nonverbal behavior without losing strategy or state change.
7. Hide character names; distinguish speakers through attention, choice, and relationship strategy rather than catchphrases.
8. Ask an actor what the character is pursuing, hiding, suppressing, or changing in every beat; reject mechanical facial parameters.
9. Compare the locked life with the outline; expose incompatibilities and preserve author choice instead of silently rewriting either layer.

## Storyboard review

Check:

- every shot has a unique duty;
- adjacent reaction and ending-state shots are merged when the audience's task and visible state do not change;
- geography, eyelines, screen direction, identity, wardrobe, props, and light remain legible;
- cuts correspond to state or audience-need changes;
- movement is motivated and static shots remain available;
- performance and physical chains preserve cause before response;
- timing accommodates speech, comprehension, action, and holds;
- sound has a source or an intentional off-screen function.

## Calibration with human decisions

For a real production team, compare at least:

- baseline workflow;
- unstructured longer character biography;
- locked life path plus a separately author-approved deep biography when applicable, followed by compiled runtime, knowledge boundaries, shared-context compression, traceable scene transfer, and turn-state simulation.

Blind reviewers to the method. Record:

- direct adoption;
- adoption after light edit;
- rejection;
- edit distance, magnitude, and categorized reasons;
- whole-scene no-rewrite rate;
- removed exposition count;
- speaker-identification accuracy with names hidden;
- actor read-aloud fluency;
- character consistency and scene consequence scores.

Do not promise an adoption-rate improvement before collecting comparable human decisions. Save individual decisions with `assets/templates/calibration-record.yaml`, including the human final version and reason codes. Prefer narrow changes supported by repeated evidence over adding a universal rule for each rejected line.

## Included linters

- `python scripts/audit_dialogue.py <file>` flags likely exposition, generic AI phrasing, duplicates, and unusually long dialogue lines.
- `python scripts/audit_life_paths.py <life-path-workbench.yaml> --require-locked` checks decision bindings, exact duplicate spines, fact-boundary IDs and hashes, cited feasibility references, declared coverage fields, full-biography length, obvious repeated padding, separate biography approval, exact compiled-file hashes and source closure, structured provenance, the conditional formal-outline gate, and any shared-event ledger declared by the workbench. `--relationship-ledger <relationship-ledger.yaml>` remains available for a direct registry audit or an explicit cross-check.
- `python scripts/audit_staged_eval.py <staged-life-path-eval.yaml>` refuses `behavior_pass: true` unless the exact audited deep inputs, compilation outputs, per-run input/source closures, distinct files and bytes, task/output trace bindings, and five-output blind-review coverage are complete. It re-runs the mechanical life-path audit and verifies record integrity, not that the declared tasks or reviews actually occurred.
- A staged blind-review record needs an explicit verdict or status for every metric and output. Ratings may be retained as supporting data, but an undeclared numeric scale cannot by itself establish a pass.
- `python scripts/audit_storyboard.py <csv-json-or-yaml>` checks required fields, IDs, finite numeric time ranges, ordering, gaps, and overlaps. Add `--expected-duration <seconds>` for an exact-duration deliverable; that mode also requires continuous coverage from 0 through the requested endpoint.
- `python scripts/validate_repo.py` checks skill structure, local links, metadata, scripts, and unfinished placeholders.

Warnings are prompts for review, not automatic rewrites.
