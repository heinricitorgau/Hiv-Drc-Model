## What this changes

<!-- What and why. Link the issue it addresses, e.g. "Closes #12". -->

## What was measured

<!-- Numbers before and after, if any changed. Include negative results and what you ruled out. -->

## Checklist

- [ ] `ruff check src tests` passes
- [ ] `pytest` passes (docstring examples included)
- [ ] New tests check against an independent derivation or a mathematical property, not the code itself
- [ ] For a bug fix: the new test was observed failing against the defect
- [ ] README claims updated if a measured number changed
- [ ] Layering kept: plotting does not compute, analysis does not plot, `app.py` computes nothing
- [ ] A new dependency is added to both `pyproject.toml` and `requirements.txt`
