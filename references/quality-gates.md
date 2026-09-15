# Quality gates and calibration

Automated checks catch omissions and contradictions. They do not prove that dialogue is human, acting is truthful, or a shot is good. Combine linting with blinded human comparison.

## Hard gates

Treat these as errors:

- a material source claim is fabricated, reassigned, or made more certain without authorization;
- an occupation, school, credential, award, diagnosis, or identity category is used as sufficient evidence for personality, morality, speech style, or first response;
- a 命线反演 exploration selects, ranks, scores, or assigns probabilities to a winner, or presents a fictional reading as private truth about a real person;
- candidate lives differ only through renamed credentials, places, dates, status, or trait adjectives while retaining the same causal mechanism and opening response;
- an open, rejected, or selected-but-unlocked life-path branch enters character, memory, relationship, outline, scene, turn-state, or screenplay artifacts;
- a fact snapshot, locked candidate, approved biography, exact compiled file, or formal outline review has a stale content hash or revision;
- an author path decision, biography approval, runtime ledger, or compiled asset is replayed against a different character/package identity, branch, fact-boundary hash, candidate hash, path-lock revision, biography revision, or body hash;
- a path lock is treated as author approval for concrete facts added during long-biography expansion;
- a shared event lacks an exact revision/hash author approval, reverses a comparable time window, or points to a missing, unlocked, unapproved, stale, contradictory, or body-hash-mismatched participant binding;
- a structured runtime artifact omits canonical source references, changes after its file hash is recorded, disagrees with its declared provenance closure, or uses a relationship-ledger/type declaration to evade the applicable audit;
- a formal scene consumes an absent, changed, symlinked, or out-of-project outline rather than the exact file and hash that were reviewed;
- fictional prehistory is presented as a discovered fact about a real person;
- a `deep` biography omits story-relevant causal or relationship coverage, invents author approval, or substitutes rejected material, repeated padding, random trivia, résumé lists, adjective piles, or forced trauma for useful history;
- a character uses information outside their knowledge boundary;
- a scene skips comprehension retrieval, has no private interpretation or stance, or uses speech style and catchphrases in place of a character-specific judgment;
- cognition and expression are sourced from the same undifferentiated retrieval list when the production package declares separate cognitive and speech libraries;
- a character explains mutually known history to equally informed partners without a scene tactic that requires the explanation;
- generated dramatic dialogue merely verbalizes private analysis or repeats the visible image while changing no power, intimacy, risk, obligation, certainty, or available tactic;
- an effect precedes its perceptible cause;
- timeline segments overlap or reverse; when an exact duration is required, the timeline also fails if it has an unexplained gap, does not start at 0, or does not end at the requested duration;
- a shot lacks a discernible duty or contradicts locked continuity;
- a reference asset has no defined role or imports excluded identity, wardrobe, setting, or audio;
- a video task selects more than one primary mode, borrows an undeclared source property, lacks its mode-specific target or seam contract, or rewrites locked upstream meaning;
- provider-specific constraints are stated as verified when they were not checked.

## Warning gates

Review rather than automatically reject:

- long or syntactically complete dialogue under high emotion;
- repeated explanation of visible facts;
- every beat being given dialogue when established gaze, expression, action, or silence could perform the state change;
- consecutive exchanges that change no state;
- characters differentiated mainly by catchphrases;
- three or more candidate lives that all become respectable upward-mobility narratives, all rely on a single trauma, or all predict the same first response;
- an author-facing exploration that leads with IDs, hashes, and provenance tables before giving readable alternatives;
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

Check the two retrieval stages separately. The comprehension pass should cite the
experience, knowledge, belief, memory, and relationship material that makes the cue
mean something to this person. Only after a judgment and social objective exist
should the expression pass retrieve relationship-appropriate syntax, register,
repair habits, withholding patterns, or approved speech evidence. If the line can be
created from the speech corpus without the cognitive pass, it is voice styling rather
than character behavior. If every person makes the same judgment in different
wording, the cognition layer has failed.

## 命线反演 exploration review

Before production lock, review the author-facing readings without looking at their
IDs:

- the same locked present remains intact in every reading;
- each path has a different causal engine, relationship cost, self-story, residual
  pressure, and testable opening impulse;
- at least one counter-reading resists the obvious summary-label explanation;
- agency and circumstance can coexist, as can effort and avoidance, without a
  single moral verdict;
- ordinary stretches connect turning points rather than every year becoming an
  incident;
- each reading says what it explains, what stays unknown, and what additional trace
  would support or weaken it;
- the writer can select, edit, splice, reject all, regenerate, or preserve an unknown,
  and no model recommendation silently becomes canon.

Ask whether a reader would describe the alternatives as different lives, not the
same résumé with different decorations. “Surprising” is not permission for random
trauma; the path should feel unexpected beforehand and coherent afterward.

## Life-path and deep-biography review

For a `deep` character, run `python scripts/audit_life_paths.py <workbench> --require-locked` and then review what a script cannot judge. A green audit proves configured mechanical contracts only; it does not prove that the author made the recorded choice, independently approve a biography revision, establish that candidates are semantically distinct, show that each cited source semantically supports its claim, or show that the biography has causal and artistic density:

