# Multi-candidate life-path development

This layer gives consequential characters a lived pre-story history before they are asked to carry plot or dialogue. It turns sparse story material into author-controlled creative hypotheses, then compiles the chosen history back into the existing Role2Reel character and scene runtime.

It is narrative abduction, not fortune-telling, psychological diagnosis, social polling, or discovery of a real person's private past.

## When to use it

Use this workflow when the user asks for a character biography or life trajectory, when a main or recurring character is defined mostly by current labels and plot functions, or when different characters keep producing interchangeable judgments, actions, and dialogue.

Do not force it into typo-only correction, faithful transcript cleanup, a minor functional role, or an already locked character whose requested scene is fully supported by existing canon. Multi-agent review can help during development or evaluation, but it is not a required runtime architecture.

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

For a candidate-only handoff, do not compress these audit fields into an unreferenced prose summary. Show each fact-boundary item as `id + category + content + source_ref`. Then show, for every candidate, explicit `supports`, `conflicts`, and `unknowns` lists that cite those IDs, a feasibility note, creative consequences, and causal nodes that retain context, available knowledge, interpretation, choice, cost, feedback, update, residue, and present trigger. A source reference may point to a labeled clause or section of the supplied material; it must not pretend that an external source was checked when none was provided.

These are materials for author judgment, not probabilities that claim to reveal which hidden past is true.

## Preserve author control

The author can select, reject, regenerate, edit a node, keep an intentional unknown, or combine compatible material. Combining material creates a new coherent candidate with explicit provenance; it is not a pile of the most dramatic events from several branches.

Use explicit states:

- `open`: branches are being explored and none may enter downstream canon;
- `selected`: one branch or composition is being developed but remains revisable;
- `locked`: the author has approved a numbered revision as story canon.

Only the locked branch may enter a long biography, memory, relationship, outline, scene, turn-state, dialogue, storyboard, or video prompt. Give each workbench a stable `character_id` and `package_context_id`. The author-decision record and lock bind both identifiers plus the exact branch, fact-boundary hash, candidate-content hash, and lock revision; changing any of them requires a new decision rather than replaying an old approval. This prevents an approval copied from one character package from authorizing another. Locking the causal branch authorizes expansion; it does not declare the resulting long biography complete. A later unlock or change creates a new revision and makes prior downstream compilations stale. Never overwrite existing author canon or mix branches silently.

The lock declaration must point to an actual author decision in the conversation or project record. The model must not manufacture the decision record because one candidate scores well. A static audit can verify that a declaration is complete and internally consistent; the workflow and forward tests must verify that the author truly chose it.

## Expand the locked path into a deep biography

For a main or important character that must keep driving plot, relationships, and dialogue, `deep` mode defaults to a minimum of **30,000 countable Chinese Han characters** in the full biography body derived from the locked path. An initialized but unclassified role remains `unclassified` until the workflow establishes its story function. The system must not silently downgrade an important character. A project may explicitly choose a lighter tier for a minor or functional role and record that author decision. Meeting the threshold and passing the mechanical audit do not constitute author approval.

The candidate outlines remain compact until the author selects or compatibly composes one, resolves its contradictions, and explicitly locks that route. Only that locked route is expanded by default. If the author explicitly asks for several full alternatives, each route must be separately locked for that experiment and every alternative presented as full must satisfy its own declared depth contract. Every full alternative used downstream also requires separate approval of its exact biography revision and body hash.

The biography is a continuous causal life, not a résumé. Across the character's actual major stages, it should cover relevant ordinary life and turning points; family, education, work, place, class, era, body, money, and institutional constraints; relationship formation and erosion; success, failure, missed chances, shame, debt, secrets, and repair; value formation and revision; anomalous choices; differences between self-narration and events; mistaken memory or self-deception; unresolved residues; and traces visible at story opening.

Not every category must receive equal space, and no invented hardship is required merely to fill a heading. Unknown periods remain labeled unknown when invention is not authorized.

Count only the locked-path biography's original narrative body. Exclude YAML, IDs, scoring tables, source quotations, rejected branches, downstream screenplay dialogue, and duplicated summaries. Repetition, synonymous restatement, random trivia, adjective piles, scenery with no state change, résumé lists, and forced trauma do not satisfy the threshold. Obvious repeated paragraphs or fixed-length Han runs fail the mechanical padding check; semantic restatement and causal thinness still require human review.

Write a long biography stage by stage in a file instead of truncating it into one chat response. Its frontmatter must name the character ID, package context, locked branch, fact-boundary hash, candidate hash, path-lock revision, biography revision, and current status. Mark it `drafting` while incomplete and `ready` only after it passes the mechanical deep contract. The author must then approve that exact character/package identity, branch, fact snapshot, candidate, path-lock revision, biography revision, and body hash; a path lock never grants blanket approval to details introduced during expansion. Any bound change invalidates biography approval and compiled runtime.

Run `scripts/audit_life_paths.py` before downstream compilation. The script checks structure, exact duplicate candidate spines, decision bindings, fact/candidate/biography hashes, countable length, obvious repetition, exact runtime files, and explicit provenance closure. It refuses a formal structured artifact that omits canonical path references, but it cannot judge whether every claim is semantically warranted, whether the life feels artistically true, or whether a human actually made either recorded approval.

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

The compilation ledger separates locked life-path source references from artifact file records. The runtime and every record bind `compiled_for_character_id` and `compiled_for_package_context_id`, then name a type, project-root-contained UTF-8 regular file, exact file SHA-256, canonical `life-path:<branch>/<node>` source closure, fact-boundary hash, candidate hash, path-lock revision, biography revision, and body hash. Per-character structured assets carry the same identity inside `compiled_provenance`. Multi-character scene, turn-state, and beat-map assets use `character_sources[]`; each character workbench audits its own exact entry, while project-level cross-workbench review is still required for the other entries. Known structured artifacts must also contain canonical references in their own data; the current character's record and file reference sets must agree. A compiled relationship ledger must be the exact file declared by the workbench. Its ordinary relationship and shared-memory claim sections receive the same branch and closure scan, while its shared-event registry receives the cross-workbench participant audit. This makes silent file edits, cross-character replay, provenance exemptions, and omitted explicit provenance fail mechanically, while semantic support for each creative claim remains a human review question.

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
