# 0.7.2 release status and provenance

**Published:** 2026-11-25 on [PyPI](https://pypi.org/project/fastapi-cache-stable/0.7.2/)
and [GitHub Releases](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.2).

## Final release record

| Item | Evidence |
|---|---|
| Release type | Compatibility patch; standard CPython 3.14 support; no runtime/API changes |
| Final source SHA | `8cb3f4fe82e3d02cb6ae7874c03d82f94d9df822` |
| Annotated tag | `v0.7.2` (tag object `d58e0e427d2bc291ce5667b9fc3000ba32a13f69`) |
| Phase B | [run 45723827682](https://github.com/agustin18/fastapi-cache/actions/runs/45723827682), attempt 1, 25/25 jobs |
| TestPyPI | [run 45724244766](https://github.com/agustin18/fastapi-cache/actions/runs/45724244766), hashes matched |
| PyPI | [run 45724514804](https://github.com/agustin18/fastapi-cache/actions/runs/45724514804), hashes matched |
| Wheel SHA-256 | `31257d8de8e5b36b13f50d233c72bf3a53d99b8eb3376264112be9072abf5fa0` |
| Sdist SHA-256 | `9990d37e9aada794447464c311885f144154309bca966dd0d3a412111db17fb3` |
| Security delta | Passed in the authenticated PyPI publication workflow |

The 0.7.2 runtime is the 0.7.1 runtime. This release extends the published
Python metadata to `>=3.8,<3.15`, includes standard CPython 3.14 and the Redis
extra through 3.14. No performance, p95/p99, Redis retry-latency or HA claim is
made. The 21 open Dependabot alerts keep their existing classification.
