# 0.7.0 release-candidate checklist — NOT APPROVED

**2026-11-23 status: NO-GO.** No 0.7.0 release artifact, source freeze,
tag, TestPyPI/PyPI upload, or independent final counteraudit. The latest
published version is 0.6.0 with [immutable release evidence](RELEASE_STATUS_0.6.0.md).
Every unchecked box is an unsatisfied gate, not a claimed completion.
See the [0.7 narrow-scope decision proposal](SCOPE_0.7.0_DECISION.md)
for explicit boundaries; the proposal is not maintainer acceptance or release GO.
Merged #130/#131/#132 do not constitute a frozen final candidate.

## 1. Scope and behavioral contracts

- [ ] #111 **narrow #123 merged** (TTL equality, zero/negative and clock
      rollback characterized, absent from 0.6.0); still approve the wider
      InMemory/Redis/Memcached/DynamoDB clear/close/ownership/cancellation
      capability and expiry/error contract with installed-artifact evidence.
- [ ] #112 **narrow #124 merged** (decode before ETag 304, fail closed,
      not in published 0.6.0). Still approve policy for coder encode/decode,
      backend GET/SET, cancellation, invalidation/retry, and Pickle trusted-store
      limitation; test negative security/concurrency paths.
- [x] #99/#103 **scope decision for 0.7**: new per-app and non-HTTP
      APIs are deferred beyond 0.7; singleton/tenant limitations documented.
      Neither RFC's future implementation is approved or the issues closed.
- [ ] #100 fixed independent hardware, real HTTP network, Redis
      failure profiles, and **regression budgets signed before measurement**;
      historical AB/BA comparator is not a performance certification.
- [ ] Approve/reject the narrow-scope proposal: **new #96 single-flight,
      #50 typed events and #99/#103 public APIs do not ship in 0.7.0**.
      #102 may supply standalone Redis failure *test evidence*, but no new
      resilience policy, HA/TLS/Cluster guarantee or public feature ships
      without separately approved tests and contracts. Keep issues open.
- [ ] Preserve import `fastapi_cache`, ordinary key identity,
      compatibility of documented flows and real migration rollback.
      Redis Cluster namespace clearing remains unsupported; Memcached
      and DynamoDB experimental; Python 3.14 unqualified.

## 2. Candidate source and documentation

- [ ] Approved PRs merged; source currently `0.7.0.dev0` (#130 merged).
      Prepare a separate final promotion PR setting `0.7.0`, release notes,
      Towncrier changelog and candidate compatibility notes, **without
      incorrectly changing published `docs/releases/PUBLISHED_VERSION`
      (remains `0.6.0` until registry publication)**. No history overwrite.
- [ ] **Frozen final stable source SHA: TBD.** No unreviewed source edits afterward.
- [ ] Full supported and legacy Python matrix plus real Redis 7.4,
      installed wheel/sdist compatibility, security, privacy and TTL tests green.
- [ ] README, COMPATIBILITY, MIGRATION, SUPPORT, SECURITY, docs site,
      changelog and examples distinguish **published 0.6.0** from
      **candidate unreleased 0.7.0**; no draft behavior advertised as shipped.
- [ ] Docs-site build and internal/external link checks passed. Site
      deployment does not imply package publication.

## 3. New exact-final-SHA Phase B

- [ ] Manual final-source workflow run **first attempt**; independently
      inspect all **20 unique mandatory jobs** (build + 12 Redis
      migration/rollback + 7 installed security profiles).
- [ ] One wheel and one sdist only, correct distribution version and
      provenance. Independently download and compute **both SHA-256**.
      Confirm workflow path, frozen source SHA, run/attempt/job manifest.
- [ ] Clean installed wheel/sdist, `pip check` and no dual `fastapi-cache2`
      namespace collision; golden cache keys and rollback verified.
- [ ] Fresh authenticated Dependabot/lock delta; each material new high
      or critical finding fixed or explicitly reviewed with evidence.
- [ ] Independent security/privacy/performance/release **counteraudit of
      exact final candidate** returned GO; rerun affected audits after
      material changes. Use [handoff](../audit/COUNTERAUDIT_0.7.0_HANDOFF.md).
      PR-level 77/77 CI is not a final-artifact audit.

## 4. Registry promotion — separate explicit approval required

- [ ] Maintainer expressly approves version, frozen source SHA, scope,
      security deferrals, both artifact hashes and each publication action.
- [ ] Annotated `v0.7.0` tag peels to final frozen stable source SHA.
- [ ] TestPyPI publishes the **exact Phase B pair without rebuild** using
      reviewed environment/OIDC/trusted-publisher restrictions.
- [ ] Production PyPI checks TestPyPI hash parity and new security delta;
      publishes the **same bytes** without rebuild, with its own GO.
- [ ] Independently verify published PyPI wheel/sdist, install, version,
      hashes, metadata, rollback, docs and GitHub Release.
- [ ] Archive source SHA, tag object/target, all 20 job URLs, both hashes,
      security decisions, auditor verdict and explicit maintainer GO in
      future `RELEASE_STATUS_0.7.0.md`.

**DO NOT TAG OR PUBLISH** on the basis of this proposed checklist. A
separate final release decision is mandatory.
