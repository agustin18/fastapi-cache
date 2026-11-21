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
  candidate source (merged in #94, with corrective PR pending); do not
  create `v0.6.0` tag yet.
- [ ] Exact HEAD CI on Python 3.8–3.13, lint/types, Redis, benchmarks,
  CodeQL, installed-runtime security, release changelog gate and docs
  link validator all **green**. Log run URLs and failing-retry disposition.
- [ ] [Phase B workflow](../../.github/workflows/migration-candidate-phase-b.yml):
  build a SINGLE 0.6.0 wheel/sdist pair, record **actual SHA-256** values,
  verify wheel METADATA and sdist pyproject, artifact provenance, and
  `twine check`; no re-build inside consumer lanes. Require all 12
  migration lanes AND seven exact-bundle security profiles (20 jobs total,
  including build). Source-only diagnostic security builds are not final
  binary evidence.
- [ ] 12 Python 3.8–3.13 × wheel/sdist runs on dedicated Redis 7.4:
  published legacy writer → exact 0.6.0 candidate reader →
  restricted ordinary-data rollback; verify `pip check` and targeted
  namespace cleanup, retain golden keys. Never resume unsafe private
  caching after rollback.
- [ ] Installed *in-repo CI fixture* verifies ordinary
  MISS/HIT/304, protected-request bypass, opt-in `Vary`,
  `max_entries=2` LRU eviction, public capacity immutability,
  default unbounded behavior. This is controlled installed-package verification.
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

## Release validation policy

Release readiness is determined by reproducible technical evidence and
maintainer approval, under [CONTRIBUTING.md](../../CONTRIBUTING.md).
Project-authored fixtures, installed-distribution tests, integration
services and maintainer-run checks are valid technical evidence.
Application feedback can strengthen coverage but is voluntary.

No minimum number of users, external applications, deployments, or
testimonials is required for any release or announcement. Do not invent
or solicit evidence merely to meet a quota. Public claims must reflect
what was actually tested; private application details are not required.

## Promotion — distinct manual authorizations

- [ ] Freeze final source/doc/lock/changelog SHA. Generate the real
  `0.6.0` section in CHANGELOG using Towncrier, consuming release
  fragments **only in the promotion PR**. The release-promotion workflow
  must regenerate the changelog from the stable base with the version/date
  in the new entry and compare output byte-for-byte. Do not bypass this
  gate or reuse the 0.5.0 release date. Any change after evidence
  capture requires a fresh exact-artifact run.
- [ ] Confirm the `pypi`, `testpypi` and `github-pages` GitHub
  Environments have appropriately restricted source branches and
  human reviewers where supported. In particular, protect Pages to
  `stable` only. Do not treat `workflow_dispatch` alone as a
  sufficient release-authorization control.
- [ ] Prepare `0.6.0rc1` only if a separately approved prerelease
  is useful for additional technical verification. A final-version
  candidate wheel **must not be uploaded** under an RC tag.
- [ ] Explicit maintainer GO for a final immutable tag, TestPyPI
  publish and smoke install; record tag/commit and both exact hashes.
- [ ] Re-check dependencies and risk decisions, then obtain
  **separate** maintainer GO for production PyPI. Both manual workflows
  require the annotated version tag, the successful manual Phase B run
  on that exact stable commit, and explicitly approved wheel/sdist hashes.
  They retrieve/verify the same pair instead of rebuilding. Production
  requires matching TestPyPI index digests and fresh authenticated
  Dependabot delta. Smoke-install from TestPyPI before production approval;
  after publication download both files and verify hashes.
- [ ] After release, repin the in-repo migration demo from 0.5.0 to
  **the exact published 0.6.0 distribution** and rerun it.
- [ ] Publish version-accurate public documentation through restricted
  `github-pages` environment on `stable` only; verify live URL,
  links/search/mobile and preservation of historical v0.5.0 docs
  before adding a link to the hosted site. This is a separate docs task,
  not a release or ordinary announcement gate.

## Evidence ledger

| Requirement | Source SHA / workflow | Evidence URL or SHA-256 | Status |
|---|---|---|---|
| CI, security, docs | TBD | TBD | PENDING |
| Exact wheel SHA-256 | TBD | TBD | PENDING |
| Exact sdist SHA-256 | TBD | TBD | PENDING |
| Phase B build + 12 migration + 7 exact security | TBD | TBD | PENDING |
| Fresh Dependabot delta | TBD | TBD | PENDING |
| #53 privacy disposition | TBD | TBD | PENDING |
| Final GO / tag / TestPyPI / PyPI | TBD | TBD | **NOT AUTHORIZED** |

The scope and status in [#92](https://github.com/agustin18/fastapi-cache/issues/92)
are authoritative; a merged candidate PR is **not** consent to publish.
