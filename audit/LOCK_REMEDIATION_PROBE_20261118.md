# Dependabot lock remediation — isolated resolver probe

**Status: evidence-gathering, NOT a security disposition or merge candidate.**

The pinned Poetry 1.8.3 lock supports CPython `>=3.8,<3.14` across all
declared dependency groups, including legacy-only test/development profiles.
GitHub's 2026-11-18 snapshot contains **42 open alerts** in `poetry.lock`,
31 marked runtime and 11 development; the alert scope describes the locked
dependency graph, **not** exploitability through the published library.

The published RC wheel installed with current dependencies on Python
3.11–3.13 passed a separate `pip-audit` per profile. Those results do not
remove lockfile alerts or replace the
[GHSA triage](../SECURITY_ADVISORY_TRIAGE.csv).

## Resolver experiments

The workflow job is **branch-gated** to this temporary audit PR. It uses
Python 3.12 and the pinned Poetry 1.8.3 resolver to run three independent
`poetry update ... --lock` commands against copies of `pyproject.toml`
and `poetry.lock` in a temporary directory, never against the checkout.
It produces a per-experiment JSON before/after package graph, a candidate
lock and the exact resolver log, including a nonzero failure code.

- **Transitive/development candidates:** requests, Jinja2, urllib3,
  cryptography, dnspython, pytest, python-multipart.
- **Framework constraints:** FastAPI, Starlette and python-multipart together.
- **Legacy AnyIO boundary:** AnyIO alone.

The resolver is allowed to **fail**. A successful upload artifact merely means
the experiment ran, not that the lock is secure or suitable for merge.

## Promotion decision

Only propose actual manifest/lock changes after reviewing the result,
verifying that Python 3.8/3.9 still install the stated legacy profile and
that the Python 3.11–3.13 runtime and all optional extras remain valid.
A resolved package version or patched advisory must not be assumed to cover
all interpreter markers or reachable consumer paths.

Before incorporating any candidate lock:

1. Confirm the exact Poetry-generated diff, content hash and locked variants.
2. Require `poetry check --lock`, `--only main` and all-extras CI across
   supported profiles; add focused tests where package behavior could change.
3. Re-run separately audited installed-wheel profiles and capture JSON
   dependencies and hashes.
4. Reconcile the GHSA IDs with explicit evidence and maintainer decisions;
   do not bulk-dismiss Dependabot.
5. If fixing all high-severity alerts would require dropping EOL Python
   support, obtain a **separate** product/support-policy decision rather
   than silently relaxing compatibility.

This audit PR should be closed without merge or replaced by a narrowly
scoped, fully tested **real lock update PR** after inspecting the artifacts.
