# 0.7.2 release candidate — PROMOTION / PUBLICATION PENDING

The latest published release is [0.7.1](RELEASE_STATUS_0.7.1.md). 0.7.2 is
staged on `stable`; this promotion PR prepares the final source. #51 is the
only release feature scope. The diagnostic qualification passed in #142 and
the PR Phase B run `45719694381` passed 25/25. Final publication remains gated
on the manual Phase B on the frozen stable SHA, exact artifacts, tag,
TestPyPI/PyPI evidence and a separate publish authorization.

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
- [x] Changelog regenerated from staged fragments in this promotion PR;
  `PUBLISHED_VERSION` moves to 0.7.2 for the final artifact, while registry
  publication remains separately gated.

## Final release gates — PENDING

- [ ] Freeze final merged stable SHA after promotion. Run new manual first-attempt
  Phase B; all 25 unique required jobs must succeed. Review exact source/run,
  provenance, installed runtime profiles and both wheel/sdist SHA-256 values.
- [ ] Fresh authenticated Dependabot delta against the accepted baseline;
  review new/reopened/material findings and generated lock changes. No
  package-owned unresolved P0/P1.
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
