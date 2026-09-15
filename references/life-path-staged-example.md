# Staged life-path example

This abbreviated fictional example shows the contract between stages. It is not a substitute for the deep biography: a real `deep` run must keep an actual author-approved biography file with sufficient causal and scene-useful coverage and pass applicable audits.

## 1. Sparse material becomes an evidence boundary

Present material: a character returns to a long-closed workshop carrying an old key; they correct one date on a notice, then add that they may remember it incorrectly. Another character says the departure years ago was voluntary. The returning character says there was no real choice.

The workbench does not flatten those statements:

| ID | Epistemic class | Content | Stable source ref |
|---|---|---|---|
| `fact-01` | author-locked fact | The character returns with the key before the story opens | `outline:v3/beat-01` |
| `trace-01` | observable trace | They know the disputed date, then qualify their certainty | `draft:v5/scene-02/action-04` |
| `testimony-01` | testimony | The other character calls the departure voluntary | `draft:v5/scene-02/line-07` |
| `testimony-02` | self-report | The returning character denies having a real choice | `draft:v5/scene-02/line-09` |
| `conflict-01` | conflict | Both accounts cannot be fully literal at once | `analysis:v1/conflict-01` |
| `unknown-01` | unknown | Why the key was kept and what ended the relationship | `author-note:v2/open-03` |

Each record retains its source reference. The current endpoint and label do not decide temperament.

## 2. Three root candidates differ in causal route

Candidate A treats the departure as an accumulated material constraint. Repeated small obligations made staying impossible; leaving reduced immediate harm but taught the character to calculate exit costs before emotional promises. Its present trace is early attention to who will absorb practical loss.

Candidate B treats the departure as a failed act of protection. The character hid a worsening problem to preserve another person's stability; the concealment delayed help, created a relational debt, and taught a strategy of private repair before public explanation. Its present trace is attention to what disclosure would do to a particular person.

Candidate C treats the departure as an active boundary that was later misread as abandonment. Leaving protected one value but silence let others write the motive. The feedback changed the character's strategy from total withdrawal to limited, evidence-backed clarification. Its present trace is attention to who controls the public account.

The candidates share the locked endpoint but not the same event sequence, interpretation, choice, cost, feedback, strategy update, relationship consequence, or current first impulse. Their support, conflict, unknown, feasibility, theme, arc, relationship, and present-response fields reference the evidence IDs above.

One abbreviated feasibility record therefore looks like this:

```yaml
feasibility:
  supports: [fact-01, trace-01, testimony-02]
  conflicts: [conflict-01]
  unknowns: [unknown-01]
  real_world_feasibility: the timing and available choices do not contradict the locked outline
```

## 3. The author composes and locks

Suppose the author rejects A, selects B's failed protection as the main route, and asks to add C's later lesson about silence. The system creates a new composite candidate rather than silently pasting prose. It identifies the source nodes, resolves their timing and motive seam, reruns factual compatibility, and presents the composite for another decision.

Only after the author explicitly approves that composite does the workbench record the path lock, its revision, the author-decision source, `locked_fact_boundary_sha256`, and `locked_candidate_sha256`. The decision record binds all four values. Editing the facts or candidate later invalidates that lock instead of reusing the old approval.

## 4. The locked route becomes a separately approved biography

The long file begins with provenance rather than pretending that the path lock approved every detail the model later invented:

```yaml
---
character_id: character-a
package_context_id: package-character-a
life_path_branch_id: path-composite-01
life_path_lock_revision: 1
fact_boundary_sha256: <actual locked fact-boundary hash>
locked_candidate_sha256: <actual locked candidate hash>
biography_revision: 1
biography_status: ready
---
```

The omitted body covers the actual life stages, ordinary routines, constraints, relationships, choices, costs, feedback, revisions, contradictions, mistaken memories, and opening residues. Its depth is judged by usable causal coverage rather than a character quota. After review, the author separately approves the exact biography revision and body hash. Changing the prose invalidates that approval.

## 5. Compilation retains causes without carrying the whole book

The compile task produces actual files, for example:

- an expectation that unannounced protection can become control;
- a relationship strategy of repairing privately before accepting public framing;
- a memory whose objective event, remembered event, and current belief remain separate;
- a debt to the person who bore the consequence of the old concealment;
- a first impulse to stop the key from being publicly displayed;
- canonical `life-path:path-composite-01/<node>` references for every derived claim.

The compile ledger records the fact-boundary hash, candidate hash, path-lock revision, approved biography revision and body hash, and exact artifact records. Every record carries a project-root-relative path, artifact type, file SHA-256, and canonical source closure; known structured files contain the same refs internally. A fresh scene task receives these compiled assets, not the long biography or rejected candidates.

## 6. The outline is reviewed before a formal scene

If the outline requires the character to deliver a complete public confession immediately, the runtime exposes a conflict: the locked route supports repair, but its learned order is private protection, evidence, then public framing. The system presents author choices and costs—for example, add pressure that makes privacy impossible, earn a change in strategy, preserve a deliberate contradiction with consequences, or revise the beat. It does not silently force the character to obey the plot.

## 7. The scene surfaces only the current tactic

At the workshop, the other character reaches to hang the old key beside the notice. The returning character covers the key with one hand, slides the disputed notice across with the other, and waits. The other person's hand stops. No one explains the departure, the protected person, or the years of debt. If a line is still needed to change the next move, it can remain as small as “先看这个。”

The private model is long; the playable surface is an action, changed distance, stopped hand, silence, and one strategically necessary line. That visible choice is useful only because its source can be traced through the approved biography and locked nodes.
