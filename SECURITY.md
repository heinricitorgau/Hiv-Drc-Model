# Security policy

## Scope

This is a research codebase: an ODE model, its estimation and sampling code, a command-line
interface and a Streamlit dashboard. It handles no credentials or personal data. The places where
a security issue could plausibly arise are:

- `Observations.from_csv` and other code that reads user-supplied files;
- `scripts/fetch_worldbank.py`, the only code that touches the network;
- `app.py`, if the dashboard is deployed publicly;
- the dependency set declared in `pyproject.toml`.

Numerical errors — a wrong R₀, a biased estimator, a miscalibrated interval — are bugs, not
security issues. Please report them as ordinary issues.

## Supported versions

Only the latest commit on `main` receives fixes.

| Version        | Supported |
| -------------- | --------- |
| `main`         | ✅        |
| anything older | ❌        |

## Reporting a vulnerability

**Please do not open a public issue.** Use GitHub's private vulnerability reporting instead:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Describe the problem, how to reproduce it, and what an attacker could achieve.

You can expect an acknowledgement within 7 days. Once the issue is confirmed, a fix will be
prepared and you will be credited in the advisory unless you prefer otherwise.
