# 0.8.0 release status and provenance

**Published:** 2026-11-26 on [PyPI](https://pypi.org/project/fastapi-cache-stable/0.8.0/)
and the GitHub Releases page.

## Final release record

| Item | Evidence |
| --- | --- |
| Release type | Minor: opt-in app-scoped lifecycle/configuration, backend contracts, failure policies and installed isolation evidence; legacy default unchanged |
| Final source SHA | `92380fa915ab16837a12bf9634838aae14c315a4` |
| Annotated tag | `v0.8.0` (tag object `97092369a34d4bfa03001261677c8df2c92fc9d3`) |
| Phase B | [run 45870303265](https://github.com/agustin18/fastapi-cache/actions/runs/45870303265), attempt 1, 25/25 jobs |
| TestPyPI | [run 45874246420](https://github.com/agustin18/fastapi-cache/actions/runs/45874246420), hashes matched |
| PyPI | [run 45874503519](https://github.com/agustin18/fastapi-cache/actions/runs/45874503519), hashes matched |
| GitHub Release | [v0.8.0](https://github.com/agustin18/fastapi-cache/releases/tag/v0.8.0), created 2026-11-26 |
| Wheel SHA-256 | `4a7d200744424f88bfaee2a4b1fc6958e138aa86236c1906964d3cda41861bd1` |
| Sdist SHA-256 | `3eae593e5bc78f901c3b6ed7fd852b3910bb713a273e12cc9f5eecdac05e3d8b` |
| Phase B artifact | `migration-phase-b-0.8.0-distributions`, digest `sha256:df6afd570e24b15b91e1d9ee8c36ab0a694be63cf0e0be27c2c818d7f2b0f948` |
| Security delta | 120/120 records, 21 unchanged open, 0 new/reopened/review-required, comparison complete, exit 0 |

The wheel metadata long description is `README_PYPI.md`; it describes 0.8.0,
C1–C3 and the correct 0.8.0 install pins. The public README and documentation
pointed at 0.7.2 until publication and now point at 0.8.0.

## Scope and residual boundaries

0.8.0 ships the C1 app-scoped configuration/lifecycle, C2 built-in backend
contracts, C3 opt-in failure policies and C4 installed isolation evidence.
The legacy singleton remains the default. The C4 comparison is descriptive
and **not a performance certification**; the 0.8.0 re-run did not reproduce
the earlier 3.02× p50 outlier, but no latency or no-regression claim is made.

`#53` hidden tenant/identity context remains application-owned; `#100`
descriptive performance/certification remains open; `#111` and `#112` keep
their broader residual scopes; `#45` remains experimental and `#102`
advanced Redis profiles remain outside 0.8.0. Pickle requires trusted storage.
No automatic tenant isolation, HA, real Memcached/DynamoDB parity or
performance certification is claimed.
