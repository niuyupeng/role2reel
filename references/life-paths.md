# Multi-candidate life-path development

This layer gives consequential fictional characters a lived pre-story history before they are asked to carry plot or dialogue. It turns sparse story material into author-controlled creative hypotheses, then compiles the chosen history back into the existing Role2Reel character and scene runtime.

Role2Reel includes a deliberately fortune-reading-shaped creative method: **命线反演 (fictional life-path reverse inference; 类推命式虚构人物前史推演)**. It borrows one useful imaginative operation from a reading—several hidden lives may explain the same few present signs—without claiming supernatural knowledge, probability, psychological diagnosis, social consensus, or discovery of a real person's private past. See [fatecasting.md](fatecasting.md) for the author-facing method.

## When to use it

Use this workflow when the user asks for a character biography or life trajectory, when a main or recurring character is defined mostly by current labels and plot functions, or when different characters keep producing interchangeable judgments, actions, and dialogue.

Do not force it into typo-only correction, faithful transcript cleanup, a minor functional role, or an already locked character whose requested scene is fully supported by existing canon. Multi-agent review can help during development or evaluation, but it is not a required runtime architecture.

## Separate exploration from production lock

Use two explicit modes:

- `explore`: present at least three readable, genuinely causal life readings. They are fictional possibilities, not canon, probabilities, or an invitation for the model to choose a winner. The author may select, edit, splice, reject, regenerate, or preserve an unknown. Keep IDs and hashes out of the reading flow unless the author asks for the audit view.
- `production-lock`: translate an author-chosen or author-composed reading into the formal fact boundary, candidate spine, provenance, decision, and lock records below. Only this mode can authorize canon-bound biography expansion or downstream compilation, and only after an actual author decision. Explicitly requested non-canon review drafts use the separate draft-expansion contract below.

Do not make a user complete production paperwork merely to compare possibilities. Conversely, do not treat enthusiasm for an exploratory reading as a formal path lock. `assets/templates/life-path-reading.md` is the readable exploration surface; `assets/templates/life-path-workbench.yaml` remains the auditable production record.

## Establish the fact boundary

Before proposing a past, separate:

- author-locked facts and events;
- observable present traces in the supplied material;
- first-person claims and other people's testimony;
- misunderstandings, rumors, and disputed accounts;
- the author's preferences and permitted changes;
- AI candidate hypotheses;
- unknowns that may remain unknown;
- contradictions that must be exposed rather than silently repaired.

Give every declared item a stable ID, content, and source reference. Candidate `supports`, `conflicts`, and `unknowns` fields cite those IDs instead of repeating unverifiable prose. The category fields must exist when a branch is selected or locked; an honest empty list is preferable to inventing a conflict or unknown merely to fill the form. Hash the complete fact boundary at lock time. Reusing claim IDs while changing their content or sources invalidates the path lock, biography approval, outline review, and runtime just as surely as editing the causal spine.

Current identity, age, education, work, status, achievement, and group statistics may constrain feasibility or act as weak priors. None may directly create personality, values, memories, morality, or a speaking style. AI-generated history is not a found truth. A candidate path becomes eligible for story canon only through an explicit author path lock; expanded biography prose and any new details require separate approval of the exact biography revision and body hash before downstream use.

For a living or identifiable real person, do not infer private or sensitive history. Offer only clearly labeled fictionalization when the user is actually creating a fictional counterpart and has authorized that scope.

## Generate comparable candidates before long-form expansion

Produce at least three causally distinct, fact-compatible outlines before writing a deep biography. The author may ask for more, but no scorer or model may automatically choose a single winner.

In `explore` mode, present those outlines first as readable life readings rather than schema dumps. Each reading should let the author feel the route from present traces through ordinary years, choices, pressures, costs, self-story, and unresolved residue to the character's opening impulse. Include a counter-reading that explains the same fixed traces through a materially different causal route. Use the divergence method in [fatecasting.md](fatecasting.md); do not derive a path from a demographic, educational, occupational, or status stereotype.

Candidates must differ in how the person reached the present and in the creative consequences of that route. Changing names, places, dates, résumé items, or trait adjectives is not a different path.

Each consequential causal node should be sufficient to establish:

