# fastapi-cache-stable 0.5.0 — version notes

> **Availability and provenance:** verify the exact version at
> [PyPI](https://pypi.org/project/fastapi-cache-stable/) before installing.
> This document describes the 0.5.0 behavior; a source checkout or
> passing candidate PR is not proof of a published distribution.
> The manual release decision must be supported by
> [release-specific evidence](RELEASE_CANDIDATE_0.5.0.md).

## Changes since 0.4.1

- **Explicit HTTP variation (#53 / PR #81):** `@cache(vary_headers=(...))`
  opt-in with validated/canonicalized field names, versioned hashed
  `:vary-v1:` keys and generated HTTP `Vary` on MISS/HIT/304.
  Returned `JSONResponse` and `PickleCoder`-supported `Response`
  carry response metadata on the actual returned object. Legacy
  non-opt-in default keys remain byte-for-byte compatible.
- **Security and provenance gates (#66):** release-specific installed
  wheel/sdist audits, fresh authenticated Dependabot delta, and a
  recorded scoped residual-risk decision are required for any
  publication. Historical package scans or the earlier 21-alert
  assessment do not automatically authorize 0.5.0.
- **Exact-artifact migration (#69):** build the version-stamped wheel
  and sdist from an identical source SHA; verify independently installed
  consumers on Python 3.8–3.13, Redis 7.4 with redis-py 4.6,
  bounded ordinary-data rollback and a separate modern-client Vary
  consumer. The prior published-to-published
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
  hooks are outside the 0.5.0 release scope.

## Verification and release decision

The [Phase-B plan](../../audit/migration/PHASE_B_050_CANDIDATE_PLAN.md)
and [0.5.0 release gate record](RELEASE_CANDIDATE_0.5.0.md)
distinguish candidate PR checks from release-intended artifacts.
Any publication must follow the final `stable` SHA's wheel **and**
sdist hashes, reproducible Redis 7.4 migration/rollback, supported
modern installed-package security scans, a fresh authenticated
Dependabot delta and a release-specific risk decision (#66).
The annotation/tag, TestPyPI/PyPI and GitHub Release are all manual,
separately approved steps. Consult actual
[PyPI versions](https://pypi.org/project/fastapi-cache-stable/)
and signed release evidence; these notes alone do not assert that
a package was published or establish a security guarantee.
