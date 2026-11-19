# Scoped release-risk decision for the first stable 0.3.0

**Status: ACCEPTED WITH THE DOCUMENTED SCOPE FOR RELEASED 0.3.0.
This document retains the original pre-publication checklist and evidence.**
For the verified publication and local-agent attestations, see
[the post-release record](../../RELEASE_STATUS_0.3.0.md).

On **2026-11-19**, the maintainer explicitly instructed preparation of the
0.3.0 stable-promotion PR **and recording of the previously scoped residual-risk
acceptance**. This file records that decision and its boundaries; it does not
impersonate a GitHub account signature or claim a submitted GitHub review.
The maintainer can confirm the recorded decision by reviewing/approving the PR
on GitHub. Approval of these boundaries is not permission to publish an
unchecked artifact.

The maintainer accepts **the 21 individual, previously reviewed release
dispositions below**, not vulnerabilities in arbitrary consumer applications,
not a blanket claim of safety on end-of-life Python, and not newly discovered
directly reachable critical/high library vulnerabilities.

This record is a **time-bounded, package-scoped release decision** prepared
from the immutable authenticated Dependabot snapshot
`20261119T032907Z` (120 alerts: 21 open, 99 fixed) and the 95-row
[canonical triage](SECURITY_ADVISORY_TRIAGE.csv), not a live query.

The 25 snapshot entries absent from the historic GHSA register were fixed
in the captured graph. The 74 represented graph-fixed GHSA remain separate
from the 21 still-open cases. An alert's GHSA, package/version and
`current_state` are never changed to manufacture closure.

## Maintainer-directed release dispositions for all 21 open GHSA