- the period, environment, relationships, and material constraints;
- what happened or persisted;
- what the person could know then;
- how they interpreted it;
- what choice they made and what alternatives were unavailable or refused;
- the cost of that choice;
- feedback from other people and reality;
- the resulting update to belief, value priority, or coping strategy;
- unresolved residue;
- present triggers that may retrieve it.

Do not turn every event into a tiny deterministic state machine. Use nodes for changes that matter; ordinary stretches can be represented as patterns when they alter or reinforce a relationship, expectation, resource, habit, or self-story.

Allow mixed causality. Effort and avoidance, success and failure, agency and coercion, luck and support, pride and shame may coexist. Existing tendencies influence choices, and the consequences of those choices can reinforce, compartmentalize, challenge, or reverse those tendencies. Avoid uniform inspirational arcs, trauma-only explanations, and category stereotypes.

For each candidate, expose:

- support from the supplied facts or traces;
- conflict with them;
- remaining unknowns;
- basic real-world feasibility;
- likely effects on theme, character arc, relationships, and present response.

For a formal candidate-only handoff in `production-lock` mode, do not compress these audit fields into an unreferenced prose summary. Show each fact-boundary item as `id + category + content + source_ref`. Then show, for every candidate, explicit `supports`, `conflicts`, and `unknowns` lists that cite those IDs, a feasibility note, creative consequences, and causal nodes that retain context, available knowledge, interpretation, choice, cost, feedback, update, residue, and present trigger. A source reference may point to a labeled clause or section of the supplied material; it must not pretend that an external source was checked when none was provided. This formal view follows the author-facing reading; it does not replace it.

These are materials for author judgment, not probabilities that claim to reveal which hidden past is true. Do not rank them as most likely, safest, strongest, or best unless the author supplies a separate creative criterion and explicitly asks for a comparison against that criterion; even then, the comparison cannot make the selection or lock on the author's behalf.

## Preserve author control

The author can select, reject, regenerate, edit a node, keep an intentional unknown, or combine compatible material. Combining material creates a new coherent candidate with explicit provenance; it is not a pile of the most dramatic events from several branches.

Use explicit states:

- `open`: branches are being explored and none may enter downstream canon;
- `selected`: one branch or composition is being developed but remains revisable;
- `locked`: the author has approved a numbered revision as story canon.

Only the locked branch may enter a canon-bound long biography, memory, relationship, outline, scene, turn-state, dialogue, storyboard, or video prompt. The expressly requested author-review draft exception below does not authorize downstream compilation. Give each workbench a stable `character_id` and `package_context_id`. The author-decision record and lock bind both identifiers plus the exact branch, fact-boundary hash, candidate-content hash, and lock revision; changing any of them requires a new decision rather than replaying an old approval. This prevents an approval copied from one character package from authorizing another. Locking the causal branch authorizes expansion; it does not declare the resulting long biography complete. A later unlock or change creates a new revision and makes prior downstream compilations stale. Never overwrite existing author canon or mix branches silently.

The lock declaration must point to an actual author decision in the conversation or project record. The model must not manufacture the decision record because one candidate scores well. A static audit can verify that a declaration is complete and internally consistent; the workflow and forward tests must verify that the author truly chose it.

## Expand the locked path into a deep biography

### Explicitly requested author-review draft

If the author has selected an identifiable route and now explicitly asks to develop its biography, proceed with a clearly labeled `author_review_draft`; do not ask them to select it again merely because backstage lock metadata has not been created. Record the selection source, exact candidate/source version, expansion request, and new-detail approval as pending. Keep formal lock fields null when no valid lock exists. This is permission to draft for review, not permission to declare canon, compile character runtime, or alter the screenplay. Existing strict production-lock audit requirements remain unchanged.

Handle a cast's readiness per character. Expand selected roles without silently choosing the others; keep unselected roles at a fact/interpretation boundary and ask only the remaining consequential choice. A correction to one role must not reset other actual selections. Do not label a partial cast package as all biographies complete.

The initial fate reading is a causal candidate skeleton, not a completed life. A requested rich biography must expand lived time before the opening: recurring routines, pleasures, relationships beyond work, unsuccessful repairs, material and institutional limits, choices, feedback and contradictions. Preserve childhood/early-life unknowns when specifics would impose unsupported biology or world rules; do not fill them with an invented family tragedy. Use relative life stages when exact dates or ages are unknown. Distinguish narrative history from interpretation and keep the screenplay re-entry audit in a separate appendix, so plot recap and metadata do not masquerade as biography length.

