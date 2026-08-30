# Quality gates and calibration

Automated checks catch omissions and contradictions. They do not prove that dialogue is human, acting is truthful, or a shot is good. Combine linting with blinded human comparison.

## Hard gates

Treat these as errors:

- a material source claim is fabricated, reassigned, or made more certain without authorization;
- a character uses information outside their knowledge boundary;
- an effect precedes its perceptible cause;
- timeline segments overlap or reverse; when an exact duration is required, the timeline also fails if it has an unexplained gap, does not start at 0, or does not end at the requested duration;
- a shot lacks a discernible duty or contradicts locked continuity;
- a reference asset has no defined role or imports excluded identity, wardrobe, setting, or audio;
- provider-specific constraints are stated as verified when they were not checked.

## Warning gates

Review rather than automatically reject:

- long or syntactically complete dialogue under high emotion;
- repeated explanation of visible facts;
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
- baseline plus longer character biography;
- character runtime plus knowledge boundaries and turn-state simulation.

Blind reviewers to the method. Record:

- direct adoption;
- adoption after light edit;
- rejection;
- edit distance or categorized edit reasons;
- whole-scene no-rewrite rate;
- removed exposition count;
- speaker-identification accuracy with names hidden;
- actor read-aloud fluency;
- character consistency and scene consequence scores.

Do not promise an adoption-rate improvement before collecting comparable human decisions. Save individual decisions with `assets/templates/calibration-record.yaml`, including the human final version and reason codes. Prefer narrow changes supported by repeated evidence over adding a universal rule for each rejected line.

## Included linters

- `python scripts/audit_dialogue.py <file>` flags likely exposition, generic AI phrasing, duplicates, and unusually long dialogue lines.
- `python scripts/audit_storyboard.py <csv-json-or-yaml>` checks required fields, IDs, finite numeric time ranges, ordering, gaps, and overlaps. Add `--expected-duration <seconds>` for an exact-duration deliverable; that mode also requires continuous coverage from 0 through the requested endpoint.
- `python scripts/validate_repo.py` checks skill structure, local links, metadata, scripts, and unfinished placeholders.

Warnings are prompts for review, not automatic rewrites.
