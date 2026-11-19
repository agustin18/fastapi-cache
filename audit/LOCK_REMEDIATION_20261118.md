# Security lock remediation — pre-stable candidate

This audit note explains the **development and CI lock only**.
It does not change the runtime dependency metadata that users receive
when installing `fastapi-cache-stable` from PyPI, and it does not
constitute a maintainer disposition for any GHSA.

## Scope and exact process

- Base: `stable` after merged PR #33 (`0358f2d`).
- Regenerate `poetry.lock` with pinned **Poetry 1.8.3**, never by hand.
- Test-only Poetry `dev` dependencies are Python-marker split. The wheel's
  `[tool.poetry.dependencies]`, Python `>=3.8,<3.14`, and backend extras
  are **unchanged**.
- Legacy Python 3.8–3.10 remains functional-only; Python 3.11–3.13 has
  server-side security support. Python 3.10 has additionally been given
  patched locked development packages where compatible.
- Runtime-wheel security and consumer reachability are evaluated
  independently from all-extras development lock files.

## Security comparison (snapshot, NOT a fresh Dependabot API count)

The committed `DEPENDABOT_ALERTS_20261118T165114Z.csv` has 42 open
alerts in `poetry.lock`. The pre-update lock included older FastAPI,
Starlette, urllib3, Jinja2 and tooling.

The generated lock's relevant Python variants are:

| Dependency | Legacy version (where necessary) | Patched modern version |
|---|---|---|
| FastAPI | 0.124.4 (Py3.8) | 0.162.5 (Py3.10), 0.165.0 (Py3.11+) |
| Starlette | 0.44.0 (Py3.8/3.9) | 1.7.0 (Py3.10), 1.10.0 (Py3.11+) |
| urllib3 | 2.2.3 (Py3.8/3.9) | 2.8.0 (Py3.10+) |
| AnyIO | 4.5.2 (Py3.8/3.9) | 4.14.2 (Py3.10+) |
| requests | 2.32.4 (Py3.8/3.9) | 2.34.2 (Py3.10+) |
| pytest | 8.3.5 (Py3.8/3.9) | 9.2.0 (Py3.10+) |
| idna | 3.7 (Py3.8) | 3.20 (Py3.9+) |
| Pygments | 2.18.0 (Py3.8) | 2.21.0 (Py3.9+) |
| cryptography | Not directly required by the old dev profile | 50.0.2 (modern) |
| Jinja2 | — | 3.1.6 |

The latest FastAPI dependency graph no longer installs some packages
that were present under FastAPI 0.111.1 (including python-multipart,
dnspython and python-dotenv), **but consumers may explicitly install
those packages**, and their advisory applicability is application-specific.

A comparison with the **saved** 42-alert snapshot before the final split
found 11 advisory entries whose package disappeared from that lock,
11 whose package variants were entirely at or above their first patched
version, and 20 involving at least one older variant. These are
diagnostic counts only: they are not actual GitHub Dependabot closure
counts nor proof that a GHSA is exploitable or fixed in every consumer.
The final lock keeps a few older variants specifically for EOL Python.

## Evidence required before merge and stable

- [ ] `poetry check --lock`, pinned Poetry 1.8.3.
- [ ] CI locked `--with dev --all-extras --sync` profiles: Python
  3.8, 3.9, 3.10, 3.11 and 3.12; the modern version baselines are
  asserted inside those actual environments.
- [ ] Main-only lock installs on Python 3.8 and 3.11; `pip check`
  and imports must succeed.
- [ ] Full package functional/legacy, Redis and optional backend tests.
- [ ] Clean installed-wheel audits on Python 3.11–3.13, with complete
  dependency inventory and package identity.
- [ ] Independent GHSA dispositions per release stage in
  [`SECURITY_ADVISORY_TRIAGE.csv`](../SECURITY_ADVISORY_TRIAGE.csv).
  The decision to accept legacy residual vulnerabilities is distinct from
  marking Dependabot warnings fixed.
- [ ] If code or package metadata change after `0.3.0rc1`, release and
  retest a new immutable RC before the first stable release.

Modern dev constraints are not evidence that applications installing older
FastAPI or doing form, proxy or network work have no vulnerabilities.
This PR must not automatically dismiss GitHub alerts or authorize stable.