Depth does not require every hobby or childhood object to foreshadow a plot beat. Let ordinary experiences have several consequences and let some remain ordinary. Carry the same relationships through time rather than appending isolated anecdotes that all prove one trait. Before handoff, identify concrete stage-to-stage changes and the unresolved costs the character brings to the opening. Report the actual scope and remaining gaps; no default page count, automatic short cap, or claim to know literally every moment of a fictional life.

For these drafts, use the biography template with `development_mode: author_review_draft`, `selected_candidate_ref`, and `expansion_authorization_ref`. Leave `life_path_lock_revision` and `locked_candidate_sha256` null until formal lock. Use a separate `selected_candidate_sha256` when freezing the readable selection. Draft review does not replace the production audit or final biography approval.

For a main or important character that must keep driving plot, relationships, and dialogue, `deep` mode requires rich, causally connected biography material derived from the locked path, with **no default page or character minimum**. Treat figurative requests for forty pages or forty thousand characters as requests for richness unless the author explicitly fixes a length. An initialized but unclassified role remains `unclassified` until the workflow establishes its story function. The system must not silently downgrade an important character. A project may explicitly choose a lighter tier for a minor or functional role and record that author decision. Passing the mechanical audit does not establish narrative sufficiency or constitute author approval.

A `light` path used for an isolated behavior or dialogue test remains a light fixture even when the resulting scene is excellent. Keep `evaluation_scope: light behavior fixture; not deep-biography evidence` (or an unambiguous Chinese equivalent) visible in the delivered test artifact. This label is metadata, not screenplay dialogue, and prevents a small successful sample from being cited as completion of the deep biography or fused production chain.

The candidate outlines remain compact until the author selects or compatibly composes one and requests expansion. Use the review-draft contract above when formal lock is absent; canon-bound expansion requires a resolved, explicitly locked route. If the author explicitly asks for several full alternatives, keep the review drafts isolated, and lock each route separately before canon-bound use. Every alternative presented as full must satisfy its declared depth contract. Every full alternative used downstream also requires separate approval of its exact biography revision and body hash.

The biography is a continuous causal life, not a résumé. Across the character's actual major stages, it should cover relevant ordinary life and turning points; family, education, work, place, class, era, body, money, and institutional constraints; relationship formation and erosion; success, failure, missed chances, shame, debt, secrets, and repair; value formation and revision; anomalous choices; differences between self-narration and events; mistaken memory or self-deception; unresolved residues; and traces visible at story opening.

Not every category must receive equal space, and no invented hardship is required merely to fill a heading. Unknown periods remain labeled unknown when invention is not authorized.

Count only the locked-path biography's original narrative body. Exclude YAML, IDs, scoring tables, source quotations, rejected branches, downstream screenplay dialogue, and duplicated summaries. Repetition, synonymous restatement, random trivia, adjective piles, scenery with no state change, résumé lists, and forced trauma do not establish depth. Obvious repeated paragraphs or fixed-length Han runs fail the mechanical padding check; semantic restatement and causal thinness still require human review.

Write a long biography stage by stage in a file instead of truncating it into one chat response. Its frontmatter must name the character ID, package context, locked branch, fact-boundary hash, candidate hash, path-lock revision, biography revision, and current status. Mark it `drafting` while incomplete and `ready` only after checking the content-sufficiency criteria below and applicable mechanical contracts. The author must then approve that exact character/package identity, branch, fact snapshot, candidate, path-lock revision, biography revision, and body hash; a path lock never grants blanket approval to details introduced during expansion. Any bound change invalidates biography approval and compiled runtime.

Run `scripts/audit_life_paths.py` before downstream compilation. The script checks structure, exact duplicate candidate spines, decision bindings, fact/candidate/biography hashes, optional explicitly requested length, obvious repetition, exact runtime files, and explicit provenance closure. It refuses a formal structured artifact that omits canonical path references, but it cannot judge whether every claim is semantically warranted, whether the life feels artistically true, or whether a human actually made either recorded approval.

### Content sufficiency, not bulk

For each important character, review the material against the actual outline. Record concrete source sections and scene consequences, not a self-awarded score:

