# Independent 0.7.0 counteraudit handoff — DRAFT / NOT SENT

**As of 2026-11-23: NO-GO.** No frozen 0.7.0 source SHA, release
artifact, tag, published registry upload or completed independent review.
This document prepares a future review request; it does **not** create
one or imply that an auditor has signed anything.

Published 0.6.0 anchor:
[release evidence](../releases/RELEASE_STATUS_0.6.0.md),
wheel SHA-256 `60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e`,
sdist SHA-256 `c0f8f8b872d337b432afd1340dbe8b9b1800933dfed9c3f3c14ad232153408f2`.
Never substitute those hashes for a 0.7.0 candidate.

## Open work the independent reviewer must treat as unresolved

- #120/#121/#122 merged (published-wheel smoke/full and 0.5/0.6 AB/BA).
  Historical Redis timing changes sign across hosted runners.
  [#100](https://github.com/agustin18/fastapi-cache/issues/100)
  has Draft #128 real loopback HTTP socket evidence; fixed independent
  hardware, Redis fault/recovery and pre-approved budgets remain.
- [#123](https://github.com/agustin18/fastapi-cache/pull/123)
  **merged** (`612e9d6`) for inclusive InMemory TTL; verify final candidate
  installed-artifact behavior, clock skew and Redis/experimental parity limits.
- [#124](https://github.com/agustin18/fastapi-cache/pull/124)
  **merged** (`4dc66ad`) for corrupt-HIT ETag/304; broader
  backend/coder policy, Pickle trust and recovery remain unresolved.
- [#99](https://github.com/agustin18/fastapi-cache/issues/99) and
  [#103](https://github.com/agustin18/fastapi-cache/issues/103)
  scope decision **deferred new app/non-HTTP APIs out of 0.7**; full
  designs remain unapproved. #96/#50/basic #102 have no implied clearance.
- [#110](https://github.com/agustin18/fastapi-cache/issues/110)
  version-neutral infrastructure exists, but no **final 0.7.0**
  Phase B, hash, tag or registry verification exists.

## Trigger for formal final-candidate contraaudit

Request final audit **only after** selected contracts are accepted,
functional PRs merged, exact baseline budgets approved and measured,
docs and security/privacy tests validated, and a candidate is frozen
to one stable SHA. Obtain first-attempt **20/20 Phase B** for exactly
that SHA (12 Redis migration/rollback + 7 installed security + build),
independent wheel/sdist hashes, provenance, fresh authenticated
Dependabot delta and complete installed-wheel/sdist evidence.

A **design-only** review of proposed RFCs may happen earlier; it is NOT
the final release candidate's independent GO.

## Exact evidence manifest — do not invent

| Required | Value |
|---|---|
| Frozen final stable source SHA | TBD |
| Selected 0.7.0 features and accepted deferrals | TBD |
| Candidate wheel filename / independent SHA-256 | TBD |
| Candidate sdist filename / independent SHA-256 | TBD |
| First-attempt full 20-job Phase B URL and job inventory | TBD |
| Python/Redis/dependency freeze, migration/rollback | TBD |
| Fixed independent hardware, budget approval before run, raw results | TBD |
| Real HTTP socket and fault/disconnect results | TBD |
| TTL/corrupt/auth/tenant/serialization/cancellation test provenance | TBD |
| Fresh Dependabot/lock findings and owner dispositions | TBD |
| Built docs/compatibility and honest published-versus-draft claims | TBD |
| Independent reviewer, evidence, P0/P1/P2 verdict | TBD |
| Maintainer explicit release GO | **NOT GIVEN** |
| TestPyPI/PyPI permissions and publish | **NOT STARTED** |

## Copyable future independent reviewer assignment

> Audit `agustin18/fastapi-cache` against the **exact 0.7.0 frozen
> source SHA and independently downloaded wheel/sdist** in the manifest
> above. Do not trust prior AI reviews, PR summaries, green checks or
> editable source as release-artifact proof. Independently verify source,
> version, wheel/sdist hashes, manifest, first-attempt full Phase B,
> annotated tag target and fresh authenticated security delta.
>
> Attempt to falsify: TTL equality and **live** clock rollback (both
> InMemory modes); Redis zero/negative TTL differences; malformed JSON,
> UTF-8 and typed response HIT/304; PickleCoder trust boundary; failed
> reads/writes and coder errors; cancellation/reconnect/timeout; cache-key,
> Authorization/Cookie/Vary/tenant boundaries; multiple app lifespans,
> non-HTTP tasks, ownership and shutdown races. Do not claim experimental
> backend parity or Redis Cluster namespace clearing.
>
> Reproduce installed-wheel migration/rollback on supported Python 3.8–3.13
> lanes, with 3.8–3.10 functional legacy versus 3.11–3.13 security-support
> distinction. Confirm no secret values in logs/events and no unsupported
> Python 3.14 or HA promises. Test opt-in single-flight/events/resilience
> **only if actually selected for 0.7.0**.
>
> Challenge each performance claim using *pre-registered* budgets, fixed
> independent hardware, full dependency/CPU provenance, repeated AB/BA,
> real socket HTTP, Redis fault profiles and raw samples. A historical
> Redis ratio that changes sign is not an improvement or regression.
>
> Return an evidence matrix: PASS / FAIL / NOT RUN, exact commands/artifact
> identities/CI URLs, reproduction steps, P0/P1/P2 severity, library-owned
> versus application-owned scope, blocking items and a precise
> **conditional GO or NO-GO**. Do not merge, tag, publish or alter settings.
> Mark inaccessible evidence NOT RUN rather than guessing.

**Review cycle:** independent first review → documented fixes → second
independent counteraudit of the **final changed SHA and artifacts** →
separate explicit maintainer GO → only then approved publish operations.
A material source/lock/version change invalidates old final-SHA evidence
and requires appropriate repeat checks. Never forge approval.
