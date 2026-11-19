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
- [x] Clean `pip` replacement in a disposable `real-estate-arg` Docker
  backend, **as reported by the executing local agent**: removed
  `fastapi-cache2==0.2.2`, installed the exact published PyPI
  `fastapi-cache-stable[redis]==0.3.0rc2` with normal dependency
  resolution, `pip check` passed, `130 passed in 16.58s`.
  Original checkout/container kept `fastapi-cache2==0.2.2`.
  Note: no independently archived CI artifact for this consumer test;
  attach its logs/provenance to final release review.
- [x] Exact PyPI-published RC2 wheel audit completed on Python 3.11–3.13
  with all extras: 3/3 SHA-256 checks, clean venv installs and `pip check`,
  73 packages installed and 72 third-party packages scanned per profile,
  no known findings. See [archived provenance](audit/security/RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md)
  and linked workflow artifacts (90-day retention).
- [x] Record maintainer-directed release-specific **bounded risk acceptance**
  for all 21 captured open GHSA, without dismissing their GitHub alerts:
  [0.3.0 signoff record](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
  Separate independent contra-audit and fresh snapshot are still needed
  before publication.

## Before stable promotion

- [x] Remove the unused `StaticFiles(directory="./")` mount from the
  Redis example, with a passing regression guard (PR #37).
- [x] Capture a fresh authenticated Dependabot snapshot on 2026-11-19
  (120 records, 21 open) and add
  [GHSA-7f5h-v6xp-fcq8](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8)
  as current-only advisory #120. This is conditionally scoped for RC2,
  **not** a claim that legacy Starlette or consumers are patched.
- [x] Record the maintainer-requested scoped 21-GHSA acceptance in
  [the 0.3.0 decision](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md),
  checked against the [95-row historical review](audit/security/STABLE_RELEASE_SECURITY_REVIEW_20261119.md).
  This records an explicit owner direction, **not** a forged GitHub
  review signature or approval of the final publish action.
  Python 3.8–3.10 remain functional legacy only.

- [x] Review opt-in OpenAPI response-model inference and regressions
  for legacy return annotations; exercise DI/cache-key behavior in
  PR #33 and its regression CI without changing default key generation.
- [x] Characterize
  [fastapi-pagination #557](https://github.com/long2ice/fastapi-cache/issues/557)
  in pinned CI; this bounds the reported configuration and does not
  claim blanket interoperability with every version.
- [x] Repeat owner-application tests using the published PyPI RC2 wheel:
  initial wheel-overlay test and later genuine dependency replacement in
  a disposable `real-estate-arg` container each passed **130** selected
  tests, per local agent; the clean replacement included `pip check`.
  Preserve logs/digest evidence for release provenance.
- [x] Cross-check the 95-row ledger/triage with all 120 records in the
  authenticated source snapshot; fail closed if a newly opened GHSA is absent
  or if identifiers, manifest or vulnerable version ranges differ.
- [x] Reconcile and individually account for all 95 historical/current GHSA
  in [the pre-stable review ledger](audit/security/STABLE_RELEASE_SECURITY_REVIEW_20261119.csv).
  This is **proposed evidence review**, not risk acceptance.
- [x] Record all **21** individually scoped release dispositions in the
  [maintainer acceptance document](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
  Preserve the [canonical source triage](audit/security/SECURITY_ADVISORY_TRIAGE.csv)
  and original GitHub alert states/PENDING evidence unchanged. The separate
  decision document carries the **release acceptance**, not a fictitious
  vulnerability fix.
- [x] Document/accept scoped residual dependency risks within the
  Python 3.11–3.13 support contract, according to the paths reviewed.
- [ ] Independent contra-auditor confirms **no directly reachable
  unmitigated critical/high vulnerability controlled by the library**
  in the exact promotion diff.
- [ ] Repeat exact-artifact runtime audits for the final candidate
  and compare METADATA, installed inventory and wheel/sdist hashes.
- [x] Runtime library/backend code and dependency constraints remain
  unchanged from the published RC2; this PR prepares release metadata,
  version and documentation only. No RC3 required on that basis.
  **If the contra-audit leads to runtime changes**, publish a new RC and
  test its exact artifact before revisiting stable.
- [x] Stage `0.3.0` metadata/version, release notes and support notices
  in a distinct PR; release changelog fragments are preserved for
  Towncrier release generation.
- [ ] Verify the merged commit, final distribution CI/security audits
  and manual publishing workflow from the immutable `v0.3.0` tag.
- [ ] Approve the stable publication explicitly, as a separate action.

## Documentation and operations before stable

- [x] Document Python 3.8–3.10 functional-only legacy compatibility
  and recommend Python 3.11–3.13 in the README, COMPATIBILITY,
  SECURITY, SUPPORT and migration documentation.
- [x] Record maintainer-directed scoped 21-GHSA acceptance; it leaves
  Dependabot alerts unchanged.
- [x] The independent agent gave **technical GO for PR #42**; the
  maintainer explicitly directed the scoped 21-GHSA acceptance recorded
  [in that PR's discussion](https://github.com/agustin18/fastapi-cache/pull/42#issuecomment-7016369125).
  A second self-approval review is not required.
- [ ] Run **one authenticated Dependabot delta check immediately before
  production PyPI publication**, against the 2026-11-19 source snapshot.
  Review newly open/reopened/changed alerts; do not re-triage the
  21 unchanged and explicitly accepted legacy/consumer risks.
  This does not block the non-production TestPyPI smoke test.
- [x] On 2026-11-19 the maintainer **reported the Compose secret issue
  resolved**. This is the owner's attestation, not a claim that this
  audit independently accessed private rotation records.
- [x] Open a distinct stable-promotion PR with version/metadata/notes;
  **not** a PyPI publish or tag.
- [ ] Verify exact final 0.3.0 wheel/sdist metadata and SHA-256, then
  publish to **TestPyPI** using the manual workflow and smoke-install
  it in a clean environment. The post-merge CI, including modern
  dependency security profiles, already passed.
- [ ] Explicitly authorize **production PyPI publication** after the
  TestPyPI artifact check and one current Dependabot delta check.

## Outside the first stable promise

Redis-py 5/6, an opt-in `exclude_params` facility, cache-stampede
prevention and tag invalidation remain candidates for later releases
unless a newly verified regression makes one necessary now.
The default key builder must not silently change or omit tenant/user
identity. DynamoDB/Memcached remain experimental.
