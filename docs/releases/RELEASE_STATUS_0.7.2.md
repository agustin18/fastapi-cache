# 0.7.2 release status and provenance

**Status:** promotion prepared 2026-11-25. The final manual Phase B on the
frozen stable SHA, annotated tag, TestPyPI/PyPI runs and SHA-256 values are
pending and will replace the provisional entries below after publication.

## Final release record

| Item | Evidence |
|---|---|
| Release type | Compatibility patch; standard CPython 3.14 support; no runtime/API changes |
| Source | `0.7.2` on `stable`; final SHA frozen after promotion |
| Phase B PR evidence | [run 45719694381](https://github.com/agustin18/fastapi-cache/actions/runs/45719694381), attempt 1, 25/25 (pre-merge) |
| Final Phase B | Pending manual first-attempt run on the final stable SHA |
| Annotated tag | Pending `v0.7.2` |
| TestPyPI | Pending exact-byte publication and digest check |
| PyPI | Pending exact-byte publication and digest check |
| Wheel SHA-256 | Pending final artifacts |
| Sdist SHA-256 | Pending final artifacts |
| Security delta | Pending authenticated PyPI publication workflow |

The 0.7.2 runtime is the 0.7.1 runtime. This release extends the published
Python metadata to `>=3.8,<3.15`, includes standard CPython 3.14 and the Redis
extra through 3.14. No performance, p95/p99, Redis retry-latency or HA claim is
made. The 21 open Dependabot alerts keep their existing classification.
