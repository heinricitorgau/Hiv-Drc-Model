"""Regenerate the images embedded in README.md and README.zh-TW.md.

The full set of twelve figures goes to ``figures/`` (git-ignored) via
``python -m hiv_drc``.  The README shows only a handful of them, and those
have to be committed or GitHub has nothing to render, so this script writes
exactly that handful into ``docs/img/``:

* three figures straight from the CLI stages (``stability``, ``estimate``,
  ``bayes``), saved under stable names;
* one figure the CLI does not draw: the published model against the real
  UNAIDS/World Bank series, with constant rates and with the logistic
  scale-up at the dashboard's default settings.  It is the picture of the
  "Meeting real data" section, and the numbers it prints are the ones the
  report quotes for the dashboard's third tab.

Run from the repository root::

    python scripts/readme_figures.py

Takes about half a minute.  Re-run it whenever a figure the README shows
changes, and commit the PNGs it writes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

sys.path.insert(0, "src")

from hiv_drc import DRC_2020, simulate  # noqa: E402
from hiv_drc.observables import apply  # noqa: E402
from hiv_drc.realdata import initial_state_from_data, load_worldbank  # noqa: E402

OUT = Path("docs/img")

#: CLI figure -> name it is committed under.
FROM_CLI = {
    "04_bifurcation.png": "bifurcation.png",
    "07_parameter_fit.png": "parameter_fit.png",
    "09_posterior.png": "posterior.png",
}

#: The dashboard's default scale-up (app.py, tab 3), counted from FIRST_YEAR.
SCALEUP = dict(
    alpha_ceiling=0.2, alpha_midpoint=10.0, alpha_rate=0.4,
    lam_ceiling=0.3, lam_midpoint=8.0, lam_rate=0.4,
)
FIRST_YEAR = 2005


def copy_cli_figures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, "-m", "hiv_drc", "stability", "estimate", "bayes",
             "--outdir", tmp],
            check=True,
        )
        for source, target in FROM_CLI.items():
            shutil.copyfile(Path(tmp) / source, OUT / target)
            print(f"  {OUT / target}")


def draw_real_data() -> None:
    observations, context = load_worldbank(first_year=FIRST_YEAR)
    years = np.asarray(context["year"], dtype=float)
    y0 = initial_state_from_data(
        plhiv=float(observations.values["plhiv"][0]),
        art_coverage=float(observations.values["art_coverage"][0]),
        population=float(context["population"][0]),
    )
    span = (0.0, float(observations.t[-1]))

    runs = {
        "constant rates (as published)": DRC_2020,
        "logistic scale-up of alpha and lambda": DRC_2020.replace(**SCALEUP),
    }
    curves = {}
    for label, p in runs.items():
        solution = simulate(p, y0=y0, t_span=span, n_points=401)
        curves[label] = (years[0] + solution.t, apply(solution, observations.names))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    panels = [
        ("art_coverage", "ART coverage", 100.0, "%"),
        ("plhiv", "People living with HIV", 1.0, "millions"),
    ]
    colours = ["#1f77b4", "crimson"]
    for ax, (key, title, scale, unit) in zip(axes, panels, strict=True):
        ax.scatter(years, np.asarray(observations.values[key]) * scale, color="#444",
                   s=22, zorder=3, label="UNAIDS / World Bank")
        for colour, (label, (t, modelled)) in zip(colours, curves.items(), strict=True):
            ax.plot(t, np.asarray(modelled[key]) * scale, color=colour, lw=2.2,
                    label=label)
        ax.set_title(title)
        ax.set_xlabel("year")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel(unit)
        ax.grid(alpha=0.3)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle(
        "The published model against real DRC data: "
        "fixing one series breaks the other",
        fontsize=13,
    )
    fig.tight_layout()
    path = OUT / "real_data.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")

    last = float(observations.t[-1])
    observed_cov = float(observations.values["art_coverage"][-1])
    observed_plhiv = float(observations.values["plhiv"][-1])
    print(f"\n  {years[-1]:.0f} observed: coverage {observed_cov:.1%}, "
          f"PLHIV {observed_plhiv:.3f} M")
    for label, (t, modelled) in curves.items():
        cov = float(np.interp(years[0] + last, t, modelled["art_coverage"]))
        plhiv = float(np.interp(years[0] + last, t, modelled["plhiv"]))
        print(f"  {label}: coverage {cov:.1%}, PLHIV {plhiv:.3f} M")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    copy_cli_figures()
    draw_real_data()
