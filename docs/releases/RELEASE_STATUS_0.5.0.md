# 0.5.0 release status and evidence

**Status:** published **2026-11-21**.
This is a post-release evidence record, not a guarantee about consumer applications.

## Release scope

Explicit opt-in HTTP header variation (`vary_headers`, #53/PR #81), including
versioned `:vary-v1:` keys and correct `Vary`/ETag/304 metadata on returned
responses; the factory-generated handler key isolation already shipped in
0.4.1; exact wheel/sdist migration and rollback evidence (#69); and the
release-scoped security decision recorded in #66. No unrelated feature was
added.

## Release identifiers and evidence

- Annotated tag `v0.5.0`: object `497f0ca8c481988b55b03e8ab3fc952f65c1b9fb`;
  peeled release commit `40c86d551b760315f3c6e99f383d6868c6294870`.
- [TestPyPI workflow 44852139879](https://github.com/agustin18/fastapi-cache/actions/runs/44852139879): success.
- [Production PyPI workflow 44852386994](https://github.com/agustin18/fastapi-cache/actions/runs/44852386994): success.
- [GitHub release](https://github.com/agustin18/fastapi-cache/releases/tag/v0.5.0): published.
- Wheel SHA-256 `7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449`;
  sdist SHA-256 `e5dfe2fb5a16cb790e98bfb5e57377d835adc55579b0fdf1cb1d0afbf610ba0b`.
- PyPI JSON reports those same hashes for `0.5.0`; the TestPyPI files
  also matched the same hashes.

## Pre-publication gates

- Exact-final-SHA Phase B [44851661315](https://github.com/agustin18/fastapi-cache/actions/runs/44851661315):
  **13/13 success** on stable `40c86d5`: Python 3.8–3.13 × wheel/sdist,
  Redis 7.4 seeding, candidate reader, targeted cleanup, physical package
  rollback to upstream 0.2.2 and independent InMemory/Vary consumer.
- Installed security profiles [44851664008](https://github.com/agustin18/fastapi-cache/actions/runs/44851664008):
  **7/7 success** on the same source SHA.
- Fresh authenticated Dependabot delta [44851667159](https://github.com/agustin18/fastapi-cache/actions/runs/44851667159):
  success, exit `0`, 120/120 records, **21 unchanged open**, no new,
  reopened or review-required findings, comparison complete, no blocking reasons.
- Stable CI and CodeQL after promotion: success.
- Risk decision: maintainer-authorized scoped 0.5.0 acceptance recorded in
  [#66 issuecomment-7055377740](https://github.com/agustin18/fastapi-cache/issues/66#issuecomment-7055377740).
  The 21 historical alerts remain open where applicable; they are not claimed
  fixed. Python 3.8–3.10 remain functional legacy only.

## Consumer verification

- A clean Python 3.12 installation from PyPI with the Redis extra completed
  `pip check`; `fastapi_cache.__version__` and
  `importlib.metadata.version("fastapi-cache-stable")` both reported `0.5.0`.
- TestPyPI artifacts were downloaded and verified against the Phase-B SHA-256
  values. A TestPyPI resolver install was not treated as a success because
  TestPyPI can expose incomplete dependency artifacts; the exact TestPyPI
  wheel was installed with PyPI dependencies and passed `pip check`.

The release does not certify arbitrary applications, Redis Cluster, TLS,
Sentinel, failover, or private authenticated rollback. See the
[version notes](RELEASE_NOTES_0.5.0.md), [migration guide](../../MIGRATION.md),
[security policy](../../SECURITY.md) and [support policy](../../SUPPORT.md).
