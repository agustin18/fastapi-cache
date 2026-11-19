# 0.3.1 release status and evidence

**Status:** published, patch release complete **2026-11-19**.
This file is a post-release evidence summary, **not** a substitute for
reviewing present-day vulnerability status or a promise about downstream
application security.

## Immutable release identifiers

- PyPI package: [fastapi-cache-stable==0.3.1](https://pypi.org/project/fastapi-cache-stable/0.3.1/)
- GitHub Release: [v0.3.1](https://github.com/agustin18/fastapi-cache/releases/tag/v0.3.1)
- Annotated tag `v0.3.1` dereferences to:
  `f55d534e9ed99d74229d8c152bd5d21a26b65b43`
- `stable` matched the tagged release commit at publication time.
- [TestPyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44602555606):
  successful source preflight, Python 3.10/3.11/3.12/3.13 tests, build
  and Trusted Publishing.
- [Production PyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44603057293):
  seven successful jobs on the same commit.

## Published distribution digests

| File | SHA-256 |
|---|---|
| `fastapi_cache_stable-0.3.1-py3-none-any.whl` | `6b16cdac697e942f79a3202b03d00174768b4060335eada1190123cc31b3136c` |
| `fastapi_cache_stable-0.3.1.tar.gz` | `ef6ae11e043ebd53b0ecd5df526e6039494b80ecf75d925d3b78ae234d2e4b88` |

The same bytes were published to TestPyPI and PyPI and matched the
production workflow artifact. PyPI's signed provenance for both files is
bound to `publish.yml@refs/tags/v0.3.1`, commit
`f55d534e9ed99d74229d8c152bd5d21a26b65b43`, production run `44603057293`,
with transparency entries. `twine check` passed in the build job.
**Post-release documentation does not alter these immutable files.**

## Behavior and verification

- The release adds the conservative bypass from
  [#56](https://github.com/agustin18/fastapi-cache/pull/56): an endpoint
  that **explicitly declares `Request`** and uses the **default key
  builder** bypasses cache reads and writes. Endpoints with a reviewed
  custom key builder still cache.
- The executing local release agent reported a clean direct PyPI install
  with dependencies from PyPI, `pip check`, and a smoke test showing:
  ordinary response `MISS → HIT`; declared `Request` bypass with correct
  per-header responses; `Header(...)` parameter `MISS → MISS → HIT`.
  The sdist was installed and checked separately.
- The same agent reported **46 targeted `real-estate-arg` tests passed**
  with published 0.3.0 and with the 0.3.1 candidate, with unchanged
  HIT/MISS for its default-builder and `Request` + custom-builder routes.
  No route in that application combines a declared `Request` with the
  default builder. These are agent-reported consumer checks, not an
  archived independent CI job.
- A final authenticated Dependabot comparison before publication found
  the same **21 open alerts**, with no new or reopened alerts at that
  point. This is not a live feed of future findings.

## Residual limits

`0.3.1` mitigates only the explicit-`Request`/default-builder case.
`Vary`-aware caching, headers or state read by hidden dependencies and
middleware, ambient `contextvars`/application state, and per-user/tenant
key design remain open in
[#53](https://github.com/agustin18/fastapi-cache/issues/53). A custom key
builder is an explicit application responsibility, not a general safety
guarantee.

The 21 previously reviewed open GHSA remain documented as a bounded
`0.3.x` acceptance, not as fixed vulnerabilities or a promise about
consumer applications. The first stable `0.3.0` distribution remains
immutable and unchanged.

## Next work

See [ROADMAP.md](ROADMAP.md) and its linked issues for `0.3.2`
maintenance (uvicorn/dependency hygiene, Dependabot delta automation,
FIPS portability and experimental backend fixes) and the `0.4.0`
redis-client compatibility driver.
