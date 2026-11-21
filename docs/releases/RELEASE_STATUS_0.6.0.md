# 0.6.0 release status and provenance

**Published on 2026-11-21.** This release supersedes published 0.5.0. PyPI: <https://pypi.org/project/fastapi-cache-stable/0.6.0/>.
TestPyPI: <https://test.pypi.org/project/fastapi-cache-stable/0.6.0/>.

## Final release record

| Item | Evidence |
|---|---|
| Final source SHA | `6b6924a61bbcc0ba602da514accb4c563806742f` |
| Annotated tag | `fa46e9ddab1d9ae8fcf38094a25f4d0442950bc6` -> peeled `6b6924a61bbcc0ba602da514accb4c563806742f` |
| Final Phase B | [run 44944620217](https://github.com/agustin18/fastapi-cache/actions/runs/44944620217), attempt 1, 20 of 20 jobs |
| Wheel SHA-256 | `60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e` |
| Sdist SHA-256 | `c0f8f8b872d337b432afd1340dbe8b9b1800933dfed9c3f3c14ad232153408f2` |
| TestPyPI | [run 44944911074](https://github.com/agustin18/fastapi-cache/actions/runs/44944911074), hashes matched |
| PyPI | [run 44945090377](https://github.com/agustin18/fastapi-cache/actions/runs/44945090377), security delta passed |
| Maintainer acceptance | [#92](https://github.com/agustin18/fastapi-cache/issues/92) and [#53](https://github.com/agustin18/fastapi-cache/issues/53) |
| GitHub release | <https://github.com/agustin18/fastapi-cache/releases/tag/v0.6.0> |

The `112f2ac171ed8adc145cb22303ae3a368a1ef1e6` tree produced the same
wheel and sdist hashes. Commit `6b6924a` adds only the remote-tag
preflight fix required by the publish workflow; the package tree is
unchanged. The final Phase B above is the authoritative run for this
release.

## Candidate record (retained for audit)

- #104 reviewed HEAD `8ff49aa28632e87db0586bec771483910ebf5554`:
  80/80 jobs over nine workflows. [CI 29/29](https://github.com/agustin18/fastapi-cache/actions/runs/44933031194),
  [Phase B 20 of 20](https://github.com/agustin18/fastapi-cache/actions/runs/44933031159),
  [Redis 17/17](https://github.com/agustin18/fastapi-cache/actions/runs/44933031181),
  [installed diagnostics 7/7](https://github.com/agustin18/fastapi-cache/actions/runs/44933031166),
  [legacy parity 2/2](https://github.com/agustin18/fastapi-cache/actions/runs/44933031162).
- Merged candidate: `b5d9e125e49ae54b578c1e2b98f33bb9b5f452c0`.
- [Incremental review](https://github.com/agustin18/fastapi-cache/pull/104#issuecomment-7067089035).

## Scope and limitations

The release covers opt-in bounded InMemory and the 0.6.0 authentication /
HTTP cache corrections. It is not an independent certification, a
universal safety claim, or a transferable approval.

Application/infrastructure-owned residual risk remains documented in
[#53](https://github.com/agustin18/fastapi-cache/issues/53): hidden
identity in ContextVar/middleware/tenant state, custom auth headers,
proxies and intermediaries, unbounded cardinality, legacy private Redis
contents and process-global configuration. Any package-owned
unmitigated cross-tenant reproduction remains a blocker for future
releases.
