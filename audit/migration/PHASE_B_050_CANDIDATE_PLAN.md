# #69 Part B — 0.5.0 exact candidate artifacts and rollback

**Status:** candidate workflow proposed in PR #82. This file is
the test contract, **not an audit conclusion** and not a PyPI approval.
The currently published version is still 0.4.1.

## Why a separate phase B is required

Phase A tested **published 0.2.2 and published 0.4.1** in separate
clean venvs. Phase B must not silently substitute either for the
candidate containing #81's opt-in header Vary API. The release
candidate's actual wheel and sdist must be tested on the same
source SHA that will be tagged or published.

Workflow: [migration-candidate-phase-b.yml](../../.github/workflows/migration-candidate-phase-b.yml).

## Provenance and artifact integrity

- Checkout exactly PR `head.sha` rather than GitHub's synthetic
  pull-request test merge SHA; run via manual dispatch on the
  final merged `stable` SHA. Verify `git rev-parse HEAD`.
- Build one `fastapi_cache_stable-0.5.0-*.whl` and one
  `fastapi_cache_stable-0.5.0.tar.gz` with `python -m build`.
  Validate wheel METADATA name/version/import, tarball pyproject
  version, and `twine check`.
- Record both SHA-256 values, source commit and run ID. Upload the
  **actual files** as one 90-day CI artifact. Each consumer downloads
  precisely that artifact and checks the SHA-256 manifest and
  source provenance before installation; no rebuilding from checkout
  in consumers.
- Capture every installed environment's `pip freeze`, `pip check`,
  migration logs and exact version into 90-day lane artifacts.
  Evidence expires after retention; archive it for release review.

## Tested matrix and intentional boundaries

- 12 migration lanes: 2 artifacts × Python 3.8, 3.9, 3.10, 3.11,
  3.12 and 3.13 against **dedicated Redis 7.4**.
- Upstream writer: immutable PyPI `fastapi-cache2==0.2.2` wheel
  in one clean venv, Redis client `redis==4.6.0`. Candidate:
  the exact CI wheel/sdist, in a separate clean venv with
  `redis==4.6.0`. No environment ever contains both packages.
- Pinned reference framework by interpreter: FastAPI 0.111.1 and
  Pydantic 1.10.27 on Python 3.8–3.10; FastAPI 0.111.1 and
  Pydantic 2.8.2 on 3.11–3.12; FastAPI 0.115.12 and
  Pydantic 2.11.7 on 3.13. This is a **bounded test profile**,
  not broad compatibility with every past/current FastAPI version.
- Replay the existing Redis legacy seed, candidate reading of
  ordinary TTL/golden key, targeted private/special namespace clear,
  unrelated namespace preservation, `Cache-Control: no-cache`
  refresh, then **uninstall** the candidate and reinstall upstream
  0.2.2 in that same venv for ordinary-data rollback. Private
  caching is **not safe** simply because rollback ordinary-data
  parity passes.
- Build an independent clean consumer of the same candidate file
  and run `candidate_050_inmemory_probe.py` (module-level key
  golden, GET MISS/HIT/304, HTTP `Vary` returned `JSONResponse`,
  explicit Request bypass, non-200 failure bypass) and
  `redis_vary_probe.py` (real Redis tenant-variant differentiation
  and returned `Response` with JsonCoder and PickleCoder).
  Redis-py 8.1.0 is tested on Python 3.10–3.13, redis-py 4.6
  on 3.8–3.9; extra Redis client/server combinations belong to
  the existing dedicated Redis implementation matrix.

## Remaining decisions (cannot be auto-marked complete)

- These tests do not certify arbitrary consumer business apps,
  hidden identity or proxy-header trust, Memcached/DynamoDB real
  services, distributed deployments, TLS/Sentinel/Cluster, or
  actual safe restoration of legacy private caching.
- 0.5.0 may remain in a draft PR or even have version metadata
  on `stable` without being an approved/public release.
- Repeat exact-artifact matrix after any candidate HEAD change
  **and after final merge**. Recheck `#66` audited modern
  wheel/sdist, live authenticated Dependabot delta and explicit
  release-scoped risk acceptance before manual publication.

See [published Phase A](PUBLISHED_022_TO_041_PHASE_A.md),
[0.5.0 checklist](../../docs/releases/RELEASE_CANDIDATE_0.5.0.md),
[SECURITY](../../SECURITY.md) and [MIGRATION](../../MIGRATION.md).
