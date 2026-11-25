# 0.7.2 release candidate — PUBLISHED 2026-11-25

The 0.7.2 release was published on 2026-11-25; this checklist is retained as
the completed release record. #51 is the only release feature scope. The
diagnostic qualification passed in #142 and the PR Phase B run `45719694381`
passed 25/25.

## Scope

- [x] Standard CPython 3.14 diagnostic wheel/sdist, real Redis 7.4, functional
  control and installed security qualification passed; optional fake clients
  passed. No runtime changes needed in the tested scope.
- [x] Source metadata `>=3.8,<3.15`, Redis markers, classifiers and generated
  lock reconciled; dependency delta reviewed; legacy lanes preserved.
- [x] Complete PR CI including 3.14 source and exact-artifact profiles.
- [x] Phase B PR evidence: 25 mandatory jobs (1 build, 14 Redis migration and
  rollback wheel/sdist jobs, 10 installed security profiles), run
  `45719694381`, attempt 1.
- [x] Independent diff review; no API, key, ETag, serialization or behavioral
  change; no dependency major upgrade or weakened gates.
- [x] Changelog regenerated from staged fragments in the promotion PR;
  `PUBLISHED_VERSION` was moved to 0.7.2 for the final artifact.

## Final release gates — COMPLETED

- [x] Frozen final stable SHA `8cb3f4fe82e3d02cb6ae7874c03d82f94d9df822`;
  manual first-attempt Phase B [run 45723827682](https://github.com/agustin18/fastapi-cache/actions/runs/45723827682),
  25/25 jobs; exact source, run, provenance and wheel/sdist hashes reviewed.
- [x] Fresh authenticated Dependabot delta passed in the PyPI publication
  workflow; the 21 reviewed alerts keep their classification; no new
  package-owned unresolved P0/P1.
- [x] Exact-artifact technical/security review and maintainer GO for v0.7.2.
- [x] Annotated tag `v0.7.2` on the frozen source; TestPyPI
  [run 45724244766](https://github.com/agustin18/fastapi-cache/actions/runs/45724244766)
  and PyPI
  [run 45724514804](https://github.com/agustin18/fastapi-cache/actions/runs/45724514804)
  published the same bytes; hashes matched.
- [x] Registry hashes, release notes, release status and docs publication
  pointer verified after production publication.

3.8–3.10 stay functional legacy only; the 3.11–3.14 security scope is conditional
on exact installed audits. Free-threaded 3.14t, Python 3.15, real
Memcached/DynamoDB conformance and new APIs remain outside this release.
