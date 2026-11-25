# fastapi-cache-stable 0.7.2 — release notes

**Published:** 2026-11-25 on PyPI. Install the exact released artifact with
`python -m pip install "fastapi-cache-stable==0.7.2"`.

## Python 3.14 compatibility

0.7.2 is a compatibility release with **no runtime, import or public API
changes** from 0.7.1. It extends the published package metadata to
`>=3.8,<3.15` and includes standard CPython 3.14; the Redis extra keeps the
existing client bounds and extends the modern marker through 3.14.

Python 3.8–3.10 remain functional legacy only. The server-side security
target for 0.7.2 is CPython 3.11–3.14, subject to the exact installed-artifact
audits recorded in the release status. Memcached and DynamoDB remain
experimental; free-threaded 3.14t and Python 3.15 are outside this release.

## Verification

Exact artifact hashes, Phase B evidence and registry verification are recorded
in the [release status](RELEASE_STATUS_0.7.2.md) and the
[GitHub release](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.2).
No performance, p95/p99, Redis retry-latency or HA claim is made.
