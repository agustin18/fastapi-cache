# 0.7.2 release candidate — STAGING / NOT APPROVED

The latest published release is [0.7.1](RELEASE_STATUS_0.7.1.md).
Staging starts from `ed50df9a81bc3e2137575a0ce400e303eee21936`. #51 is the only release feature scope.
The [diagnostic qualification](../audit/PYTHON_3_14_QUALIFICATION.md) passed
in #142. This does not qualify the exact 0.7.2 release artifacts.

## Scope

- [x] Standard CPython 3.14 diagnostic wheel/sdist, real Redis 7.4, functional
  control and installed security qualification passed; optional fake clients
  passed. No runtime changes needed in the tested scope.
- [ ] Source metadata `>=3.8,<3.15`, Redis markers, classifiers and generated
  lock reconciled; review dependency delta and preserve legacy lanes.
- [ ] Complete PR CI including 3.14 source and exact-artifact profiles.
- [ ] Phase B PR evidence: 25 mandatory jobs (1 build, 14 Redis migration and
  rollback wheel/sdist jobs, 10 installed security profiles). Explicit modern
  3.14 FastAPI/Pydantic/httpx/httpx2 lane; if the upstream legacy wheel fails
  on 3.14, stop and review a cross-interpreter design, not a skipped PASS.
- [ ] Independent diff review; no API, key, ETag, serialization or behavioral
  change; no dependency major upgrade or weakened gates. Abort and re-scope
  if required.
- [ ] Regenerate the changelog from staged fragments in a separate promotion
  PR; source 0.7.2 is not publication. PUBLISHED_VERSION remains 0.7.1.

## Final release gates — NOT RUN

- [ ] Freeze final merged stable SHA after promotion. Run new manual first-attempt
  Phase B; all 25 unique required jobs must succeed. Review exact source/run,
  provenance, installed runtime profiles and both wheel/sdist SHA-256 values.
- [ ] Fresh authenticated Dependabot delta against accepted baseline; review
  new/reopened/material findings and generated lock changes. No package-owned
  unresolved P0/P1.
- [ ] Exact-artifact technical/security review and explicit maintainer GO.
- [ ] Separate approval for annotated v0.7.2 tag on the frozen source, then
  TestPyPI exact bytes, digest verification and separately authorized PyPI
  publication of the same pair with fresh security delta.
- [ ] Verify registry hashes, clean installations, release notes and docs
  publication pointer after production publication.

3.8–3.10 stay functional legacy only; proposed 3.11–3.14 security scope is
conditional on exact installed audits. Free-threaded 3.14t, Python 3.15,
real Memcached/DynamoDB conformance and new APIs are outside scope.
No tag, package upload or release authorization is implied by staging.
