# Contributing

Thanks for taking an interest. This repository reproduces Mbayi, Mpompi & Munyakazi,
*Tamkang Journal of Mathematics* **57**(2), 149–169 (2026), and then pushes on it: parameter
recovery, identifiability, real World Bank data, and Bayesian uncertainty. Contributions of every
size are welcome — a typo, a failing case, a new observation operator, or a result that
contradicts one in the README.

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

- **Read the relevant README section.** The README is the write-up of the results, including the
  negative ones. If your change touches something it describes, the claim and the code have to
  stay in agreement.
- **For anything larger than a small fix, open an issue first** so we can agree on the approach
  before you spend time on it.
- **Security problems do not go in public issues** — see [SECURITY.md](SECURITY.md).

## Setting up

```bash
git clone https://github.com/heinricitorgau/hiv-drc-model.git
cd hiv-drc-model
pip install -e ".[dev]"
```

Python 3.10–3.12 is tested on Linux, Windows and macOS. `emcee` is a hard dependency even for
pure ODE work, because `hiv_drc/__init__` imports the Bayesian module.

Dependencies live in `pyproject.toml`. `requirements.txt` mirrors it for deployment targets; if
you add a dependency, add it in both.

## Checks that must pass

These are exactly what CI runs:

```bash
ruff check src tests
pytest
python -m hiv_drc --samples 100 --sweep-points 9 --starts 2 --grid 11 \
  --mcmc-walkers 10 --mcmc-steps 60 --mcmc-burn 15 --outdir /tmp/figures
```

The full suite takes a few minutes: `--doctest-modules` is on, so every docstring example in
`src/` is executed, and the Bayesian tests run real (small) MCMC chains.

## How the code is organised

The layering is deliberate; please keep it:

- `parameters.py` is the configuration block. `Parameters` is frozen — build variants with
  `.replace(...)`.
- `plotting.py` never computes, and the analysis modules never plot.
- `synthetic.py` knows how data are made; `estimation.py` knows how to fit and only uses the
  generating parameters to *score* a result, never to produce one.
- `bayesian.py` sits beside `estimation.py`, not on top of it.
- `app.py` is presentation only — it calls the public API and computes nothing.

A few invariants that are easy to break by accident:

- `rhs` must stay analytic (no `abs`, `max` or branching on the state); the Jacobian uses
  complex-step differentiation and silently degrades otherwise.
- With a time-varying rate configured, `reproduction_number()` and the equilibrium solvers
  **raise** on purpose. Do not "fix" that by returning a number.
- Wide intervals, infinite standard errors and near-±1 correlations are reported findings about
  non-identifiability. Do not narrow bounds or drop parameters to make output tidier.

## Writing tests

- **No test compares the code to itself.** Check against an independent derivation (a closed
  form, a finite-difference reference, a problem with a known answer) or a property that must
  hold mathematically.
- **For a bug fix, show the new test fails against the defect** before the fix, and say so in the
  pull request.
- Docstring examples are tests. Keep them correct.

## Commits and pull requests

- Commit messages here are narrative: say what changed, what you measured, and what you ruled
  out — negative results included. A one-line summary is rarely enough.
- If a measured number changes, update the README claim that reports it in the same pull request.
- Keep a pull request to one concern. Fill in the pull request template.

## Licence

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
