# fastapi-cache-stable 0.8.0 — release notes (staging candidate)

**Status:** staged for 0.8.0; not published. The version, release notes and
risk record are being prepared for review. No tag, TestPyPI or PyPI artifact
is authorized by this document.

0.8.0 adds an **opt-in** application-scoped configuration and lifecycle,
internal backend capability contracts, opt-in failure policies and
installed-artifact isolation evidence. Existing `fastapi_cache` imports,
singleton initialization and default request behavior remain the compatible
default.

## User-visible changes

- **App-scoped configuration:** `CacheConfig`, `CacheHandle` and
  `CacheScopeError` allow one handle per FastAPI app, with explicit
  `scope_id`, deterministic physical keys and `start`/`aclose` lifecycle.
  Use `@cache(scope="app")`; the legacy singleton remains the default.
  App scope is opt-in, borrowed-only and supports exact `InMemoryBackend` and
  standalone `RedisBackend` (not Redis Cluster).
- **Failure policies:** `CacheFailurePolicy` adds independent opt-in flags
  for classified standalone Redis read transport errors
  (`strict_read`), conservative responses after a failed SET
  (`conservative_write`) and one uncached recompute for exact built-in JSON
  syntax/UTF-8 failures (`recover_json`). All flags default to `False`.
  Typed validation, tag conversion, custom-coder and Pickle errors keep their
  previous behavior; there is no automatic retry, repair or clear.
- **Backend contracts:** an internal descriptor records capabilities and
  ownership for exact built-in adapters. It does not add public backend API,
  change legacy `Backend` signatures or promote experimental providers.
- **C4 evidence:** installed wheel/sdist isolation, privacy matrix,
  cross-process scope checks and a descriptive 0.7.2 comparison are recorded.
  The comparison is **descriptive, not a performance certification**.

## Explicitly not added

No C5, no tag invalidation, no single-flight, no cache events, no stale
serving, no automatic tenant detection, no owned backend mode, no Redis
Cluster namespace clear, no HA/TLS/Sentinel certification and no real
Memcached/DynamoDB conformance claim. `#97`/`#49` remain planned for 0.9;
`#96`/`#50` follow later. `#103` is separate from 0.8.

## Compatibility

Python support is unchanged from 0.7.2: package metadata remains
`>=3.8,<3.15`; Python 3.8–3.10 are functional legacy profiles and 3.11–3.14
are the security target. No dependency bounds, import path, default key
format or singleton behavior changed. The scoped physical-key envelope is
opt-in and distinct from legacy keys.

## Security and operational boundaries

`#53` remains open: app scope does not automatically discover tenant,
authorization, locale or arbitrary request context. Use a validated
identity-aware key builder or explicit bypass; the C4 evidence includes a
negative hidden-context example. `#100` remains open: the C4 comparison is
descriptive and includes an unresolved Redis/TCP concurrent p50 outlier; no
latency, p95/p99, HA or no-regression claim is made. `#111`, `#112`, `#45`
and `#102` remain open for their broader residual scopes. Pickle requires
trusted storage; an ETag is not integrity or authorization.

## Evidence and publication state

The C4 evidence is recorded in `C4_EVIDENCE_PROTOCOL.md` and the C4 workflow
artifact. Final source SHA, Phase B, security delta, exact artifact hashes,
TestPyPI/PyPI and provenance are **pending separate release gates**. Do not
reuse the C4 candidate artifact as publication evidence; the final Phase B
must build the exact released source.
