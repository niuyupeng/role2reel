# Role2Reel v0.1.0 validation report

Date: 2026-08-30

This report documents pre-release smoke tests. It is not evidence of a production adoption-rate improvement.

## Deterministic validation

| Check | Result |
|---|---|
| Skill Creator `quick_validate.py` | Pass |
| Role2Reel repository validator | Pass |
| Python unit tests | 25 discovered; 24 pass and 1 symlink-capability test skipped on local Windows |
| Unit tests on local Python 3.9 and bundled Codex Python | Pass on both |
| YAML syntax parse | 18/18 files parse |
| SVG XML parse | Pass |
| Release ZIP integrity | 57/57 allowlisted files readable; no corrupt member |

The test suite covers non-overwriting project initialization, Unicode and Windows-safe IDs, cross-run slug collisions, graph-linked scene participants, Fountain cue syntax, finite and exact storyboard timelines, canonical JSON/YAML aliases, malformed YAML, repository-path edge cases, forward-case schema, and allowlist-only release packaging. The local Windows account cannot create symbolic links, so that one capability test is skipped there; the same test is designed to execute on Linux CI.

## Independent forward tests

Generation agents received only the skill path, realistic request, and minimum source material. They did not receive the expected answer, suspected failure, or scoring rubric. Outputs were reviewed against the hard invariants recorded in `tests/forward/cases.json`.

| Case | Cold runs | Hard-invariant result |
|---|---:|---|
| FT-01 — transcript humanization and uncertainty | 3 | 3/3 pass |
| FT-02 — subtext and private knowledge boundaries | 3 | 3/3 pass |
| FT-03 — 28-second state-change storyboard | 3 post-fix | 3/3 pass |
| FT-04 — multimodal reference-asset isolation | 3 | 3/3 pass |
| FT-06 — typo-only scope restraint | 3 | 3/3 pass |
| FT-07 — fixed-camera one-take constraint | 3 | 3/3 pass |

FT-05, the generic property-notice non-trigger case, received a static routing review only. It is not counted as a behavioral pass because the available subagent harness could not observe automatic skill selection.

## Failure found and corrected

An exploratory FT-03 output split the daughter's stopped hand and the unchanged final hold into two adjacent shots. The second shot added no reveal, spatial relation, sound source, state change, or new audience task. That output also used the same number of shots as spoken units, failing the anti-mechanical-splitting invariant.

The storyboard guidance was narrowed to require merging adjacent reaction and ending-state shots when one continuous view can perform both duties. Three fresh post-fix runs produced four or five shots, covered exactly 0–28 seconds without gaps or overlaps, included silent visual storytelling, added no dialogue or marketing material, and kept the final spoken cue and physical reaction in causal order.

## What these results do not prove

- They do not establish that every output will feel human or cinematic.
- They do not measure adoption by script supervisors, writers, directors, actors, or editors.
- They do not compare Role2Reel against a baseline under blinded production conditions.
- They do not validate current limits or syntax for any changing video model.
- Human taste dimensions were reviewed during development but not scored by an independent blinded panel.

Production claims require representative source material, recorded human final edits, blinded method comparison, and the calibration protocol in `references/quality-gates.md`.
