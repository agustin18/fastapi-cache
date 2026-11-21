# 0.6.0 release candidate — exact-artifact acceptance (DRAFT)

> **NOT PUBLISHED. NOT AUTHORIZED FOR TAG OR PYPI.**
> The latest released distribution is `fastapi-cache-stable==0.5.0`.
> This file is an execution contract for the local release operator,
> not a record of completed evidence or an approval to deploy.

## Scope freeze

- [x] [#85](https://github.com/agustin18/fastapi-cache/pull/85): opt-in
  bounded `InMemoryBackend(max_entries=N)`, indexed expiration heap and LRU;
  `max_entries` is a read-only property fixed at construction.
- [x] [#93](https://github.com/agustin18/fastapi-cache/pull/93): published
  0.5.0 vs merged/unreleased source documented separately.
- [ ] [#53](https://github.com/agustin18/fastapi-cache/issues/53):
  classify package-owned and application-owned hidden identity/context
  risks, document negative/positive reproductions and explicit reviewer
  risk acceptance. A demonstrated unresolved package-controlled cross-tenant
  disclosure is a **NO-GO**.
- [ ] Confirm [#50](https://github.com/agustin18/fastapi-cache/issues/50)
  event hooks and [#49](https://github.com/agustin18/fastapi-cache/issues/49)
  parameter exclusion **remain outside 0.6.0**; defer feature work.
- [ ] Verify site copy for public competitor-neutral positioning and
  retained *published* 0.5.0 installation instructions.

## Candidate build and tests — every checkbox requires actual evidence

- [ ] Record PR HEAD SHA and merge SHA. Bump metadata to `0.6.0` on this
  **unmerged candidate branch**; do not create `v0.6.0` tag yet.
- [ ] Exact HEAD CI on Python 3.8–3.13, lint/types, Redis, benchmarks,
  CodeQL, installed-runtime security, release changelog gate and docs
  link validator all **green**. Log run URLs and failing-retry disposition.
- [ ] [Phase B workflow](../../.github/workflows/migration-candidate-phase-b.yml):
  build a SINGLE 0.6.0 wheel/sdist pair, record **actual SHA-256** values,
  verify wheel METADATA and sdist pyproject, artifact provenance, and
  `twine check`; no re-build inside consumer lanes.
- [ ] 12 Python 3.8–3.13 × wheel/sdist runs on dedicated Redis 7.4:
  published legacy writer → exact 0.6.0 candidate reader →
  restricted ordinary-data rollback; verify `pip check` and targeted
  namespace cleanup, retain golden keys. Never resume unsafe private
  caching after rollback.
- [ ] Installed independent *in-repo CI fixture* verifies ordinary
  MISS/HIT/304, protected-request bypass, opt-in `Vary`,
  `max_entries=2` LRU eviction, public capacity immutability,
  default unbounded behavior. This is **not** consumer #91.
- [ ] Verify locked main-only Poetry profiles and installed wheel/sdist
  `Requires-Python >=3.8,<3.14`. CPython 3.8–3.10 remains
  **legacy functional only**; recommended security-supported servers
  are CPython 3.11–3.13. Do not claim 3.14, TLS/Sentinel/Cluster or
  experimental backends are certified.
- [ ] Fresh authenticated Dependabot delta versus baseline and
  installed wheel/sdist dependency scans *from the final merge SHA*;
  document affected path/reachability, mitigation and high/critical
  decisions individually. A passing prior-release audit is not a
  surrogate for candidate package evidence.

## Real independent consumers — release blocker

- [ ] [#91 Consumer A](https://github.com/agustin18/fastapi-cache/issues/91):
  independently maintained new app exercises standalone Redis, InMemory,
  private/tenant safeguards, install metadata, lifecycle and error cases.
- [ ] [#91 Consumer B](https://github.com/agustin18/fastapi-cache/issues/91):
  independently maintained legacy user migrates real app from released
  0.2.2, with clean install, selective Redis cleanup and safe rollback.
- [ ] Attach evidence, versions, permissioned identifiers and actual
  package digests. Fork examples, owner-run fixture and CI jobs count
  **0/2**, even if all internal checks pass.

## Promotion — distinct manual authorizations

- [ ] Freeze final source/doc/lock/changelog SHA. Generate the real
  `0.6.0` section in CHANGELOG using Towncrier, consuming release
  fragments **only in the promotion PR**. Any change after evidence
  capture requires a fresh exact-artifact run.
- [ ] Prepare `0.6.0rc1` only if a separately approved prerelease
  is useful for independent external exercises. A final-version
  candidate wheel **must not be uploaded** under an RC tag.
- [ ] Explicit maintainer GO for a final immutable tag, TestPyPI
  publish and smoke install; record tag/commit and both exact hashes.
- [ ] Re-check dependencies, risk decisions and consumers, then obtain
  **separate** maintainer GO for production PyPI; use manual publish
  workflows, observe results and preserve provenance.
- [ ] After release, repin the in-repo migration demo from 0.5.0 to
  **the exact published 0.6.0 distribution** and rerun it.
- [ ] Publish version-accurate public documentation through restricted
  `github-pages` environment on `stable` only; verify live URL,
  links/search/mobile and preservation of historical v0.5.0 docs
  before adding an external website link or advertising #88.

## Evidence ledger

| Requirement | Source SHA / workflow | Evidence URL or SHA-256 | Status |
|---|---|---|---|
| CI, security, docs | TBD | TBD | PENDING |
| Exact wheel SHA-256 | TBD | TBD | PENDING |
| Exact sdist SHA-256 | TBD | TBD | PENDING |
| Phase B 13/13 | TBD | TBD | PENDING |
| Fresh Dependabot delta | TBD | TBD | PENDING |
| #53 privacy disposition | TBD | TBD | PENDING |
| #91 consumer A | TBD | TBD | PENDING |
| #91 consumer B | TBD | TBD | PENDING |
| Final GO / tag / TestPyPI / PyPI | TBD | TBD | **NOT AUTHORIZED** |

The scope and status in [#92](https://github.com/agustin18/fastapi-cache/issues/92)
are authoritative; a merged candidate PR is **not** consent to publish.
