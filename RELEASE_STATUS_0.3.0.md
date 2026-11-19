# 0.3.0 release status and evidence

**Status:** published, final release complete **2026-11-19**.
This file is a post-release evidence summary, **not** a substitute for
reviewing present-day vulnerability status or a promise about downstream
application security.

## Immutable release identifiers

- PyPI package: [fastapi-cache-stable==0.3.0](https://pypi.org/project/fastapi-cache-stable/0.3.0/)
- GitHub Release: [v0.3.0](https://github.com/agustin18/fastapi-cache/releases/tag/v0.3.0)
- Annotated tag `v0.3.0` dereferences to:
  `c1b83036a4d3900432a96a44686cf6dd56cf8618`
- [TestPyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44582554928):
  successful on the exact release commit.
- [Production PyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44586143153):
  seven successful jobs: source preflight, Python 3.10/3.11/3.12/3.13
  tests, build and PyPI Trusted Publishing.

## Published distribution digests

| File | SHA-256 |
|---|---|
| `fastapi_cache_stable-0.3.0-py3-none-any.whl` | `d6c3c4f66c0a4f7f97aecd7df16f125dafb3bdd3481c37a98254c8724a413d04` |
| `fastapi_cache_stable-0.3.0.tar.gz` | `4dfb09e1da3c575731f929d863a0e31e7b48a0cbd843d1702aea3ca2df27b6a1` |

The same file hashes appeared in TestPyPI and production publishing
workflow logs; the production build completed `twine check`.
Source-control and publishing workflow status were independently
verified using GitHub. **A post-release documentation commit does not
retroactively alter these immutable distribution files.**

## Application and security checks

- The executing **local release agent reported** clean install of the
  published wheel, `pip check`, and a FastAPI MISS→HIT smoke test.
  These are agent-reported checks, not re-run independently in this
  documentation PR.
- The same agent reported a final **authenticated Dependabot delta
  comparison** against the 2026-11-19 snapshot: the **21 open alerts
  were unchanged**, with no new alerts at the point of publication.
  This is *not* a live feed of future findings.
- The original 95-row historical security ledger and 21 scoped release
  dispositions remain available in
  [the audit archive](audit/security/README.md) and the
  [accepted bounded decision](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
  They were never mass-dismissed or represented as globally fixed.
- 0.3.x security and critical correctness maintenance applies
  **best-effort** to server-side CPython 3.11–3.13 for the 12-month
  target from 2026-11-19; Python 3.8–3.10 remain functional legacy
  compatibility only. See [SUPPORT.md](SUPPORT.md).

## Next work

See [ROADMAP.md](ROADMAP.md) and its linked issues for post-release
maintenance, security/dependency hygiene, documentation and future
Redis-client compatibility. This record is **closed** for 0.3.0
unless evidence of an error in the historical release facts appears.
