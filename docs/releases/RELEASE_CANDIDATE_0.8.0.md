# 0.8.0 release candidate — promotion checklist

**Status:** published 2026-11-26. This checklist is retained as the final
pre-release and promotion record. The immutable `v0.8.0` source remains
`92380fa915ab16837a12bf9634838aae14c315a4`; later docs/provenance commits do not
change the released artifact.

## Scope

- C1 app-scoped configuration and lifecycle (#99 / #148).
- C2 built-in backend capability and ownership contracts (#111 / #149).
- C3 opt-in failure and serialization policies (#112 / #150).
- C4 installed isolation and descriptive performance evidence (#53/#100 / #151).
- Pre-release guards for candidate-version resolution and docs/version
  comparison (#152).
- No new runtime features after C4, no C5 and no expansion of #96/#50/#97/#49/#98.

## Included source identity

| Item | Value |
| --- | --- |
| Promotion version | `0.8.0` |
| Staging merge | `87afab0501106b3dd064b1f0c7c354b12f94a314` |
| Promotion merge | `dd383ad` |
| C1 squash | `3ddedba3347f1050f86784d3bad14ad1ce331ca1` |
| C2 squash | `2aa9a031a5ad6c1a92759314d5e9d6172cb224e6` |
| C3 squash | `b57d32072eaf962e93279d4e5a7b5be799f0b23d` |
| C4 squash | `635201679ee1584c20e8c3f1f5c3fd80a6a2e74f` |
| Guards squash | `cc9539ffd45c98b0fa59012253f40d3d7a45d173` |
| Final source SHA | `92380fa915ab16837a12bf9634838aae14c315a4` |
| Annotated tag | `v0.8.0` (tag object `97092369a34d4bfa03001261677c8df2c92fc9d3`) |
| GitHub Release | https://github.com/agustin18/fastapi-cache/releases/tag/v0.8.0 |

## Risk and residual scope

The following are accepted for the 0.8.0 scope, with the documented limits;
none of the issues is closed by this release.

| Issue | 0.8.0 disposition |
| --- | --- |
| #53 hidden tenant/identity/context | Accepted with explicit app-responsibility warnings and safe examples; no automatic tenant detection. |
| #100 descriptive performance | Certification remains INCONCLUSIVE. The #153 0.8.0 re-run did not reproduce the 3.02x p50 outlier (p50 -0.52%, p95 -1.00%, p99 -0.85%, throughput +0.55%); the ~9ms regime moved to scoped-off. Maintainer decision: accept the descriptive residual and defer the focused A/A; #100 remains open; no performance claim. |
| #111 backend contract | Accepted for exact built-in adapters; custom/experimental limits remain documented. |
| #112 failure policy | Accepted as opt-in, default-off C3 scope; typed/custom/Pickle recovery remains out of scope. |
| #45 DynamoDB | Remains experimental; no TTL/close parity claim. |
| #102 Redis resilience | HA/TLS/Sentinel/Cluster profiles remain outside 0.8.0. |

The 0.8.0 notes must not claim automatic isolation, performance certification,
HA, real Memcached/DynamoDB parity or universal tenant safety.

## Promotion gates

- [x] Functional scope freeze after C4; no new feature work.
- [x] Source version advanced to `0.8.0`; `PUBLISHED_VERSION` updated to `0.8.0` after verified publication.
- [x] C4 harness resolves the candidate version dynamically and keeps the
  published 0.7.2 baseline pinned by version and SHA-256.
- [x] Docs/version guard permits a newer source while public docs remain on
  0.7.2; publish markers are not updated early.
- [x] Review release notes, candidate checklist and risk matrix.
- [x] TCP decision recorded: accept descriptive residual, defer A/A, #100 open.
- [x] External auditor verification of the promotion diff and C4 evidence.
- [x] Final maintainer GO for tag and publication.
- [x] Final source SHA and manual Phase B 25/25 on that exact SHA.
- [x] Fresh authenticated Dependabot delta and independent wheel/sdist review.
- [x] TestPyPI exact-byte check.
- [x] Separate PyPI authorization, annotated `v0.8.0` tag and GitHub Release.
- [x] Published-byte verification.
- [ ] Docs deployment and provenance record (post-release PR).

## Publication sequence

1. Merged the promotion PR; final source frozen at `92380fa`.
2. Phase B passed 25/25 on the final source.
3. Wheel/sdist hashes and the fresh security delta were verified independently.
4. Created annotated `v0.8.0` and published to TestPyPI.
5. Verified exact bytes, then obtained separate PyPI authorization.
6. Published to PyPI and created the GitHub Release.
7. Post-release docs/provenance PR deploys docs and records the final state.

No tag or upload was part of the promotion PR; no rebuild occurred.
