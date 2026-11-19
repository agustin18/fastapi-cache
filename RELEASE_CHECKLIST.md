# Stable release readiness

This is the **one maintained release-status checklist**. User-facing guides
avoid hardcoding the current alpha/beta/RC in several files. Historic versions
belong in [CHANGELOG.md](CHANGELOG.md). Check
[PyPI](https://pypi.org/project/fastapi-cache-stable/) for published versions.

## Evidence already obtained

- Source release candidate: `0.3.0rc1`, built from `stable`
  `9a2f708c3b727f3a9194eba73dfc19507c1993bc`.
- [TestPyPI](https://test.pypi.org/project/fastapi-cache-stable/0.3.0rc1/)
  and [PyPI](https://pypi.org/project/fastapi-cache-stable/0.3.0rc1/)
  contain the same tested distributions.
- Wheel SHA-256:
  `251d5249feb319e99ba3438c929b618124a34525a4188dbe3817973d1edba6db`.
- Sdist SHA-256:
  `374cac1c57948f2fc63613b744c2609a788177edf0988261d518019eea173415`.
- CI for the release commit and publish workflows passed on Python
  3.10–3.13; runtime audits on Python 3.11–3.13 reported 72 third-party
  dependencies, zero known findings at the time of the scan.
- The
  [Redis 7.4.12 published-wheel migration E2E](https://github.com/agustin18/fastapi-cache/actions/runs/44427808411)
  passed with isolated legacy writer → published RC reader → legacy
  rollback reader. [PR #32](https://github.com/agustin18/fastapi-cache/pull/32)
  is a disposable test-only PR, not a change intended for merge.
- One maintainer-owned application previously passed Redis and InMemory
  integration tests using a local candidate wheel. That does **not**
  prove the owner application passed using the **published** RC wheel.

## RC2 release preparation — not yet published

- [x] PRs #33, #35, #36, #37 and #38 have been integrated in `stable`.
- [x] The latest authenticated security snapshot is
  [20261119T032907Z](audit/security/DEPENDABOT_ALERTS_20261119T032907Z.csv):
  21 open alerts with separately documented applicability; the new
  Starlette Range advisory is current-only #120 and remains open.
- [x] Set candidate source version to `0.3.0rc2` and build release notes
  with Towncrier from the six merged change fragments.
- [ ] Review and approve the **exact release PR head** after CI, CodeQL,
  Poetry lock profiles and wheel/sdist checks all pass.
- [ ] Merge this candidate preparation PR to `stable`, then create and
  verify a unique `v0.3.0rc2` tag on the reviewed release commit.
- [ ] Obtain explicit publication approval; publish to TestPyPI and PyPI
  via protected manual workflows, never from an unreviewed branch.
- [ ] Download the published wheel and sdist, record **new** SHA-256 hashes,
  compare METADATA/inventory, scan the exact installed wheel across modern
  supported Python versions, and run Redis migration plus owner-application
  Redis/InMemory verification from the published wheel.

Previous RC1 hashes below remain historical provenance; they are not
hashes of the newly prepared RC2 artifacts.

## Before stable promotion

- [x] Remove the unused `StaticFiles(directory="./")` mount from the
  Redis example, with a passing regression guard (PR #37).
- [x] Capture a fresh authenticated Dependabot snapshot on 2026-11-19
  (120 records, 21 open) and add
  [GHSA-7f5h-v6xp-fcq8](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)
  as current-only advisory #120. This is conditionally scoped for RC2,
  **not** a claim that legacy Starlette or consumers are patched.
- [ ] Complete the final risk decision for this GHSA before stable,
  including consumer-owned file-serving routes on legacy Python.

- [ ] Review opt-in OpenAPI response-model inference and regression tests
  for legacy return annotations; characterize dependency-injection
  cache-key stability without changing the default key builder.
- [ ] Reproduce
  [fastapi-pagination #557](https://github.com/long2ice/fastapi-cache/issues/557)
  with its stated dependency versions; document a known failure separately
  from package-supported interoperability.
- [ ] Repeat owner-application Redis/InMemory checks against a wheel
  downloaded from PyPI and verified by SHA-256, not editable source.
- [ ] Complete the 95-row [GHSA register](audit/security/SECURITY_ADVISORY_TRIAGE.csv):
  93 historical IDs plus two current-only IDs. Reconcile each row with
  proportionate proof and explicit disposition; a triage PENDING
  record is **not** an open Dependabot alert.
- [ ] Resolve/mitigate or explicitly accept residual risks within the
  agreed security-support contract. No unmitigated critical/high
  vulnerability directly reachable in a package-controlled path.
- [ ] Repeat exact-artifact runtime audits for the final candidate
  and compare METADATA, installed inventory and wheel/sdist hashes.
- [ ] If code changes after the published RC, publish a new prerelease
  candidate (for example `rc2`) and test that exact artifact before stable.
- [ ] Prepare stable metadata/version, CHANGELOG and support notices;
  verify CI, release workflow and publish from the reviewed commit.
- [ ] Approve the stable publication explicitly, as a separate action.

## Outside the first stable promise

Redis-py 5/6, an opt-in `exclude_params` facility, cache-stampede
prevention and tag invalidation remain candidates for later releases
unless a newly verified regression makes one necessary now.
The default key builder must not silently change or omit tenant/user
identity. DynamoDB/Memcached remain experimental.
