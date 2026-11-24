# fastapi-cache-stable 0.7.1 — release notes

**Published:** 2026-11-24 on PyPI. Install the exact released artifact with
`python -m pip install "fastapi-cache-stable==0.7.1"`.

## Metadata-only correction

0.7.1 has **no runtime, import or public API changes** from 0.7.0. It rebuilds
the distribution metadata from the corrected README so the PyPI long
description no longer advertises 0.6.0 as the latest stable release.

The runtime content is the 0.7.0 correctness line: inclusive InMemory TTL
expiry, decode-before-304 validation and the documented Redis
`get_with_ttl()` tuple contract. The 0.7.0 artifact remains immutable and its
own release notes still describe the original publication.

## Verification

Exact artifact hashes, Phase B evidence and registry verification are
recorded in the [release status](RELEASE_STATUS_0.7.1.md) and the
[GitHub release](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.1).
No performance, p95/p99, default Redis retry-latency or HA claim is made.
