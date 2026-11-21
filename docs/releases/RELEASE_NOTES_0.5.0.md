# fastapi-cache-stable 0.5.0 — release candidate notes

> **Status: PREPUBLICATION DRAFT.** The latest published version is
> [0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/).
> These notes describe the proposed 0.5.0 artifact, not a live PyPI
> distribution. Do **not** install an unapproved 0.5.0 from an arbitrary
> package index or create a tag based on these notes.

## Scope staged after published 0.4.1

- **Explicit HTTP variation (#53 / PR #81):** `@cache(vary_headers=(...))`
  opt-in with validated/canonicalized field names, versioned hashed
  `:vary-v1:` keys and generated HTTP `Vary` on MISS/HIT/304.
  Returned `JSONResponse` and `PickleCoder`-supported `Response`
  carry response metadata on the actual returned object. Legacy
  non-opt-in default keys remain byte-for-byte compatible.
- **Security and provenance gates (#66):** existing release Dependabot
  delta and installed wheel/sdist profiles provide evidence; the
  final, fresh release-specific assessment and scoped residual-risk
  decision have **not** been completed or authorized by this PR.
- **Published-to-candidate migration (#69):** stage an exact SHA,
  version-stamped wheel and sdist; verify independent installed
  consumers on Python 3.8–3.13, Redis 7.4 with redis-py 4.6
  migration and safe ordinary-data rollback; add a separate
  modern-client Vary consumer. The prior published-to-published
  0.2.2 → 0.4.1 golden regression remains frozen as an independent
  historical comparison.
- **CI, Redis and docs maintenance (#67/#68/#78–#80):** carry forward
  the already-shipped 0.4.1 factory-key isolation, release safety
  controls, test isolation and documentation corrections. These are
  **not** newly invented 0.5.0 fixes.

## Preserved compatibility

The distribution is `fastapi-cache-stable`, import `fastapi_cache`.
Python metadata remains `>=3.8,<3.14`; Python 3.8–3.10 is a
**functional-only legacy migration bridge**, not security-maintained.
Production security work targets server-side Python 3.11–3.13.
The Redis client range remains Python-conditional and includes a
tested 4.6.0 migration path. The exported `default_key_builder` and
ordinary unwrapped module-level handler keys are unchanged.

## Migration and security warnings

- Upgrade by **removing `fastapi-cache2` first**: never co-install
  the two distributions, which expose the same `fastapi_cache` module.
- Untrusted/authenticated responses are not protected merely by
  `vary_headers`: `X-API-Key` is syntactically allowed but is not
  recognized by the standard Authorization/Cookie bypass. Validate
  identity, tenant and permissions and use a complete custom builder
  or disable private caching. Client-controlled high-cardinality header
  values can exhaust backend capacity.
- Previously stored private entries, ambiguous generated-route keys
  and incompatible special-type markers may require scoped namespace
  rotation/cleanup. Raw HTTP `Vary` alone does not partition the
  internal Redis/InMemory cache. `PickleCoder` must not decode
  untrusted cache bytes.
- The upstream `fastapi-cache2==0.2.2` rollback probe proves
  **ordinary compatible Redis data can be read**, not that re-enabling
  historical auth/private caching is safe. Gate rollback traffic and
  clean affected private namespaces first.
- `#49` exclude_params, `#54` bounded InMemory and `#50` event
  hooks are optional and **not** in this candidate.

## Verification and release decision

[Phase-B plan](../../audit/migration/PHASE_B_050_CANDIDATE_PLAN.md)
and [0.5.0 release checklist](RELEASE_CANDIDATE_0.5.0.md)
list the evidence still needed. A green PR matrix on its HEAD is
**preliminary**. Re-run against the **merged final stable commit**
and exact release-intended wheel/sdist, attach SHA-256, check modern
installed security profiles and freshly authenticated Dependabot
delta (#66), review residual risks, and obtain an explicit maintainer
decision **before any v0.5.0 tag/TestPyPI/PyPI**.

No release date or security approval is implied by these notes.
