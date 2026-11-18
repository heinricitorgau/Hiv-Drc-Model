# Hiv-Drc-Model — installation and usage

**English** · [繁體中文](USAGE.zh-TW.md) · [← back to the README](../README.md)

How to install the package, drive it from the command line, the Python API and the dashboard, and where everything lives. The results themselves are in [REPORT.md](REPORT.md).

## Contents

- [Installation](#installation)
- [Usage](#usage)
- [Output figures](#output-figures)
- [Project structure](#project-structure)

---

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/heinricitorgau/hiv-drc-model.git
cd hiv-drc-model
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

Or, without installing the package, just the dependencies (this file is a mirror of
pyproject's, kept for deployment targets that install from a requirements file):

```bash
pip install -r requirements.txt
```

For development (adds pytest and ruff):

```bash
pip install -e ".[dev]"
```

For the [interactive dashboard](#interactive-dashboard) (adds streamlit):

```bash
pip install -e ".[app]"
```

Dependencies are only `numpy`, `scipy`, `matplotlib` and `emcee`. Streamlit is needed for
`app.py` alone and is kept in the `app` extra, so importing `hiv_drc` never pulls in a web
framework.

---

## Usage

### Command line

Run everything and write all twelve figures to `figures/`:

```bash
python -m hiv_drc
```

The six stages are `dynamics`, `r0`, `stability`, `sensitivity`, `estimate` and `bayes`.
Individual stages can be selected by name:

```bash
python -m hiv_drc dynamics
```

```bash
python -m hiv_drc r0 stability
```

Generate noisy data and recover the parameters from it:

```bash
python -m hiv_drc estimate --noise 0.05 --starts 8 --data data/synthetic/observations.csv
```

Sample the posterior instead of finding a point estimate:

```bash
python -m hiv_drc bayes --noise 0.05 --mcmc-walkers 16 --mcmc-steps 1000
```

Useful options:

| Flag | Default | Effect |
| --- | --- | --- |
| `--outdir DIR` | `figures` | Where PNGs are written |
| `--years N` | `50` | Time horizon for the dynamics |
| `--samples N` | `1000` | Latin hypercube sample size |
| `--spread F` | `0.25` | Relative half-width of the sampling band |
| `--sweep-points N` | `41` | Points in the bifurcation sweep |
| `--show` | off | Open figures interactively instead of only saving |
| `--no-save` | off | Skip writing PNGs |

Options for the `estimate` stage:

| Flag | Default | Effect |
| --- | --- | --- |
| `--fit PARAM...` | `beta alpha` | Which parameters to recover |
| `--noise F` | `0.05` | Relative measurement noise on the synthetic data |
| `--noise-model M` | `proportional` | `proportional` or `constant` measurement error |
| `--obs-years N` | `30` | Length of the observation window |
| `--obs-points N` | `31` | Number of observations |
| `--seed N` | `20260830` | Seed for the noise and the multi-start draws |
| `--starts N` | `8` | Multi-start restarts for the optimiser |
| `--weights W` | `scale` | Residual weighting: `scale`, `sigma` or `none` |
| `--grid N` | `41` | Resolution of the cost-surface grid |
| `--data PATH` | none | Write the synthetic observations to this CSV |

Options for the `bayes` stage (in addition to `--fit`, `--noise`, `--noise-model`,
`--obs-years`, `--obs-points` and `--seed` above, which it shares with `estimate`):

| Flag | Default | Effect |
| --- | --- | --- |
| `--mcmc-walkers N` | `16` | Ensemble size for the MCMC sampler |
| `--mcmc-steps N` | `1000` | Steps per walker |
| `--mcmc-burn N` | `250` | Steps discarded as burn-in |

At the defaults this evaluates the forward model roughly 16,000 times; expect anywhere from
tens of seconds to a few minutes depending on the machine.

After `pip install -e .` the same thing is available as a console script:

```bash
hiv-drc --samples 2000 --outdir results
```

### As a library

```python
from hiv_drc import DRC_2020, reproduction_number, simulate

result = reproduction_number(DRC_2020)
print(result)                      # R0 = 1.214450 (R1 = 48.543689, ...)

solution = simulate(DRC_2020, t_span=(0.0, 50.0))
print(solution["I1"][-1])          # unaware infectives at t = 50
print(solution.prevalence[-1])     # infected share of the population
```

Parameters are an immutable dataclass, so scenarios are built by copying rather than
mutating:

```python
from hiv_drc import critical_beta, endemic_equilibrium

intervention = DRC_2020.replace(phi=0.09, alpha=0.05, sigma1=0.0125)
print(reproduction_number(intervention).R0)     # 0.7644 — below threshold

print(critical_beta(DRC_2020))                  # 0.123513

equilibrium = endemic_equilibrium(DRC_2020)
print(equilibrium.infected, equilibrium.is_stable)
```

Recovering parameters from data takes three lines:

```python
from hiv_drc import generate_observations, estimate_parameters

observations = generate_observations(noise=0.05, seed=20260830)   # or Observations.from_csv
fit = estimate_parameters(observations, fit=("beta", "alpha"))
print(fit.summary())
```

```
  param        estimate     std err                     95% CI      truth      error   rel err
  beta         0.165803    0.074724   [  0.016333,   0.315274]   0.150000  +0.015803   +10.54%
  alpha        0.037321    0.005075   [  0.027170,   0.047473]   0.035000  +0.002321    +6.63%

  cost = 1.648974e-01   RMSE (millions)   A: 0.004153   T: 0.005151
  R0 at the estimate = 1.342384
  corr(beta, alpha) = +0.1184
```

Sampling the posterior instead takes one more line, and answers a different question: not
"what is the best fit" but "what does the data actually rule out":

```python
from hiv_drc import run_mcmc

posterior = run_mcmc(observations, fit=("beta", "alpha"), n_walkers=16, n_steps=600, burn=150)
print(posterior.summary())
```

```
  param            median         std                     95% CI   R-hat      ESS
  beta           0.145171    0.021042   [  0.095625,   0.175486]   1.162      n/a   truth 0.150000  (-3.22%)
  alpha          0.034575    0.002350   [  0.030047,   0.039226]   1.146      n/a   truth 0.035000  (-1.22%)
  eta_A          0.046998    0.006543   [  0.037134,   0.062503]   1.109      n/a
  eta_T          0.056340    0.007368   [  0.044648,   0.074339]   1.157      n/a

  acceptance fraction 0.587   16 walkers x 600 steps (150 discarded as burn-in)
  R0 at the posterior median = 1.175355
```

`eta_A` and `eta_T` are not epidemiological parameters — they are each series' own inferred
relative measurement-noise level, fitted jointly rather than assumed.

### Interactive dashboard

`app.py` puts the model behind a browser UI, for exploring scenarios without writing code. A
deployed copy runs at [hiv-drc-model-6h4eabztaookr4gj4steeg.streamlit.app](https://hiv-drc-model-6h4eabztaookr4gj4steeg.streamlit.app); to run it locally:

```bash
pip install -e ".[app]"
streamlit run app.py
```

Three tabs. **Dynamics** moves $\beta$, $\alpha$ and $\phi$ on sliders and recomputes $R_0$
from the closed form on every change, alongside its $R_1/R_2/R_3$ decomposition and the
trajectory of $I_1$, $I_2$, $A$ and $T$. **The inverse problem** generates noisy $A$ and $T$
from the current parameters, recovers them with `estimate_parameters`, and shows the Wald
intervals next to the truth the estimator was never given. **Real data and the scale-up**
drops synthetic data entirely: it loads the UNAIDS series with `load_worldbank`, builds the
initial state from the first year's PLHIV, ART coverage and population rather than from
Table 2, and draws the published `plhiv` and `art_coverage` against the model.

That third tab exists to be toggled. With constant rates the model reaches 34% ART coverage
by 2024 against the published 71%, because a constant $\alpha$ cannot produce an S-curve.
Switching on the logistic scale-up and leaving the sliders at their defaults lands coverage
at 70.9% — and PLHIV at 0.173 million against the published 0.540. Matching one series to
within a tenth of a point while missing the other threefold is the whole lesson of
[Meeting real data](REPORT.md#meeting-real-data), reachable from a checkbox.

The dashboard computes nothing itself: every number on screen comes from `DRC_2020`,
`simulate`, `reproduction_number`, `generate_observations` and `estimate_parameters`. It is a
view, not a second implementation, so it cannot drift from the tested one.

The figures are labelled in Chinese where a CJK font is installed and in English where
one is not — matplotlib does not fail on a missing glyph, it draws a blank box, so on a bare
Linux container every label would silently become one.

$S$ and $R$ are hidden by default rather than drawn on a secondary axis — $S$ is about 88
million and $A$ about 0.05 million, and two y-scales on one plot make the slopes
incomparable. A checkbox adds them as a second panel sharing the time axis.

The parameter selector is worth using on more than its default. At the sliders' baseline and
5% noise, fitting $\beta$ and $\alpha$ recovers them to +10.5% and +6.6% at a cost of 0.1649.
Adding $\phi$ to the same fit moves the cost to 0.1642 — nothing — while $\beta$ goes to
$1.00 \pm 21.5$ and $\phi$ to its upper bound at $1.00 \pm 23.7$, both intervals straddling
zero. The residual barely noticed; the parameters stopped meaning anything. That is [the same
non-identifiability](REPORT.md#but-the-nine-parameter-model-is-not-identified) the scale-up study runs
into, reachable from a dropdown, and it is why the correlation and the standard errors sit
beside the estimates rather than the point values alone.

---

## Output figures

All twelve are written to `figures/` (git-ignored — they are regenerated by one command).

| File | Contents |
| --- | --- |
| `01_population_dynamics.png` | Four panels: uninfected compartments ($S$, $R$), infected compartments ($I_1$, $I_2$, $A$, $T$), total population against the carrying capacity, and prevalence. $S$ and $R$ are drawn apart from the infected classes because they differ by three orders of magnitude. |
| `02_scenarios.png` | Total infected population under the baseline, a raised contact rate ($\beta = 0.2$), and the paper's enhanced-intervention scenario, each annotated with its $R_0$. |
| `03_r0_surface.png` | $R_0$ over the $(\beta, \sigma_1)$ plane. Left: filled contour with the $R_0 = 1$ threshold and the DRC operating point. Right: the same surface in 3-D cut by a translucent $R_0 = 1$ plane, the intersection drawn in black. |
| `04_bifurcation.png` | Endemic infected level against $R_0$, and the dominant Jacobian eigenvalue at both the disease-free equilibrium and the attractor. This is the picture of a forward transcritical bifurcation. |
| `05_local_sensitivity.png` | Tornado plot of the paper's normalised sensitivity indices. |
| `06_global_sensitivity.png` | Latin-hypercube/PRCC screen: PRCC on $R_0$, global versus local comparison, PRCC on the 50-year infected total, and the sampled $R_0$ distribution. |
| `07_parameter_fit.png` | The inverse problem: noisy observations of $A$ and $T$ as scatter, the recovered model as a curve, the generating trajectory dashed underneath, the residuals, and each estimate against its true value with 95% intervals. |
| `08_cost_surface.png` | The objective over the $(\beta, \alpha)$ plane on a log colour scale, with the true parameters, the least-squares estimate and the 95% confidence box marked. The shape of the basin is the identifiability diagnostic. |
| `09_posterior.png` | Pairwise marginal posteriors over $\beta$, $\alpha$ and the two fitted noise levels — the MCMC "corner plot". A round cloud means a pair is separately identified; an elongated one means only some combination of them is. |
| `10_trace.png` | Per-parameter walker traces: every walker's path over the kept steps, with its split-$\hat R$ annotated. A fuzzy horizontal band is a well-mixed chain; a visibly separated walker is not. |
| `11_posterior_predictive.png` | Observed $A$ and $T$ against the posterior *predictive* band (model plus each draw's own fitted noise), with the fraction of points actually inside the band reported per panel. |
| `12_bayes_vs_frequentist.png` | The least-squares Wald interval and the MCMC credible interval for the same fit, drawn on the same axis. Where they disagree, the quadratic approximation behind the Wald interval was already starting to break down. |

---

## Project structure

```
hiv-drc-model/
├── src/hiv_drc/
│   ├── __init__.py          Public API
│   ├── __main__.py          Enables `python -m hiv_drc`
│   ├── parameters.py        Table 2 and Table 3 — the configuration block
│   ├── model.py             The ODE right-hand side and its Jacobian
│   ├── simulation.py        solve_ivp wrapper and the Solution type
│   ├── reproduction.py      R0: closed form and next-generation matrices
│   ├── equilibria.py        Disease-free and endemic equilibria, stability
│   ├── sensitivity.py       Local indices, Latin hypercube sampling, PRCC
│   ├── analysis.py          Parameter sweeps: R0 grid, bifurcation, threshold
│   ├── observables.py       What surveillance reports, as functions of the state
│   ├── priors.py            Informative priors and the contraction diagnostic
│   ├── realdata.py          Loading UNAIDS/World Bank series; initial state from data
│   ├── synthetic.py         Mock data: forward model + Gaussian measurement error
│   ├── estimation.py        The inverse problem: bounded nonlinear least squares
│   ├── bayesian.py          The same inverse problem, solved by MCMC (emcee)
│   ├── plotting.py          Figures (no computation lives here)
│   └── cli.py               Command-line interface
├── tests/                   226 tests (242 with doctests)
│   ├── conftest.py          Shared fixtures
│   ├── test_model.py        ODE right-hand side and Jacobian
│   ├── test_simulation.py   Integration, conservation, solver agreement
│   ├── test_reproduction.py R0 closed form against the next-generation matrix
│   ├── test_equilibria.py   Equilibria and the stability theorem
│   ├── test_sensitivity.py  Local indices and PRCC
│   ├── test_observables.py  Operators, checked against identities between them
│   ├── test_realdata.py     Units, gaps, and the Table 2 discrepancy
│   ├── test_scaleup.py      Time-varying rates, and the structural ceiling
│   ├── test_priors.py       Densities, and contraction on cases with known answers
│   ├── test_synthetic.py    The data generator
│   ├── test_estimation.py   Recovery, bounds, uncertainty, identifiability
│   ├── test_bayesian.py     Priors, likelihood, split-R-hat, MCMC recovery
│   └── test_app.py          The dashboard, driven through Streamlit's AppTest
├── notebooks/
│   ├── 01_inverse_problem.ipynb       Narrated walkthrough of the estimation pipeline
│   └── 02_bayesian_uncertainty.ipynb  The same fit by MCMC, and where the two disagree
├── scripts/
│   ├── coverage_study.py    One-off measurement behind the Bayesian coverage table
│   ├── observability_study.py  Which observation sets identify the rates
│   ├── fetch_worldbank.py   Downloads the DRC indicators (the only network access)
│   ├── realdata_fit.py      Fitting the real series, window by window
│   ├── scaleup_fit.py       Constant vs alpha(t) vs alpha(t)+lambda(t)
│   ├── prior_contraction.py  Whether informative priors earned their intervals
│   └── readme_figures.py    Regenerates the images the README embeds (docs/img/)
├── data/
│   ├── README.md            Provenance and column definitions
│   ├── real/                UNAIDS/World Bank snapshot for the DRC
│   └── synthetic/           Generated observations (`--data` writes here)
├── docs/
│   ├── REPORT.md            The full write-up of the results
│   ├── USAGE.md             This file: installation, CLI, API, dashboard
│   ├── *.zh-TW.md           Traditional Chinese versions
│   └── img/                 The figures the README shows (committed)
├── figures/                 Generated output (git-ignored)
├── assets/                  README banner
├── app.py                   Streamlit dashboard — presentation only, no computation
├── pyproject.toml
├── requirements.txt        Deploy mirror of pyproject's runtime dependencies
├── CITATION.cff             Citation metadata (GitHub's "Cite this repository")
├── README.md                Overview and headline results (English)
└── README.zh-TW.md          Traditional Chinese version
```

The layering is deliberate: `plotting.py` never computes and the analysis modules never
plot, so a figure can be restyled without repeating a twenty-thousand-year integration, and
every analysis module stays importable on a machine with no display.

The same separation runs through the estimation layer. `synthetic.py` knows how data are made
and nothing about fitting; `estimation.py` knows how to fit and reaches for the generating
parameters only to *score* a result, never to produce one. That boundary is what makes a
recovery test meaningful — and it is why `Observations.from_csv` returns data with
`truth=None`, so real data and synthetic data take exactly the same path through the fitter.

`bayesian.py` sits beside `estimation.py` rather than on top of it: the two modules share
`synthetic.Observations` and `estimation.PARAMETER_BOUNDS`, and `run_mcmc` calls
`estimate_parameters` once to centre its walkers, but neither module imports the other's
result type. Either can be deleted without breaking the other.
