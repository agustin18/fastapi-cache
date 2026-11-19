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

## Before stable promotion

- [ ] Characterize OpenAPI response-model inference and dependency-injection
  cache-key stability. Add regressions for any package-owned fixes.
- [ ] Reproduce
  [fastapi-pagination #557](https://github.com/long2ice/fastapi-cache/issues/557)
  with its stated dependency versions; document a known failure separately
  from package-supported interoperability.
- [ ] Repeat owner-application Redis/InMemory checks against a wheel
  downloaded from PyPI and verified by SHA-256, not editable source.
- [ ] Complete the 94-row [GHSA register](SECURITY_ADVISORY_TRIAGE.csv):
  93 historical IDs plus one current-only ID. Reconcile each row with
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
