# 0.6.0 release status and provenance

**Promotion prepared, not published.** Latest published version remains
[0.5.0](RELEASE_STATUS_0.5.0.md). No tag or index upload authorized.

## Candidate record (not the final release)

- #104 reviewed HEAD `8ff49aa28632e87db0586bec771483910ebf5554`:
  80/80 jobs over nine workflows. [CI 29/29](https://github.com/agustin18/fastapi-cache/actions/runs/44933031194),
  [Phase B 20/20](https://github.com/agustin18/fastapi-cache/actions/runs/44933031159),
  [Redis 17/17](https://github.com/agustin18/fastapi-cache/actions/runs/44933031181),
  [installed diagnostics 7/7](https://github.com/agustin18/fastapi-cache/actions/runs/44933031166),
  [legacy parity 2/2](https://github.com/agustin18/fastapi-cache/actions/runs/44933031162),
  remaining CodeQL, docs, changelog, title 5/5.
- Merged candidate: `b5d9e125e49ae54b578c1e2b98f33bb9b5f452c0`.
- [Incremental review](https://github.com/agustin18/fastapi-cache/pull/104#issuecomment-7067089035):
  corrective delta favorable; final acceptance remains separate.
- [Notes](RELEASE_NOTES_0.6.0.md), [checklist](RELEASE_CANDIDATE_0.6.0.md),
  [risk record](../../audit/security/RELEASE_RISK_DISPOSITION_0.6.0.md).

## Final evidence (pending)

| Item | Evidence |
|---|---|
| Final promotion merge SHA, CI, Towncrier verification | Pending |
| Manual stable Phase B first attempt (20/20) | Pending |
| Exact wheel SHA-256 | Pending |
| Exact sdist SHA-256 | Pending |
| Downloaded bytes, provenance and retrieval preflight | Pending |
| Fresh authenticated Dependabot delta | Pending |
| Maintainer acceptance of A1–A6 and P1–P4 gates | Pending |
| Annotated tag and peeled commit | Not authorized |
| TestPyPI exact hashes and smoke install | Not authorized |
| PyPI exact hashes and smoke install | Not authorized |

The authoritative live ledger is [#92](https://github.com/agustin18/fastapi-cache/issues/92)
and scoped privacy acceptance in [#53](https://github.com/agustin18/fastapi-cache/issues/53).
After final merge record immutable SHA and hashes there without changing
the reviewed source. After actual publication, update this record and
public install pins in a docs-only follow-up. No independent adoption or
production certification is claimed.
