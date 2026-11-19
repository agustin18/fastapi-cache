# Pre-stable release security review — 2026-11-19

**Status: DRAFT FOR INDEPENDENT AUDIT AND MAINTAINER SIGNOFF, NOT AN APPROVED SECURITY RELEASE GATE.**

This document reviews the known advisory register at the authenticated GitHub
Dependabot capture `20261119T032907Z`. It does **not** represent a live
security feed or a claim that the entire transitive dependency graph is safe.

## Evidence and immutable artifact provenance

- [Source snapshot](DEPENDABOT_ALERTS_20261119T032907Z.csv):
  120 alert records, **21 open** (1 critical, 9 high,
  9 medium, 2 low) and **99 fixed** at capture.
- [Historical/current GHSA register](SECURITY_ADVISORY_TRIAGE.csv):
  **95 distinct rows, 74 with current GitHub state fixed, 21 open**. The
  93-row historical baseline is preserved independently; the two current-only
  GHSA are not invented historical alerts.
- [Raw snapshot vs canonical triage regression](../../scripts/validate_stable_security_review.py):
  verifies all 120 captured alerts, requires every raw open GHSA in canonical
  triage and matches identifiers, status, manifest and version fields; the
  25 omitted rows may be **fixed only**. Adversarial tests add an unregistered
  open alert and alter raw fields to ensure fail-closed behavior.
- [Row-by-row release review ledger](STABLE_RELEASE_SECURITY_REVIEW_20261119.csv):
  **95/95 represented** with original alert number, state, class, exact
  source scope, evidence reference and proposed release disposition.