| Advisory | Captured severity | Package | Proposed release decision | Alert # |
|---|---|---|---|---|
| [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6) | critical | anyio | `LEGACY_CONDITIONAL_ACCEPT` | 75 |
| [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 15 |
| [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 16 |
| [GHSA-38jv-5279-wg99](https://github.com/advisories/GHSA-38jv-5279-wg99) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 26 |
| [GHSA-qccp-gfcp-xxvc](https://github.com/advisories/GHSA-qccp-gfcp-xxvc) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 48 |
| [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r) | high | starlette | `CONSUMER_FILE_SERVING_SCOPE` | 64 |
| [GHSA-82w8-qh3p-5jfq](https://github.com/advisories/GHSA-82w8-qh3p-5jfq) | high | starlette | `APPLICATION_CONDITIONAL` | 70 |
| [GHSA-8988-9cw3-xx77](https://github.com/advisories/GHSA-8988-9cw3-xx77) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 77 |
| [GHSA-vxq7-64xx-v4gw](https://github.com/advisories/GHSA-vxq7-64xx-v4gw) | high | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 78 |
| [GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8) | high | starlette | `CONSUMER_FILE_SERVING_SCOPE` | 120 |
| [GHSA-pq67-6m6q-mj2v](https://github.com/advisories/GHSA-pq67-6m6q-mj2v) | medium | urllib3 | `NO_INSPECTED_PACKAGE_PATH` | 12 |
| [GHSA-2c2j-9gv5-cj73](https://github.com/advisories/GHSA-2c2j-9gv5-cj73) | medium | starlette | `APPLICATION_CONDITIONAL` | 14 |
| [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2) | medium | requests | `DEVELOPMENT_ONLY` | 31 |
| [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) | medium | pytest | `DEVELOPMENT_ONLY` | 44 |
| [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx) | medium | idna | `APPLICATION_CONDITIONAL` | 49 |
| [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr) | medium | starlette | `APPLICATION_CONDITIONAL` | 52 |
| [GHSA-x746-7m8f-x49c](https://github.com/advisories/GHSA-x746-7m8f-x49c) | medium | starlette | `APPLICATION_CONDITIONAL` | 63 |
| [GHSA-5p39-cfhj-2xmp](https://github.com/advisories/GHSA-5p39-cfhj-2xmp) | medium | anyio | `APPLICATION_CONDITIONAL` | 74 |
| [GHSA-48p4-8xcf-vxj5](https://github.com/advisories/GHSA-48p4-8xcf-vxj5) | medium | urllib3 | `RUNTIME_OUTSIDE_SUPPORTED_PROFILE` | 119 |
| [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq) | low | Pygments | `APPLICATION_CONDITIONAL` | 33 |
| [GHSA-jp82-jpqv-5vv3](https://github.com/advisories/GHSA-jp82-jpqv-5vv3) | low | Starlette | `APPLICATION_CONDITIONAL` | 69 |

**Interpretation of decisions:**

- `LEGACY_CONDITIONAL_ACCEPT`: retain Python 3.8/3.9 functional support
  despite the known affected AnyIO line; no direct `fastapi_cache` TLS
  trigger was found. Document lack of security support, residual consumer
  TLS risk, and prefer upgrading interpreter plus dependencies.
- `CONSUMER_FILE_SERVING_SCOPE`: no vulnerable file-serving mount in the
  shipped example after PR #37 and no `FileResponse` route in core cache
  code. This does not mitigate downstream affected Starlette deployments.
- `NO_INSPECTED_PACKAGE_PATH`: direct source review found no applicable
  vulnerable urllib3 API use in core/inspected DynamoDB transport. This is
  **not** a statement about independent urllib3 usage by applications.
- `APPLICATION_CONDITIONAL`: triggering functionality lives in an
  application-controlled Starlette/AnyIO/IDNA/Pygments usage path rather
  than a demonstrated package-controlled entry point. A consuming
  application must review its actual features and versions.
- `DEVELOPMENT_ONLY`: reviewed reports refer to local dev/test dependency
  profiles, not the installed published cache wheel runtime.
- `RUNTIME_OUTSIDE_SUPPORTED_PROFILE`: the described Pyodide/browser/Node
  advisory is outside the server-side CPython verification contract.

## Required acceptance boundaries

1. **Do not claim 'zero vulnerabilities' globally.** The published PyPI
   `0.3.0rc2` wheel was scanned on **server-side CPython 3.11–3.13**
   with all extras. At scan time, 72 installed third-party dependencies
   per profile produced no known findings. This cannot certify Python
   3.8/3.9, an arbitrary consumer's requirements, or future resolver results.
2. **Do not accept an unmitigated critical/high _package-controlled_
   reachable vulnerability.** If a new call path or exploit evidence
   contradicts today's scope, re-open the decision and fix/block release.
3. **Security support is Python 3.11–3.13 only**, best effort per SUPPORT.md.
   Functional support on 3.8–3.10 remains a migration bridge.
4. **No Dependabot alert is dismissed as 'fixed' merely on this basis.**
   Raw snapshots stay immutable; new or reopened alerts need reassessment.
5. **Consumer responsibilities** include TLS destinations, independent
   urllib3, static/file-serving routes, form parsing and custom middleware,
   custom cache keys/tenant isolation, and safe `PickleCoder` usage.
6. **Exact final wheel release gate:** the `0.3.0` distribution must be
   rebuilt, metadata verified and security-audited separately from RC2.
7. **Operational secret exposure:** any real Docker Compose credentials
   leaked into logs/history must be assessed and rotated before operations
   that could use compromised credentials.

## Source evidence and trigger details

- [Complete individual source scopes and approval gates](STABLE_RELEASE_SECURITY_REVIEW_20261119.csv)
- [Detailed security review](STABLE_RELEASE_SECURITY_REVIEW_20261119.md)
- [Raw GHSA snapshot](DEPENDABOT_ALERTS_20261119T032907Z.csv)
- [Exact RC2 wheel audit](RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md)
- [User-facing legacy support explanation](LEGACY_SUPPORT_AND_RISKS.md)
- [Public support](../../SUPPORT.md) and [security policy](../../SECURITY.md)

## Maintainer-directed risk decision and pending publication gates

**Decision date:** 2026-11-19 (recorded at explicit owner request for a
0.3.0 release PR; GitHub-hosted approval/identity attestation still pending).

- [x] Accept the **21 individual release-specific dispositions** in the table
  and their restrictions; this does not close or dismiss any GHSA.
- [x] Acknowledge the **74 graph-fixed** ledger rows and 25 omitted snapshot
  rows as resolved **in the dated captured dependency graph only**, not as
  globally fixed bugs or an assurance for all consumers.
- [x] Specifically accept the critical **AnyIO #75** residual only for
  the documented Python **3.8/3.9 functional legacy/test** profiles.
  No security support is promised to those runtimes, and downstream AnyIO
  TLS usage still requires consumer action or an interpreter upgrade.
- [x] Specifically accept the conditional **Starlette #120/#64/#70**
  scope: the library no longer ships an unsafe StaticFiles mount and does
  not serve files or parse forms through the affected code paths. An
  application independently using vulnerable Starlette file/form handling
  is **not protected** by installing this fork.
- [x] Accept the **urllib3** package-path disposition only as no
  directly applicable library call found in the reviewed cache/DynamoDB
  transport. Consumer-owned urllib3 usage is **not accepted on their behalf**.
- [x] Confirm that Python 3.8–3.10 are **functional legacy compatibility**
  only; recommend server-side CPython 3.11–3.13, with 0.3.x best-effort
  security maintenance limited to the documented modern profiles.
- [x] Preserve the captured alert states and the **canonical source triage**
  as historical evidence (including its PENDING bookkeeping status).
  This separate document records the **release-specific acceptance**;
  source PENDING is **not** secretly converted to FIXED or globally accepted.

**Independent and operational conditions still outstanding:**

- [x] Independent local agent returned **technical GO for PR #42**
  (the 0.3.0 preparation). Its 27/27 CI passed, without a runtime or
  dependency change from the audited RC2. Newly demonstrated
  package-controlled critical/high flaws remain a hard NO-GO.
- [x] Maintainer-directed bounded acceptance was recorded
  [on PR #42](https://github.com/agustin18/fastapi-cache/pull/42#issuecomment-7016369125)
  against head `38a900967e2043bc604a5230d4b4bb9f6a16d541`;
  merge commit `ad2d577e2d345131c56c06f0859961b17675e652`.
  The PR comment is a release decision record, not a fabricated
  GitHub APPROVE review. Owner self-approval is not required.
- [ ] Make **one authenticated Dependabot delta check immediately before
  production PyPI**, using the 2026-11-19 snapshot. Review only
  new/reopened/materially changed findings. Already scoped and unchanged
  residual GHSA **do not need re-acceptance**. The preliminary
  non-production TestPyPI test need not wait for this.
- [ ] Verify the versioned **0.3.0 final wheel and sdist**, installability,
  runtime dependency inventory and vulnerability audit in Python 3.11–3.13
  using a fresh build; the published RC2 hash is not the final hash.
- [x] Maintainer reported on 2026-11-19 that the Docker Compose secrets
  issue is **resolved**. This records the owner's operational
  attestation, not independent access to private rotation evidence.
- [ ] Separately authorize the actual PyPI publication **after** the
  release PR, CI, security refresh and artifact verification.

**Decision:** GO to prepare/review the first stable 0.3.0 distribution
under these bounded conditions; **NOT** a claim that 0.3.0 is published
or that all external release gates have passed.

The decision must be reconsidered if a new credible exploit path exists
in package-controlled behavior, a relevant dependency graph changes, or
the maintained 0.3.x support scope changes.

## Post-publication addendum — 2026-11-19

The independent release-preparation review returned technical GO for PR #42.
The maintainer explicitly directed the scoped 21-GHSA acceptance; see the
[PR discussion](https://github.com/agustin18/fastapi-cache/pull/42#issuecomment-7016369125).
Subsequently the annotated `v0.3.0` tag, TestPyPI and production PyPI
workflow completed successfully with matching artifact hashes.
The local release agent reported a final authenticated delta comparison
with the same **21 open alerts and no new ones**. The source snapshots,
individual scope boundaries and historical checklist entries above remain
unchanged; none of these advisories was marked fixed by this release.
This addendum does not extend acceptance to new advisories, affected
consumer deployments or EOL Python security support.
