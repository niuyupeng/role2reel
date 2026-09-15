# Episode calibration without answer leakage

Use finished episodes to diagnose transferable craft weaknesses, not to require a
model to guess the author's one possible future plot. This updates a workflow or
skill; it is not model-weight training. Read [quality-gates.md](quality-gates.md)
and [story-character-roundtrip.md](story-character-roundtrip.md) alongside this route.

## Two different tasks

- **Next-episode prediction:** disclose only approved canon through episode N and
  the allowed series brief. Withhold episode N+1, future biographies containing
  spoilers, future outlines, critiques, summaries, filenames revealing plot, and
  retrieval indexes containing those facts.
- **Outline-to-script realization:** the target episode's author-approved outline
  is intentionally supplied; withhold its finished script. Do not report this as
  blind next-episode prediction.

The first episode and canonical setup come from the author. If they are missing,
request them; do not create a substitute and call it an evaluation of the series.
Use only confirmed episode versions. Do not infer finality from modification time.

## Bounded improvement loop

1. Register source files, episode order, revisions, allowed input, target reference,
   task type, current skill snapshot, and run settings. Split development material
   from held-out episodes and a separate story/project before tuning. If material
   is insufficient, label the limitation; do not manufacture a split or score.
2. Freeze the exact generation packet. Run in a fresh context seeing that packet
   only. A filesystem folder is not an access-control sandbox: the caller must
   enforce the context boundary. If this agent has already read the answer, it
   cannot conduct a clean blind generation for that case.
3. Save the output, exact model/version/settings and input binding before revealing
   the reference. The helper below does not invoke models, enforce their isolation,
   prove who generated a file, or authenticate human reviews.
4. Compare cause, motivation, knowledge, setup/payoff, capacity, emotional rhythm,
   and speakability. Separate hard canon errors, missing supplied requirements,
   weak realization, and legitimate alternative choices. Text difference or an
   unguessed twist is not automatically a quality failure.
5. Propose the smallest applicable rule change with evidence and scope. Do not
   copy the reference's exact plot, catchphrases, or house style into universal
   instructions. Each revision round has one named diagnostic focus; rerun prior
   failures and held-out material before accepting the change.
6. Stop at the recorded round budget or when new runs no longer support improvement.
   Record human decisions and contrary evidence. Keep held-out results withheld
   from development; once used to tune a rule, that case is no longer held out.

Before a long story expands into scenes, use a provisional framework as an
intermediate checkpoint, not the final deliverable when a complete script was requested.
Pause for the author only for a consequential missing choice or requested approval.
Let the framework pose character-history questions;
do not invent an inevitable biography merely to force a desired beat. Apply the
existing author path-lock and biography-approval gates to any new character canon.

## Local helper

`scripts/episode_eval.py` builds a generation packet, freezes a supplied candidate,
and creates a reviewer comparison. Its manifest is
[episode-eval.json](../assets/templates/episode-eval.json). Paths are relative to the
manifest directory; only existing UTF-8 text files beneath it are accepted.

```text
python scripts/episode_eval.py prepare manifest.json new-run-directory
python scripts/episode_eval.py seal new-run-directory candidate.md --model recorded-model --settings recorded-settings
python scripts/episode_eval.py review new-run-directory
```

Give the generator only `generation-input.json`, never `private-state.json` or the
reference. A new run directory is mandatory. Review refuses changed inputs,
reference, or candidate. Review output is a diagnostic draft with human verdict
pending, not a pass certificate. Manual packets are useful when no approved model
API is available; do not claim an external backend ran.
