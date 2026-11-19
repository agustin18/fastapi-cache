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

## RC2 published and validated — 2026-11-19

- [x] PR #39 merged, immutable `v0.3.0rc2` tag resolves to
  `277b6e71dac5c2807acdbc11366a7864aec1927a`.
- [x] [TestPyPI workflow 44456382885](https://github.com/agustin18/fastapi-cache/actions/runs/44456382885)
  and [PyPI workflow 44458562090](https://github.com/agustin18/fastapi-cache/actions/runs/44458562090)
  completed with Python 3.10–3.13 tests and release checks.
- [x] Matching published wheel SHA-256:
  `2c3f35e053770edd708c42e88e1d2d788bc3c2ed6e2bb3d5b8409f48b79762bf`.
  Matching sdist SHA-256:
  `145df1aada6deafc90faa3558589b8ac91276fb14eadf28e78e250032998fa1e`.
- [x] Published-wheel Redis 7.4.12 legacy writer → RC2 reader → legacy
  rollback E2E and clean Python 3.11 wheel install/`pip check`,
  as reported by the executing agent.
- [x] Consumer `real-estate-arg`: agent reports **130/130** selected tests
  passing with the published RC2 wheel **overlaid** on the running container
  (FastAPI 0.136.3, redis-py 4.6.0). The installed dependency was left
  unchanged; this is **functional-only**, not a resolver/install test.
- [ ] Independent clean `pip` replacement + resolver + tests in disposable
  consumer environment. Do not count an import overlay as this gate.
- [x] Exact PyPI-published RC2 wheel audit completed on Python 3.11–3.13
  with all extras: 3/3 SHA-256 checks, clean venv installs and `pip check`,
  73 packages installed and 72 third-party packages scanned per profile,
  no known findings. See [archived provenance](audit/security/RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md)
  and linked workflow artifacts (90-day retention).
- [ ] Approve residual legacy/consumer GHSA scope in a dedicated review;
  the clean modern wheel does not itself close the 21 open lockfile alerts.

## Before stable promotion

- [x] Remove the unused `StaticFiles(directory="./")` mount from the
  Redis example, with a passing regression guard (PR #37).
- [x] Capture a fresh authenticated Dependabot snapshot on 2026-11-19
  (120 records, 21 open) and add
  [GHSA-7f5h-v6xp-fcq8](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)
  as current-only advisory #120. This is conditionally scoped for RC2,
  **not** a claim that legacy Starlette or consumers are patched.
- [ ] Obtain explicit maintainer signoff on
  [the 95-row pre-stable review](audit/security/STABLE_RELEASE_SECURITY_REVIEW_20261119.md),
  including this GHSA, the AnyIO critical legacy acceptance and other
  consumer-owned file-serving routes. Proposed verdicts are not approved
  dispositions.

- [ ] Review opt-in OpenAPI response-model inference and regression tests
  for legacy return annotations; characterize dependency-injection
  cache-key stability without changing the default key builder.
- [ ] Reproduce
  [fastapi-pagination #557](https://github.com/long2ice/fastapi-cache/issues/557)
  with its stated dependency versions; document a known failure separately
  from package-supported interoperability.
- [ ] Repeat owner-application Redis/InMemory checks against a wheel
  downloaded from PyPI and verified by SHA-256, not editable source.
- [x] Cross-check the 95-row ledger/triage with all 120 records in the
  authenticated source snapshot; fail closed if a newly opened GHSA is absent
  or if identifiers, manifest or vulnerable version ranges differ.
- [x] Reconcile and individually account for all 95 historical/current GHSA
  in [the pre-stable review ledger](audit/security/STABLE_RELEASE_SECURITY_REVIEW_20261119.csv).
  This is **proposed evidence review**, not risk acceptance.
- [ ] Approve the 21 open advisory verdicts and close the canonical
  [GHSA triage register](audit/security/SECURITY_ADVISORY_TRIAGE.csv)
  with traceable final decisions; historical fixed-state entries must not be
  confused with live vulnerability status.
- [ ] Resolve/mitigate or explicitly accept residual risks within the
  agreed security-support contract. No unmitigated critical/high
  vulnerability directly reachable in a package-controlled path.
- [ ] Repeat exact-artifact runtime audits for the final candidate
  and compare METADATA, installed inventory and wheel/sdist hashes.
- [ ] If code changes after the published RC, publish a new prerelease
  candidate (for example `rc3`) and test that exact artifact before stable.
- [ ] Prepare stable metadata/version, CHANGELOG and support notices;
  verify CI, release workflow and publish from the reviewed commit.
- [ ] Approve the stable publication explicitly, as a separate action.

## Outside the first stable promise

Redis-py 5/6, an opt-in `exclude_params` facility, cache-stampede
prevention and tag invalidation remain candidates for later releases
unless a newly verified regression makes one necessary now.
The default key builder must not silently change or omit tenant/user
identity. DynamoDB/Memcached remain experimental.
