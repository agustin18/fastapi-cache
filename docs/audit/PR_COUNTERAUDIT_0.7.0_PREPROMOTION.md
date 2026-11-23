# PR counteraudit 0.7 — before final version promotion

**This is a PREPROMOTION review prompt, not final release approval.**
Read the canonical 0.7 [risk register](../releases/RISK_REGISTER_0.7.0.md),
[scope decision](../releases/SCOPE_0.7.0_DECISION.md),
[release notes](../releases/RELEASE_NOTES_0.7.0.md),
[artifact checklist](../releases/RELEASE_CANDIDATE_0.7.0.md), and
[final-artifact handoff](COUNTERAUDIT_0.7.0_HANDOFF.md).

**Stable anchor before these PRs:** `0c306a67a6adb4ed098e96e70dd0da192c8fbf85`.
**PR under review:** #135 release risk + proportional no-claim performance
deferral.
The auditor must fetch the **current live PR HEAD SHA**, not use a hardcoded
SHAs from a moving branch. No source promotion to `0.7.0`,
tag, TestPyPI, PyPI, or release workflow is authorized by this review.

## First phase: adversarial review of merged runtime source

Compare exactly `v0.6.0...stable` plus the proposed PR diffs.
Prove that runtime changes relative to published 0.6.0 are ONLY
`fastapi_cache/backends/inmemory.py`, `.../redis.py` and
`fastapi_cache/decorator.py`, and inspect every runtime delta,
installed wheel tests and real 0.6.0 migration path. If the set
is different, **report it**; do not trust this prediction.

Falsify at least:
- TTL equality at deadline, bounded/unbounded, zero/negative, expired
  entry clock rollback, Redis EX=0 and missing TTL sentinel difference;
- Redis `get_with_ttl` type/bytes compatibility and any risk for consumers
  previously relying on a list; scoped `clear` and ownership;
- corrupt cached HIT with matching `If-None-Match`, invalid JSON/
  UTF-8/typed models, valid 304, raw response headers and ETag;
- failed backend GET/SET, explicit caller-owned redis-py retry policy
  versus default retries, actual Redis process down/restart (#133),
  concurrent requests and cancellation; no HA claim;
- PickleCoder against untrusted bytes **without executing a malicious
  payload in an unsafe environment**; require trusted-store warning;
- Authorization/Cookie bypass, returned private/no-store, Vary and
  key/tenant separation; hidden `request.state`/middleware and
  global process singleton are application-owned caveats, **not**
  auto-isolated features;
- Python 3.8–3.10 functional-legacy and 3.11–3.13 security-supported
  evidence; 3.14 explicitly not certified.

## Second phase: critique the PR decisions and future strategy

1. Inspect PR #135 for unintended release authorization, metadata
   changes, fabricated benchmark limits or hashes, unsubstantiated
   PASS claims, misleading 0.7 install snippets, stale `#133` status
   or `1d78154` as latest. Published pointer must be exactly
   `docs/releases/PUBLISHED_VERSION=0.6.0`. The PR must NOT change
   version from `0.7.0` or produce a tag.
2. #100 no-claim fixed-host deferral: the maintainer **accepted** this
   release-specific deferral on 2026-11-23. The independent reviewer must
   still verify the limited runtime delta, no performance feature, honest
   HTTP/Redis smoke and no material regression. If any fails, reject the
   deferral and require reproducible commands, hardware and a preregistered
   budget. GitHub-hosted metrics are not independent benchmarks. Redis 7.4
   #133 uses `Retry(NoBackoff(),0)`; it does not prove default redis-py
   outage latency. This is not a performance PASS.
3. No separate competitor PR is under review. Use the current stable
   roadmap for future-scope discussion; do not treat future dates as
   contractual targets.
4. Run `ruff check .`, pre-commit, site build and link checker,
   artifact/release-contract tests, supported and legacy Python/Redis
   smoke on the **exact PR HEADs**; independently inspect mandatory
   workflows and explain any missing credentials or NOT RUN evidence.
5. Re-run the **#135 diff** conceptually on latest `stable`; verify it
   does not create contradictory headings/links or claim a release.

## Expected independent report

For each item provide `PASS / FAIL / NOT RUN`, exact PR SHA, command
or file/line/CI run URL, severity `P0/P1/P2`, scope
(package-owned/application-owned/experimental/future feature), and
what evidence would convert NOT RUN to PASS.

Return separately:
- **PR merge recommendation** for #135: GO / CONDITIONAL / NO-GO.
- **Release readiness today**: should remain NO-GO until a *separate*
  final `0.7.0` source promotion PR is reviewed and merged, the
  source SHA is frozen, first-attempt **20** Phase B jobs succeed,
  exact wheel/sdist SHA-256 and fresh authenticated Dependabot delta
  are reviewed, and **independent final-artifact** audit returns GO.
- **Performance deferral verdict**: explicit ACCEPT/REJECT, not
  silently equated with "no regressions found".
- **Deferred backlog**: what remains for 0.8/0.9/1.0 and whether any
  unaddressed 0.7 P0/P1 is incorrectly postponed.

The reviewer must NOT merge, retag, publish, dispatch a privileged
release job, alter branch protection or claim final auditor consent.