- Causal continuity: relevant experiences and ordinary routines explain present expectations, choices, costs, and changes; the person is not a list of labels or isolated dramatic incidents.
- Conflicting wants and limits: identify what the person pursues, protects, avoids, misunderstands, and may sacrifice; include an example where priorities compete rather than adding trait adjectives.
- Relationship texture: show how shared events, trust, grievances, affection, status, and boundaries change behavior with different people. Keep other people's knowledge separate.
- Lived specificity: use relevant habits, material constraints, work and non-work life, pleasures, failures, and repair; do not manufacture trauma or trivia to fill a template.
- Scene transfer: trace the outline's consequential choices to available character evidence. Try the same current cue with another character or relationship; a change only in catchphrases is insufficient.
- Expression and restraint: supply situation-bound speech/action examples only after the stance is established. A rich biography must not produce exposition-heavy dialogue.

When a gap matters, name the affected beat and add the smallest coherent history or scene repair for author review. When added detail no longer changes relevant understanding, choices, relationships, or expression, stop expanding. This is not permission to reduce a recurring lead to a few generic traits: richness must support both the current story and the declared recurring use. Do not require an arbitrary number of anecdotes or pages.

`minimum_chinese_characters: null` (or omitted) means no length gate. A positive integer is an opt-in explicit length requirement, not a quality score; cite the actual user requirement in the project brief. Existing historical manifests with numeric thresholds retain them for reproducible audits. Do not silently rewrite old approval records; new revisions may remove inherited defaults in accordance with the current user clarification.

Mechanical audits check declared coverage, provenance, approval bindings, and obvious repetition; they cannot establish that these content criteria have actually been met. Keep human review pending until it occurs.

## Build shared lives consistently

Personal histories must agree across characters where they overlap. The project-level relationship ledger therefore includes a shared-event registry. Each event has one stable event ID, objective core, typed time window, numbered revision, content hash, exact-hash author approval, and participant bindings. Changing its objective core, time window, or participant bindings invalidates that hash and approval; comparable time endpoints must satisfy `start <= end`. Every binding names the character workbench, locked branch, fact-boundary hash, path-lock revision, candidate hash, approved biography revision and body hash, locked node references, perception version, and memory version. Each participant workbench declares the same ledger and event ID, so `--require-locked` audits the registry automatically instead of depending on a remembered CLI option. The cross-workbench audit does not require participants to remember the event in the same way.

Maintain who knows what, who knows that the others know it, debts, secrets, misunderstandings, taboos, established shorthand, old jokes, and cues that can retrieve a shared context. Shared-memory contracts point to the registry event instead of restating its objective core in free text.

A look, gesture, laugh, silence, object, or fragment of language may reactivate an established shared interpretation. It cannot transmit a new proposition that the relationship history never established. People who mutually know an event do not recap it for one another merely to inform the audience.

## Compile the biography into runnable assets

The long biography is offline story history, not scene-prompt material. Compile only useful, traceable residues:

| Approved-biography or locked-path residue | Runtime destination |
|---|---|
| objective event, subjective memory, present belief | separate event and memory records |
| learned expectation, attention bias, attribution rule | character runtime with node-level source references |
| knowledge, ability, misconception, information boundary | cognitive resources with lock revision and source references |
| desire, fear, pride, shame, debt, value priority | character and relationship ledgers |
| shared event, mutual knowledge, shorthand, taboo | shared-context relationship record |
| first impulse, default relationship move, defense, coping strategy | character runtime and scene bridge with causal dependencies |
| language resource grounded in history and relationship | expression evidence |

Use a small number of scene-relevant personal or shared memories at runtime. Never place the complete long biography in a scene prompt.

The compilation ledger separates locked life-path source references from artifact file records. The runtime and every record bind `compiled_for_character_id` and `compiled_for_package_context_id`, then name a type, project-root-contained UTF-8 regular file, exact file SHA-256, canonical `life-path:<branch>/<node>` source closure, fact-boundary hash, candidate hash, path-lock revision, biography revision, and body hash. Per-character structured assets carry the same identity inside `compiled_provenance`. Every shared structured artifact from scene through video—scene contract, turn state, beat map, storyboard, continuity, visual bible, asset contract, and video task—uses `character_sources[]`; each character workbench audits its own exact entry, while project-level cross-workbench review is still required for the other entries. Known structured artifacts must also contain canonical references in their own data; the current character's record and file reference sets must agree.

