# 0.7.1 release status and provenance

**Published:** 2026-11-24 on [PyPI](https://pypi.org/project/fastapi-cache-stable/0.7.1/)
and [GitHub Releases](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.1).

## Final release record

| Item | Evidence |
|---|---|
| Release type | Metadata-only correction over 0.7.0; no runtime changes |
| Final source SHA | `c6f46da82595c808866c9b944a5f931e07ceeb4b` |
| Annotated tag | `v0.7.1` (tag object `6fda616aef8080c5ed42de582233940cd9fede16`) |
| Phase B | [run 45302769038](https://github.com/agustin18/fastapi-cache/actions/runs/45302769038), attempt 1, 20/20 jobs |
| TestPyPI | [run 45303059177](https://github.com/agustin18/fastapi-cache/actions/runs/45303059177), hashes matched |
| PyPI | [run 45303318025](https://github.com/agustin18/fastapi-cache/actions/runs/45303318025), hashes matched |
| Wheel SHA-256 | `54d64e3f24110f434d2a1b765006e528302d5550ad0b4ce20b8eb706a49e9aa3` |
| Sdist SHA-256 | `c3fa245c9212ec292c43523e1402baad75da4571bbac0832380020c2205426d5` |
| Security delta | Passed in the authenticated PyPI publication workflow |

The 0.7.0 runtime is unchanged. This release rebuilds the PyPI long
description from the corrected README, which removes the stale 0.6.0
project-page text. The 21 open Dependabot alerts remain classified as
application or legacy conditional; this metadata-only patch makes no new
runtime or security claim.

The previous `0.7.0` record remains immutable. This release makes no
performance, p95/p99, default Redis retry-latency or HA claim.
