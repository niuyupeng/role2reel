# Forward evaluation

The files in this directory specify behavioral evaluations. The repository unit test validates only the `cases.json` schema and coverage; it does **not** call a model, score generated work, or turn a case specification into a behavioral pass.

## Evidence status

- Results recorded for the v0.1 cases are historical and are summarized in `EVALS.md`.
- FT-01 through FT-13 have informal development cold runs and post-fix case-level regressions summarized in `EVALS.md`; they do not satisfy this formal protocol because exact model/run metadata and blinded human review were not recorded.
- FT-14 has not received an actual-artifact staged deep run or blinded human review.
- FT-15–FT-17 cover author-facing 命线反演, two-stage cognition/expression retrieval, and a light path-to-behavior scene. Any development cold runs remain informal until exact run metadata and blinded human review are recorded.
- FT-18 specifies the complete fused pipeline and must remain pending without real source material, an actual author path decision, a separately approved deep biography, isolated compilation/generation tasks, and human review.
- FT-19–FT-22 specify extension, protected edit, two-source transition, and multi-panel video tasks. Schema or linter success cannot establish provider support or rendered quality.
- FT-23–FT-25 specify bounded dialogue reintegration, story-capacity tradeoffs, and stale handoff rejection. They remain pending behavioral execution and human review; repository tests check their specifications only.
- Adding a case, passing its JSON contract test, or passing a deterministic linter is not evidence that generation behavior improved.

## Cold-run protocol

For each behavioral run:

1. Start a fresh task with only the installed skill version, the case request, and its supplied input.
2. Record the exact skill commit or archive hash, model and version, reasoning setting, date, and run identifier.
3. Do not show the generating agent the expected answer, suspected failure, hard invariants, or human rubric.
4. Run each case at least three times under the same recorded settings. Keep outputs and per-invariant decisions outside the repository or under ignored `test-results/`.
5. Require every applicable hard invariant to pass; report failures individually instead of averaging them away.
6. Randomize anonymized outputs before human review. Reviewers must not know which workflow produced an output.
7. Keep source fidelity, privacy, author-lock integrity, knowledge boundaries, and branch isolation as hard gates rather than taste scores.
8. Mark unavailable routing observations as untested. A static inspection cannot establish automatic skill invocation.

## Three blinded comparison arms

Use representative material and compare at least these three arms with the same source, target deliverable, model family, model version, and sampling settings:

| Arm | Workflow |
|---|---|
| A — baseline | Pinned unmodified Role2Reel v0.1 workflow |
| B — biography length only | The same pinned v0.1 workflow plus an unstructured longer biography, without candidate comparison, author lock, provenance, or runtime compilation |
| C — selected life path | Multiple causal candidates, explicit author path lock, a separately approved exact biography revision and body hash when deep mode applies, then compiled runtime, knowledge boundaries, and turn-state simulation |

Record material differences in context length and human preparation time. Do not quietly give one arm extra canon, source evidence, or revision opportunities.

## Three metric families

### 1. Adoption and editing burden

- direct adoption;
- adoption after light edit;
- rejection;
- edit magnitude and categorized edit reasons;
- whole-scene no-rewrite rate.

### 2. Causal individuality and integrity

- speaker identification with names and workflow labels hidden;
- character consistency and scene-consequence scores;
- path-swap sensitivity, occupational-context stability, and causal-node ablation;
- rejected or unlocked branch leakage;
- knowledge-boundary and shared-context errors;
- explanatory lines removed without losing strategy or state change.

### 3. Performance and dramatic usefulness

- actor read-aloud fluency;
- clarity of pursuit, concealment, restraint, and tactical change;
- subtext and relationship movement;
- whether action, gaze, space, pause, or silence can replace unnecessary dialogue;
- blinded reviewer preference with a recorded repair reason, not an unsupported “more human” label.

The previously mentioned approximately 20% directly usable rate is only an informal, small-sample baseline observation. It is not a v0.2 result, target, guaranteed floor, or promised improvement. Before comparing against it, define the same unit of analysis and adoption rule, use representative material and blinded reviewers, and report the actual denominator and uncertainty.

Cases intentionally include non-trigger, restraint, counterfactual, branch-isolation, depth-contract, and author-control checks. Never convert case completion or deterministic test coverage into an adoption-rate claim.

## Staged deep execution

FT-09 through FT-12 are explicitly `light` unit fixtures. Informal development regressions can check their narrow behavior, but they cannot demonstrate biography-to-runtime causality or replace a formally recorded run. FT-14 defines the staged deep protocol only: it becomes evidence after real audited artifacts, separate author approval of the exact biography revision and body hash, completed staged runs, and recorded reviews exist. Its execution compiles in one fresh task, generates the scene in another task that never sees the long biography or rejected branches, and then runs controlled swaps, ablation, dialogue deletion, and blinded actor review.

Follow [staged-deep-protocol.md](staged-deep-protocol.md) and save a populated `assets/templates/staged-life-path-eval.yaml`. Keep `behavior_pass: false` until every real artifact, run, traceability decision, and human review exists. Before changing it to true, run `scripts/audit_staged_eval.py`; a clean record audit is necessary but cannot prove that the declared runs or reviews actually happened.