- RC2 tag `v0.3.0rc2` -> Git SHA
  `277b6e71dac5c2807acdbc11366a7864aec1927a`.
  [PyPI publishing workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44458562090)
  and [source CI](https://github.com/agustin18/fastapi-cache/actions/runs/44454056151)
  passed; source's dedicated security jobs passed on Python 3.11, 3.12, 3.13.
- RC2 PyPI wheel SHA-256:
  `2c3f35e053770edd708c42e88e1d2d788bc3c2ed6e2bb3d5b8409f48b79762bf`.
  RC2 sdist SHA-256:
  `145df1aada6deafc90faa3558589b8ac91276fb14eadf28e78e250032998fa1e`.
  Workflow provenance verifies these hashes; this review does not claim an
  additional exact-PyPI-wheel security scan has been saved here.

## How to interpret the ledger

`current_state=fixed` (74 rows) means Dependabot reported the advisory fixed
in the **captured dependency graph**, not proof that every future resolver,
legacy interpreter or consumer application is protected. These receive
`FIXED_IN_CAPTURED_GRAPH`, not a claim of code-path proof.

The **21 open** GHSA all have an individual preliminary disposition and scope
documented in the source register. They receive a **proposed** release-specific
disposition below, not a closed Dependabot status, a dismissal, a GitHub
security finding deletion or final acceptance by the maintainer.

The source `triage_status` field intentionally remains `PENDING` until a
reviewer explicitly signs off. A preliminary `NOT_APPLICABLE` is bounded to
the inspected library path, not the arbitrary dependency use of a consumer.

## The 21 open GHSA — individually tracked

| Advisory | Severity | Dependency | Proposed library-path verdict | Trigger / scope documented in source register |
|---|---|---|---|---|
| [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6) | critical | anyio | `APPLICATION_OR_LEGACY_CONDITIONAL` | Python 3.8/3.9 runtime and Poetry-installed test profiles use AnyIO 4.5.2. The maintainer accepts the runtime residual as separately scop |
| [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Affected trigger: chained response decompression. The package's DynamoDB backend uses aiobotocore/aiohttp and calls no urllib3 API; reque |
| [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Affected trigger: streaming decompression of highly compressed responses. The package's DynamoDB backend uses aiobotocore/aiohttp and cal |
| [GHSA-38jv-5279-wg99](https://github.com/advisories/GHSA-38jv-5279-wg99) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Affected trigger: streaming decompression across redirects. The package's DynamoDB backend uses aiobotocore/aiohttp and calls no urllib3  |
| [GHSA-qccp-gfcp-xxvc](https://github.com/advisories/GHSA-qccp-gfcp-xxvc) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Affected trigger: sensitive headers on proxied low-level redirects. The package's DynamoDB backend uses aiobotocore/aiohttp and calls no  |
| [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r) | high | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Windows-only Starlette StaticFiles file-serving risk. The Redis example's unused StaticFiles(directory='.') mount was removed by PR #37;  |
| [GHSA-82w8-qh3p-5jfq](https://github.com/advisories/GHSA-82w8-qh3p-5jfq) | high | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires a consuming app to parse attacker-controlled URL-encoded form data through Starlette request.form(); no such call exists in fast |
| [GHSA-8988-9cw3-xx77](https://github.com/advisories/GHSA-8988-9cw3-xx77) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Default DynamoDB transport only; independent urllib3 use excluded |
| [GHSA-vxq7-64xx-v4gw](https://github.com/advisories/GHSA-vxq7-64xx-v4gw) | high | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | Default DynamoDB transport only; independent urllib3 use excluded |
| [GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8) | high | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Starlette 0.39.0 through 0.49.0 FileResponse Range parsing may allow unauthenticated CPU exhaustion. The Python 3.8/3.9 lock includes Sta |
| [GHSA-pq67-6m6q-mj2v](https://github.com/advisories/GHSA-pq67-6m6q-mj2v) | medium | urllib3 | `NO_REVIEWED_LIBRARY_CALL_PATH` | urllib3 is runtime/transitive through botocore in the optional DynamoDB graph, but this advisory requires constructing PoolManager with a |
| [GHSA-2c2j-9gv5-cj73](https://github.com/advisories/GHSA-2c2j-9gv5-cj73) | medium | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires a consuming Starlette app to parse large attacker-controlled multipart uploads; fastapi_cache does not handle request forms or f |
| [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2) | medium | requests | `DEVELOPMENT_TOOLING_ONLY` | Affected trigger: predictable temporary-file reuse in extract_zipped_paths(). requests is a development dependency and is not imported by |
| [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) | medium | pytest | `DEVELOPMENT_TOOLING_ONLY` | The affected surface is pytest temporary-directory handling under shared Unix /tmp; pytest is a development dependency, not part of the p |
| [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx) | medium | idna | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires idna.encode() on a very long attacker-controlled hostname; fastapi_cache uses configured DynamoDB regions, not request-supplied  |
| [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr) | medium | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Relevant only when consumer security decisions depend on request.url.path; fastapi_cache's key builder does not read request URL fields. |
| [GHSA-x746-7m8f-x49c](https://github.com/advisories/GHSA-x746-7m8f-x49c) | medium | starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires a consumer route based on Starlette HTTPEndpoint method dispatch; fastapi_cache does not define or dispatch such endpoints. |
| [GHSA-5p39-cfhj-2xmp](https://github.com/advisories/GHSA-5p39-cfhj-2xmp) | medium | anyio | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires an AnyIO process-pool worker to write enough data to stderr; fastapi_cache does not start process-pool workers. Consumer process |
| [GHSA-48p4-8xcf-vxj5](https://github.com/advisories/GHSA-48p4-8xcf-vxj5) | medium | urllib3 | `APPLICATION_OR_LEGACY_CONDITIONAL` | The advisory affects urllib3 redirect handling in Pyodide browser/Node runtimes. Compatibility and security guarantees cover the tested s |
| [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq) | low | Pygments | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires running Pygments AdlLexer on crafted source; fastapi_cache does not import Pygments or invoke lexers. Consumer tooling use is se |
| [GHSA-jp82-jpqv-5vv3](https://github.com/advisories/GHSA-jp82-jpqv-5vv3) | low | Starlette | `APPLICATION_OR_LEGACY_CONDITIONAL` | Requires a malformed request target and consumer middleware/application trusting reconstructed URL authority; the package key builder ign |

## Material release boundaries and needed decisions

1. **Critical AnyIO [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6).**
   Upstream trigger: TLS through AnyIO `connect_tcp` or `TLSStream.wrap`
   with internationalized hostnames and redirected/hijacked connections.
   The lock selects AnyIO 4.5.2 on Python 3.8/3.9, while modern audited
   runtime profiles choose a patched version. Existing policy documents a
   **bounded acceptance** for legacy runtime and isolated local tests only,
   not downstream consumers or arbitrary network destinations. Confirm the
   acceptance's profile boundary, support wording and the current installed
   runtime scan before signing off. Do **not** label the vulnerable package fixed.
2. **High Starlette [GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8).**
   Legacy Starlette 0.44.0 remains affected in Python 3.8/3.9 profiles.
   `fastapi_cache.coder` references `FileResponse` for coder classification
   but does not create a file-serving route; the example's unused
   `StaticFiles(directory="./")` mount was removed in PR #37.
   **This does not protect consumers who independently expose FileResponse or
   StaticFiles**. Confirm this distinction in stable-facing docs and explicitly
   approve the consumer-owned residual.
3. **High Starlette [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r).**
   The previously documented example route no longer exists after PR #37;
   consumer-owned Windows file-serving routes still require review.
4. **Other Starlette advisories** are conditional on form parsing, URL/path
   processing or HTTPEndpoint behavior chosen by consuming apps. This library
   is not a security boundary for other FastAPI/Starlette routes.
5. **urllib3 (seven preliminary non-applicable + Pyodide conditional)**
   and **IDNA** assessments are scoped to the package's inspected optional
   DynamoDB/aiobotocore/aiohttp transport. Consumers may independently use
   urllib3/requests or untrusted hostname inputs; the verdict must not cover
   those paths.
6. **requests and pytest** advisories are marked development-tooling only
   in the reconciled profile. **Pygments** requires a specific lexer invocation
   outside this library's runtime code.

## Maintainer proposal for scoped acceptance

The follow-up [21-GHSA maintainer decision record](MAINTAINER_RISK_ACCEPTANCE_20261119.md)
describes conditional risk acceptance, legacy Python recommendations and
consumer responsibilities. It remains subject to owner PR review;
this original dated evidence ledger stays preserved without rewriting
open Dependabot status or claiming fixed transitive packages.

The `real-estate-arg` agent subsequently reported a clean pip
`fastapi-cache2` -> PyPI RC2 replacement in a disposable Docker
backend and **130 passing tests (16.58s)**. This is third-party/local
agent evidence, not independently archived CI provenance here.

## Explicit release gates still outstanding

- [ ] **Owner/auditor signoff** on all 21 *open* advisory dispositions. Confirm
  the existing bounded acceptance of the critical AnyIO legacy exposure and
  the high Starlette #120 consumer-owned risk. The proposed ledger is not
  signoff and changes no Dependabot alert states.
- [x] Audit the **exact downloaded RC2 PyPI wheel** with all extras on
  CPython 3.11, 3.12 and 3.13: all three passed the published SHA check,
  `pip check` and a full `pip-audit` inventory (72 third-party deps,
  **zero known findings** at scan time). Evidence and 90-day artifacts:
  [published-wheel audit](RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md).
- [ ] Sign off on the 74 graph-fixed rows as a group **within the captured
  source graph** (not a claim about all future consumer resolutions).
- [x] Agent reports completed disposable `real-estate-arg` clean pip
  replacement: `fastapi-cache2==0.2.2` removed, `0.3.0rc2[redis]`
  installed with dependencies and `pip check`, **130 tests passed**.
  Original application/container retained its legacy installation.
- [ ] Retain independent reviewable output from the consumer run:
  package inventory/lock delta and execution logs were reported by the
  agent but not archived in this repository.
- [ ] Re-run a **fresh authenticated** Dependabot capture before stable signoff
  and reconcile any changed/new GHSA (fail closed on new open alerts).
- [ ] Once those gates pass, decide the individual stable dispositions in the
  canonical triage register, retaining the original state and evidence
  separately. A reviewer's PR approval is the place to authorize documented
  risk acceptance; this draft does not manufacture that approval.
- [ ] Only then open the distinct `0.3.0` release-preparation PR. Rebuild and
  re-audit that uniquely versioned distribution; stable is **not** the same
  bytes or hash as RC2.

## Reproducibility

From the repository root, validate the reviewed register without network:

```sh
python scripts/validate_stable_security_review.py
python -m pytest -q tests/test_stable_security_review.py
```

Re-run the source reconciliation from its immutable capture:

```sh
python scripts/reconcile_dependabot_alerts.py \
  --current-snapshot audit/security/DEPENDABOT_ALERTS_20261119T032907Z.csv
```

A new `--current-snapshot` or live capture requires reviewing and refreshing
this **separate** release ledger; the fail-closed validation intentionally
rejects silent drift. The original snapshots and previous releases stay
immutable. See [SECURITY.md](../../SECURITY.md), [SUPPORT.md](../../SUPPORT.md)
and [RELEASE_CHECKLIST.md](../../RELEASE_CHECKLIST.md) for scope and gates.