A compiled relationship ledger must be the exact file declared by the workbench. Relationship claims, common-ground propositions, second-order beliefs, and shared-memory contracts may carry per-record `character_sources[]`, so a claim derived from two lives does not force A's workbench to validate B's branch against A's candidates. The current workbench audits only its matching source record; the other participant still needs its own workbench audit. The shared-event registry continues to receive the stronger cross-workbench participant audit. This makes silent file edits, cross-character replay, provenance exemptions, and omitted explicit provenance fail mechanically, while semantic support for each creative claim remains a human review question.

Compile character, memory, and relationship assets before revisiting the outline. If an existing plot beat requires a choice incompatible with the locked life, report the conflict and offer options such as adding sufficient pressure, earning a transition, preserving intentional contradiction, or revising the beat. Do not automatically rewrite author canon or force the character to serve the plot. Narrow character-only compilation need not have an outline, but formal scene or screenplay compilation binds the exact project-contained outline file and SHA-256 as well as its version, fact-boundary hash, candidate hash and lock revision reviewed, conflicts, options and costs, author decisions, and status. Changing the outline invalidates that review. Scene-like content activates this gate from a declared type, path, or high-confidence structural discriminator; labeling it `other_structured` or setting a Boolean false cannot disable it. An unresolved hard conflict blocks formal scene compilation.

## Run the character before writing the line

For each consequential beat:

```text
current cue
-> what this person can actually know and notice
-> a few relevant personal or shared memories
-> private interpretation or misinterpretation
-> current judgment, desire, and relationship strategy
-> first bodily or relational impulse
-> decision whether to respond
-> action / gaze / distance / expression / pause / silence / minimum dialogue
```

Check nonverbal options first. Dialogue exists only when action, gaze, space, stopping, delay, silence, or shared context cannot perform the current strategy. A line may be long when the character has a specific strategic reason; restraint is not a fixed word limit.

Do not transcribe private analysis into speech, repeat what the audience sees, explain shared history to mutually informed people, or use generic facial choreography. Every visible performance choice should be traceable to a cue, comprehension, first impulse, suppression or redirection, and final action.

## Validate behavior, not just files

Required behavioral checks include:

- same present facts, different locked paths: attention, private interpretation, first response, relationship move, or expression channel changes materially;
- same locked path, changed occupational context: core value order and relationship strategy remain while genuinely role-dependent knowledge or tools may change;
- causal-node ablation: removing a formative event changes downstream behavior for an explainable reason, or the event is decorative;
- branch isolation: rejected and unlocked branches have zero downstream references;
- shared context: only participants with the relevant mutual knowledge can understand the compressed nonverbal exchange, and nobody recaps it afterward;
- dialogue deletion: any line replaceable by nonverbal behavior without losing strategy or state change is removed;
- name hiding: characters remain distinguishable through attention, choice, and relationship strategy rather than catchphrases;
- outline conflict: incompatibility between locked life and plot is exposed rather than silently overwritten;
- actor test: each beat has a playable pursuit, concealment, restraint, or change rather than mechanical facial parameters.

In a same-present path comparison, a residue may first change what the character checks or suspects before the uncertain condition is confirmed. Keep the cue and unknowns fixed, but instantiate each branch's attention, appraisal, and next relationship move; do not leave one run merely conditional and then claim a behavioral difference. When the user explicitly requests the comparison, make the smallest present-scene specification consistent with the supplied cue, apply it identically to every branch, and label it as reversible rather than inventing prior history. Call the comparison non-diagnostic only when no compatible present specification can engage the branch without contradicting locked facts; do not use that escape when a neutral wording or action can make the shared cue concrete.

Compare the original workflow, biography-length-only workflow, and the complete selected-life-path workflow under blinded human review. Record adoption, whole-scene no-rewrite rate, edit magnitude, explanatory-line removal, read-aloud naturalness, identifiability, and consistency. Do not promise an improvement before comparable evidence exists.

For an abbreviated illustration of the entire handoff, see [life-path-staged-example.md](life-path-staged-example.md). Its biography body is intentionally omitted; the example does not waive the real deep-file or author-approval gates.

For a recorded FT-14 run, populate `assets/templates/staged-life-path-eval.yaml` and run `scripts/audit_staged_eval.py`. A passing record re-runs the mechanical workbench audit and checks exact files, hashes, isolated task IDs, five controlled variants, traceability, and completed review fields. It still cannot prove execution honesty, reviewer independence, semantic branch isolation, or artistic success.
