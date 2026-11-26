# 0.8.0 release candidate — staging checklist

**Status:** staging candidate, not published. This checklist prepares the
release; it does not authorize a tag, Phase B promotion or registry upload.
Published 0.7.2 remains the current release and its artifacts stay immutable.

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
| Staging version | `0.8.0` |
| C1 squash | `3ddedba3347f1050f86784d3bad14ad1ce331ca1` |
| C2 squash | `2aa9a031a5ad6c1a92759314d5e9d6172cb224e6` |
| C3 squash | `b57d32072eaf962e93279d4e5a7b5be799f0b23d` |
| C4 squash | `635201679ee1584c20e8c3f1f5c3fd80a6a2e74f` |
| Guards squash | `cc9539ffd45c98b0fa59012253f40d3d7a45d173` |
| Final source SHA | Pending merge and freeze |

## Risk and residual scope

The following are accepted for the 0.8.0 scope, with the documented limits;
none of the issues is closed by this release.

| Issue | 0.8.0 disposition |
| --- | --- |
| #53 hidden tenant/identity/context | Accepted with explicit app-responsibility warnings and safe examples; no automatic tenant detection. |
| #100 descriptive performance | Certification remains INCONCLUSIVE; the Redis/TCP concurrent p50 outlier needs focused diagnosis before publication; no performance claim. |
| #111 backend contract | Accepted for exact built-in adapters; custom/experimental limits remain documented. |
| #112 failure policy | Accepted as opt-in, default-off C3 scope; typed/custom/Pickle recovery remains out of scope. |
| #45 DynamoDB | Remains experimental; no TTL/close parity claim. |
| #102 Redis resilience | HA/TLS/Sentinel/Cluster profiles remain outside 0.8.0. |

The 0.8.0 notes must not claim automatic isolation, performance certification,
HA, real Memcached/DynamoDB parity or universal tenant safety.

## Staging gates

- [x] Functional scope freeze after C4; no new feature work.
- [x] Source version advanced to `0.8.0`; `PUBLISHED_VERSION` remains `0.7.2`.
- [x] C4 harness resolves the candidate version dynamically and keeps the
  published 0.7.2 baseline pinned by version and SHA-256.
- [x] Docs/version guard permits a newer source while public docs remain on
  0.7.2; publish markers are not updated early.
- [ ] Review release notes, candidate checklist and risk matrix.
- [ ] Focused Redis/TCP concurrent diagnostic (A/A and candidate comparison).
- [ ] Final maintainer GO for promotion.
- [ ] Final source SHA and manual Phase B 25/25 on that exact SHA.
- [ ] Fresh authenticated Dependabot delta and independent wheel/sdist review.
- [ ] TestPyPI exact-byte check.
- [ ] Separate PyPI authorization, annotated `v0.8.0` tag and GitHub Release.
- [ ] Published-byte verification, docs deployment and provenance record.

## Publication sequence

1. Merge this staging PR after review and the focused diagnostic decision.
2. Freeze the final `stable` SHA; run the manual Phase B on that SHA.
3. Verify wheel/sdist hashes and the fresh security delta independently.
4. Create the annotated `v0.8.0` tag and publish to TestPyPI.
5. Verify exact bytes, then obtain separate PyPI authorization.
6. Publish to PyPI, create the GitHub Release, deploy docs and record
   provenance in a follow-up promotion PR.

No tag or upload is part of the staging PR.
