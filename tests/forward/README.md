# Forward evaluation

These cases test behavior, not wording. Run each case in a fresh task with only the installed skill, the request, and the supplied input. Do not show the generating agent the expected answer, suspected bug, or scoring rubric.

Recommended protocol:

1. Run each case three times with the same model and reasoning setting.
2. Require all machine-checkable hard invariants to pass in all three runs.
3. Give fidelity, naturalness, subtext, and shot motivation to a blinded reviewer using a 0–2 scale.
4. Keep generated artifacts outside the repository or under ignored `test-results/`.
5. Compare skill-on and skill-off outputs only when model, settings, and source material are identical.
6. Never convert these cases into an adoption-rate claim; production adoption requires representative human decisions.

Cases live in `cases.json`. They intentionally include non-trigger and restraint tests, because a useful skill must know when not to expand the task.