- the locked-path biography meets the content-sufficiency criteria in life-paths.md, passes applicable mechanical checks, and has separate author approval bound to its exact revision and body hash;
- stages form a continuous temporal account to the script opening, with unknown gaps labeled rather than invented invisibly;
- every consequential node changes knowledge, expectation, relationship, available strategy, debt, pride, shame, constraint, or unresolved pressure;
- at least three candidates are compatible with the hard facts yet differ in causal spine and creative consequence, not surface labels;
- rejected branches do not leak, and changing the lock invalidates downstream artifacts from the old revision.

Do not impose a character-count gate unless the author explicitly requests one, and never treat length as evidence of artistic quality. Use a blinded reader for causal coherence, non-stereotyped individuality, ordinary-life texture, relationship truth, and dramatic usefulness.

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

Also verify that the board cites the exact approved scene/meaning revision, that
every visual entity and wardrobe state resolves to the visual bible, that an entire
shot may be explicitly nonverbal while retaining sound, and that each shot's
`state_out` can hand off to the next shot's `state_in`.

## Video-task review

Check the provider-neutral task before rendering provider syntax:

- exactly one primary mode is selected;
- generation, exact/long generation, extension, edit, two-source transition, and
  multi-panel tasks satisfy their own input and handoff contract;
- every reference states borrow, target, interval, preserve, and exclude, with all
  undeclared inheritance denied;
- identity, body, wardrobe, accessory, voice, geography, prop, screen direction,
  camera, sound, and first/last states stay locked where required;
- the exact timeline has no gap or overlap and preserves stimulus before reaction
  and contact before physical result;
- current provider/model/interface/date/source were verified whenever a changing
  provider capability is claimed.

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
- `python scripts/audit_humanization.py <raw-source> <meaning-ledger.yaml> <humanized-draft.md> --source-revision <revision>` opens all three real files and checks source path/revision/hash, stable ledger and draft IDs/revisions, normalized draft-body hash, and exact approval bindings. It cannot judge meaning fidelity, ledger completeness, or whether the recorded approval really occurred.
- `python scripts/audit_character_runtime.py <turn-state.yaml> --cognitive-resources <character-a.yaml> --cognitive-resources <character-b.yaml> --speech-corpus <character-a.yaml> --speech-corpus <character-b.yaml> --memories <character-a.yaml> --memories <character-b.yaml> --relationship-ledger <file>` checks a whole multi-character turn-state against character-scoped cognition, memory, relationship, common-ground, second-order-belief, and approved expression evidence. Repeat each per-character option as needed. Referenced IDs fail closed when their source index is absent, unknown, duplicated, malformed, or owned by another character; explicit nonverbal no-match remains valid. The audit also checks that legacy turn projections do not contradict their detailed decision traces. It cannot validate a psychological interpretation or make a line good.
- `python scripts/audit_life_paths.py <life-path-workbench.yaml> --require-locked` checks decision bindings, exact duplicate spines, fact-boundary IDs and hashes, cited feasibility references, declared coverage fields, optional explicitly requested biography length, obvious repeated padding, separate biography approval, exact compiled-file hashes and source closure, structured provenance, the conditional formal-outline gate, and any shared-event ledger declared by the workbench. `--relationship-ledger <relationship-ledger.yaml>` remains available for a direct registry audit or an explicit cross-check.
- `python scripts/audit_staged_eval.py <staged-life-path-eval.yaml>` refuses `behavior_pass: true` unless the exact audited deep inputs, compilation outputs, per-run input/source closures, distinct files and bytes, task/output trace bindings, and five-output blind-review coverage are complete. It re-runs the mechanical life-path audit and verifies record integrity, not that the declared tasks or reviews actually occurred.
- A staged blind-review record needs an explicit verdict or status for every metric and output. Ratings may be retained as supporting data, but an undeclared numeric scale cannot by itself establish a pass.
- `python scripts/audit_storyboard.py <csv-json-or-yaml>` checks required fields, IDs, finite numeric time ranges, ordering, gaps, and overlaps. Add `--expected-duration <seconds>` for an exact-duration deliverable; that mode also requires continuous coverage from 0 through the requested endpoint. A modern board additionally requires `--meaning <file> --scene <file> --beats <file> --visual-bible <file>` so IDs, revisions, file hashes, and asset revisions are checked against actual documents; legacy v0.1 row boards remain structural-only.
- `python scripts/audit_continuity.py <continuity.yaml> --storyboard <storyboard.yaml> --visual-bible <visual-bible.yaml>` opens the real bound documents before checking explicit lock decisions and adjacent shot-state handoffs. Legacy v1 ledgers remain compatible. `--allow-unbound-structure` is a clearly non-production draft lint only.
- `python scripts/audit_video_task.py <video-task.yaml> --storyboard <file> --continuity <file> --visual-bible <file> --asset-contract <file>` opens all four real upstream files; it checks exact source bindings, verifies that the supplied continuity itself binds that same storyboard and visual bible, then checks one primary mode, timeline, deny-by-default borrowing, locks, immutable media bindings, and mode-specific extension/edit/transition/multi-panel fields. Local media is resolved below the asset-contract directory by default (or `--asset-media-root`); provider media requires immutable provider asset ID and version. `--allow-unbound-structure` is a clearly non-production draft lint only. It does not prove that a provider supports the task or that a render succeeded.
- `python scripts/validate_repo.py` checks skill structure, local links, metadata, scripts, and unfinished placeholders.

Warnings are prompts for review, not automatic rewrites.
