# Contributing to Role2Reel

Contributions should make behavior more truthful, controllable, or testable without turning one preference into a universal rule.

## Best contributions

- a minimal source example and a model output that failed;
- the human-approved final version;
- whether the candidate was adopted, lightly edited, heavily edited, or rejected;
- a precise reason code such as knowledge leak, meaning drift, exposition, generic voice, broken causality, empty shot duty, timeline error, or asset leakage;
- a new forward test that fails before the change and passes after it.

Do not submit confidential scripts, personal character data, unlicensed training material, or private production assets.

## Development

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_repo.py
python -m unittest discover -s tests -v
python scripts/package_skill.py
```

When changing behavior:

1. Keep `SKILL.md` short enough to route cheaply.
2. Put conditional detail in the relevant reference rather than loading it for every request.
3. Add deterministic scripts only when they prevent repeated fragile work.
4. Separate hard invariants from taste judgments.
5. Preserve user scope and authorization boundaries.
6. Update `THIRD_PARTY_NOTICES.md` when third-party material is incorporated or adapted.

## Pull requests

Explain the observed failure, the narrow mechanism changed, the test evidence, and any trade-off. Avoid acceptance-rate claims without blinded comparable evaluation.
