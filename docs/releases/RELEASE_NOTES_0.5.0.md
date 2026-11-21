# fastapi-cache-stable 0.5.0 — version notes

> **Published 2026-11-21.** Wheel SHA-256
> `7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449`;
> sdist SHA-256 `e5dfe2fb5a16cb790e98bfb5e57377d835adc55579b0fdf1cb1d0afbf610ba0b`.
> See the [release status and provenance](RELEASE_STATUS_0.5.0.md) for
> workflows, tag identifiers and consumer checks.

## Changes since 0.4.1

- **Explicit HTTP variation (#53 / PR #81):** `@cache(vary_headers=(...))`
  opt-in with validated/canonicalized field names, versioned hashed
  `:vary-v1:` keys and generated HTTP `Vary` on MISS/HIT/304.
  Returned `JSONResponse` and `PickleCoder`-supported `Response`
  carry response metadata on the actual returned object. Legacy
  non-opt-in default keys remain byte-for-byte compatible.
- **Security and provenance gates (#66):** the release used exact-artifact
  installed wheel/sdist audits, a fresh authenticated Dependabot delta and a
  scoped residual-risk decision. The 21 historical alerts remain open where
  applicable; see the [release evidence](RELEASE_STATUS_0.5.0.md).
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

The exact-final-SHA Phase B matrix passed 13/13, the installed security
profiles passed 7/7, and the fresh authenticated Dependabot delta reported
21 unchanged open alerts with no new, reopened or review-required findings.
The release was tagged, tested on TestPyPI and published to PyPI manually.
See [status and provenance](RELEASE_STATUS_0.5.0.md) and the
[historical gate record](RELEASE_CANDIDATE_0.5.0.md). These notes do not
establish a security guarantee for arbitrary consumer applications.
