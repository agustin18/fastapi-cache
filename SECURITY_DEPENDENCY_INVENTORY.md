# Dependency security inventory

**Snapshot:** 2026-11-16 · **Stable SHA:** `38e2dc5bde5f5ce442b5c0ef4949e54544ee05c1` · **Package:** `fastapi-cache-stable==0.3.0b1`

This is an inventory for release planning, not an exploitability verdict. It records the pre-remediation lock snapshot; PR #25's h11/httpcore remediation is described below. The alert-level snapshot is in [`DEPENDABOT_ALERTS_2026-11-16.csv`](DEPENDABOT_ALERTS_2026-11-16.csv).

## Dependabot snapshot: `poetry.lock`

The authenticated repository alert API returned 93 open alerts with 93 distinct GHSA IDs across 14 packages. These are lockfile findings, not 93 independent runtime defects.

| Package | Locked version(s) | Scope / relation | Alerts by severity | Notes |
|---|---|---|---|---|
| `aiohttp` | 3.9.5 | Runtime, transitive, optional | 51: 13 high, 22 medium, 16 low | Pulled through optional `aiobotocore`/DynamoDB; lock marks it optional. |
| `anyio` | 4.4.0 | Runtime, transitive | 2: 1 critical, 1 medium | Fix begins at 4.14.2; that release requires Python >=3.10. |
| `cryptography` | 43.0.0 | Development, transitive | 6: 3 high, 1 medium, 2 low | Reached through `types-redis`. |
| `dnspython` | 2.6.1 | Runtime, transitive | 2 high | Reached through `fastapi -> email-validator`. |
| `h11` | 0.14.0 | Runtime, transitive | 1 critical | Reached through `uvicorn`; fix 0.16.0. |
| `idna` | 3.7 | Runtime, transitive | 1 medium | Also appears in resolver results through `httpx`/`email-validator`. |
| `Jinja2` | 3.1.4 | Runtime, direct | 3 medium | Declared directly; no import from `fastapi_cache/` found in this review. |
| `Pygments` | 2.18.0 | Runtime, transitive | 1 low | Via the FastAPI CLI dependency tree in the lock. |
| `python-dotenv` | 1.0.1 | Runtime, transitive | 1 medium | Via `uvicorn[standard]` in the lock. |
| `python-multipart` | 0.0.9 | Runtime, transitive | 8: 4 high, 1 medium, 3 low | Required for FastAPI form parsing; optional in current FastAPI standard extras, but present in the locked FastAPI 0.111.1 graph. |
| `pytest` | 8.3.1 | Development, direct | 1 medium | Development-only. |
| `requests` | 2.32.3 | Development, direct | 2 medium | Development-only. |
| `starlette` | 0.37.2 | Runtime, transitive | 7: 3 high, 3 medium, 1 low | Via `fastapi -> starlette`. |
| `urllib3` | 1.26.19 and 2.2.2 | Runtime, transitive | 7: 6 high, 1 medium | Both versions occur in the lock under different constraints/markers; optional DynamoDB resolves 1.26.x on Python 3.8/3.9. |

Totals: **2 critical, 31 high, 37 medium, 23 low**; **84 runtime and 9 development**; **87 transitive and 6 direct**. For each record the CSV stores the alert/identifiers, lock version metadata, relationship, scope, affected range, first patched version, and a pending manual-applicability status. The lock's Python constraint is recorded separately from advisory-specific Python applicability.

Representative parent chains from `pyproject.toml` and `poetry.lock`:

| Package | Lock dependency path |
|---|---|
| AnyIO | FastAPI -> Starlette -> AnyIO; FastAPI -> HTTPX -> AnyIO |
| h11 | Uvicorn -> h11 |
| Starlette | FastAPI -> Starlette |
| aiohttp | optional aiobotocore/DynamoDB -> aiohttp |
| urllib3 | optional aiobotocore -> botocore -> urllib3; development requests -> urllib3 |
| dnspython / idna | FastAPI -> email-validator -> dnspython/idna |
| python-multipart | FastAPI -> python-multipart |
| cryptography | development types-redis -> cryptography |
| python-dotenv | Uvicorn standard extra -> python-dotenv |
| Pygments | FastAPI -> fastapi-cli -> typer -> rich -> Pygments |

These are candidate paths in the lock graph, not an exploitability assessment. Optional extras, marker-specific versions, actual installed versions, and advisory reachability still need per-finding review.

## What a fresh PyPI installation resolves

Each profile was installed from the published PyPI wheel in a clean `uv` virtual environment. `pip check` passed in every profile. `pip-audit 2.10.1` ran against the pinned `pip freeze` inventory with alias expansion disabled; the counts below are distinct output ID strings, not CVE severity counts.

| Python | Profile | Key resolved versions | `pip check` | `pip-audit` result |
|---|---|---|---|---|
| 3.8.20 | Base / Redis | FastAPI 0.124.4, Starlette 0.44.0, AnyIO 4.5.2, h11 0.16.0 | Pass | 9 IDs across AnyIO and Starlette |
| 3.8.20 | All extras | Above plus aiohttp 3.10.11, urllib3 1.26.20 | Pass | 66 IDs across aiohttp, urllib3, AnyIO and Starlette |
| 3.9.25 | Base / Redis | FastAPI 0.128.8, Starlette 0.49.3, AnyIO 4.12.1, h11 0.16.0 | Pass | 7 IDs across AnyIO and Starlette |
| 3.9.25 | All extras | Above plus aiohttp 3.13.5, multidict 6.7.1, urllib3 1.26.20 | Pass | 46 IDs across five packages |
| 3.10.16 | Base / Redis / all extras | FastAPI 0.162.5, Starlette 1.7.0, AnyIO 4.16.0, h11 0.16.0; all extras include aiohttp 3.14.5, urllib3 2.8.0 | Pass | No findings |
| 3.13.12 | Base / Redis / all extras | FastAPI 0.163.1, Starlette 1.10.0, AnyIO 4.16.0, h11 0.16.0; all extras include aiohttp 3.14.5, urllib3 2.8.0 | Pass | No findings |

The 3.8/3.9 results confirm the policy distinction: those versions remain in the legacy functional matrix, but current compatible dependency resolution is not free of known advisories. AnyIO 4.14.2 cannot be selected there because it requires Python >=3.10. The optional DynamoDB extra also pulls an older urllib3 line on those interpreters. Python 3.10+ results reflect a fresh resolution as of this snapshot; they do not repair the locked development environment.

PR #25 adds a separate CI security-audit profile for Python 3.11–3.13. It builds the wheel,
installs the package's `all` extras plus `fastapi[standard-no-fastapi-cloud-cli]` into an isolated
target directory, then scans that directory with a separate `pip-audit` environment. This keeps
runner/build-tool packages out of the runtime report. The legacy rows above remain subject to
manual per-advisory applicability review; no critical finding is waived solely because its
interpreter is EOL.

The already-published `0.3.0b1` metadata is `>=3.8,<4.0`, so pip accepts Python 3.14 even though CI stops at 3.13. A Python 3.14.7 base install passed `pip check` and a small MISS/HIT smoke test, but no full suite or optional-extra audit was run there. Stable `0.3.0` is planned with `>=3.8,<3.14`; Python 3.14 remains outside the release matrix until full CI passes.

## Poetry development lock — initial local recheck (2026-11-17; superseded)

Using Poetry 1.8.3 with Python 3.12, `poetry install --with dev --all-extras --no-root --sync` installed 59 locked packages. `pip-audit 2.10.1 --path <venv>/lib/python3.12/site-packages --aliases off` reported 151 records (87 distinct ID strings) across 13 packages, including the optional aiohttp tree.

`pip check` on that environment reports: `pendulum 3.0.0 requires time-machine, which is not installed.` The installed Pendulum metadata requires `time-machine >=2.6.0` for CPython, while the lock records it only under Pendulum's `test` extra. This is a lock/development-environment consistency finding; the fresh PyPI install selected Pendulum 3.3.0 and passed `pip check`.

`poetry export --with dev` (without optional extras) succeeds. `poetry export --with dev --all-extras` fails in Poetry's exporter because it elects urllib3 2.2.2 while the Python <3.10 botocore marker requires `urllib3 >=1.25.4,<1.27`. The actual Poetry all-extras install completed, so this exporter failure is recorded separately from pip install behavior.

## Candidate working-tree recheck before main-only correction (2026-11-17; superseded)

This section records the local candidate after the Pendulum lock correction. It does not
change the historical 2026-11-16 Dependabot or published-wheel snapshots above. Its dev-only
`time-machine` approach was superseded after the main-only checks below failed.

- Base: `stable` at `032218f41aeef612ae4ac175b7848a1af31d4c26`; candidate commit:
  `36978ecbb1d76f07f5a7f69c81d3f306d3fadefe`. The working tree also has uncommitted
  changes in `pyproject.toml`, `poetry.lock`, and this inventory; none is in the published
  `0.3.0b1` artifact.
- Added `time-machine >=2.6.0` to the Poetry `dev` group and locked 2.15.0. Pendulum 3.0.0's
  PyPI wheel metadata requires this package on CPython even though Pendulum's lock metadata
  lists it under its optional `test` extra. The project wheel metadata does not add
  `time-machine` as a direct runtime dependency.
- With Poetry 1.8.3, `poetry check --lock` passes. Clean Poetry environments installed from
  the lock with `dev` and all project extras pass `pip check` on Python 3.8 and 3.12.
  The functional suite passes on each: 189 passed, 8 Redis-dependent tests skipped.
- `pip-audit 2.10.1 --path <Python-3.12-lock-env>/lib/python3.12/site-packages --aliases off`
  reports 149 finding records (86 distinct IDs) across 12 packages in the locked `dev` plus
  all-extras environment. This is a lock/development-profile scan, not the supported-runtime
  wheel audit in CI; the two results have different scopes and must not be conflated.
- `poetry export --with dev --all-extras --without-hashes` still fails: the exporter selects
  urllib3 2.2.2 where botocore's Python <3.10 marker requires `<1.27`. The lock can still be
  installed directly. For a reproducible lock audit, install into a clean Poetry environment
  using `poetry install --with dev --all-extras --no-root --sync`, then scan that environment's
  `site-packages` with `pip-audit --path ... --aliases off`; record Python, Poetry,
  pip-audit, and `pip freeze` with the result.

## Source-verified preliminary code-path dispositions

These are preliminary path assessments for selected advisories, not an external audit or a
complete disposition of the 93-alert snapshot. Every GHSA must retain its own row and evidence;
unlisted findings remain `PENDING`. `APPLICATION_CONDITIONAL` does not mean the risk is
accepted.

| GHSA | Preliminary state | Evidence and boundary |
|---|---|---|
| [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6) (AnyIO TLS, critical) | `APPLICATION_CONDITIONAL` | The trigger is AnyIO `connect_tcp()` / `TLSStream.wrap()` with non-ASCII hostnames and a redirected connection. No such call is present in this package; consumers may call these APIs through their own application/dependency code. The fix, AnyIO 4.14.2, is unavailable on Python 3.8/3.9. Maintainer risk acceptance remains pending. |
| [GHSA-5p39-cfhj-2xmp](https://github.com/advisories/GHSA-5p39-cfhj-2xmp) (AnyIO process stderr) | `APPLICATION_CONDITIONAL` | Requires an AnyIO process-pool worker to write enough data to stderr. No process-pool API use was found in the package. Consumer use remains possible. |
| [GHSA-f96h-pmfr-66vw](https://github.com/advisories/GHSA-f96h-pmfr-66vw) (Starlette multipart fields) | `APPLICATION_CONDITIONAL` | Requires an application to parse attacker-controlled multipart form data. No `request.form()` call was found in `fastapi_cache/`. |
| [GHSA-2c2j-9gv5-cj73](https://github.com/advisories/GHSA-2c2j-9gv5-cj73) (Starlette multipart large files) | `APPLICATION_CONDITIONAL` | The vulnerable route is multipart parsing of large uploads; the cache package does not parse forms. |
| [GHSA-82w8-qh3p-5jfq](https://github.com/advisories/GHSA-82w8-qh3p-5jfq) (Starlette URL-encoded form limits) | `APPLICATION_CONDITIONAL` | Requires application use of `request.form()` on `application/x-www-form-urlencoded`; no such call was found in the package. |
| [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr) (Starlette Host/path reconstruction) | `APPLICATION_CONDITIONAL` | Affects applications making security decisions from `request.url.path`. `default_key_builder` does not read the request or URL; downstream middleware/application code may. |
| [GHSA-jp82-jpqv-5vv3](https://github.com/advisories/GHSA-jp82-jpqv-5vv3) (Starlette path/URL authority) | `APPLICATION_CONDITIONAL` | Requires a malformed request target and application/middleware code that trusts reconstructed URL fields. The package key builder does not read those fields. |
| [GHSA-x746-7m8f-x49c](https://github.com/advisories/GHSA-x746-7m8f-x49c) (Starlette `HTTPEndpoint`) | `APPLICATION_CONDITIONAL` | The trigger requires applications to use Starlette `HTTPEndpoint`; no such use was found in the cache package. |
| [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r) (Starlette `StaticFiles`, Windows UNC) | `APPLICATION_CONDITIONAL` | Applies to Windows applications serving static files. Core package code does not use `StaticFiles`; the Redis example mounts it in `examples/redis/main.py`, so that sample's Windows deployment must be considered separately. |
| [GHSA-cq5v-8q36-5273](https://github.com/advisories/GHSA-cq5v-8q36-5273) (aiohttp response parser) | `EXPERIMENTAL_EXTRA` | aiobotocore 2.13.1 uses `aiohttp.ClientSession` for DynamoDB HTTP requests, so malformed response parsing is on the experimental backend's path. `auto_decompress=False` does not disable the HTTP response parser; `AIOHTTP_NO_EXTENSIONS=1` is the advisory's specific workaround but is not enabled by this package. Normal AWS endpoint trust and custom endpoint/proxy configuration affect reachability. The tested Python 3.8/3.9 profiles resolve affected aiohttp versions; Python 3.11–3.13 fresh profiles resolve patched aiohttp. This is not a demonstrated exploit in DynamoDB. |
| [GHSA-h4cc-hm5h-fmm9](https://github.com/advisories/GHSA-h4cc-hm5h-fmm9) (aiohttp concatenated-stream decompression) | `NOT_APPLICABLE` to the default DynamoDB transport | The advisory requires aiohttp to decompress response content. aiobotocore 2.13.1 constructs `ClientSession(auto_decompress=False)`, sends `Accept-Encoding: identity`, and exposes raw response bytes through `AioAWSResponse`; the inspected `get_item`/`put_item` path performs no later decompression. This does not cover applications using aiohttp independently or custom transport/event overrides. |
| [GHSA-8988-9cw3-xx77](https://github.com/advisories/GHSA-8988-9cw3-xx77) (urllib3 HTTPS proxy TLS) | `NOT_APPLICABLE` to the package's DynamoDB transport | aiobotocore's async endpoint sends requests through aiohttp, not urllib3's proxy connection manager. This does not assess independent urllib3 use by a consuming application. |
| [GHSA-vxq7-64xx-v4gw](https://github.com/advisories/GHSA-vxq7-64xx-v4gw) (urllib3 chunked response streaming) | `NOT_APPLICABLE` to the package's DynamoDB transport | The async endpoint wraps aiohttp responses and does not use urllib3 `HTTPResponse.stream()` / `read_chunked()`. This does not assess independent urllib3 use by a consuming application. |
| [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq) (Pygments `AdlLexer` ReDoS, low) | `APPLICATION_CONDITIONAL` | The trigger is local use of `AdlLexer` with crafted source. No Pygments import or lexer use exists in `fastapi_cache/`; Pygments is absent from the default wheel and enters the FastAPI CLI/standard-extra or development profiles. The Python 3.8 lock has 2.18.0 (fixed in 2.20.0); modern FastAPI-standard profiles resolved 2.21.0. A consumer invoking the lexer on untrusted local input must assess its own exposure. |
| [GHSA-mf9w-mj56-hr94](https://github.com/advisories/GHSA-mf9w-mj56-hr94) (python-dotenv symlink write, moderate) | `APPLICATION_CONDITIONAL` | The trigger requires `set_key()` / `unset_key()` on an attacker-controlled symlink and a cross-device rename fallback. No dotenv mutation calls exist in this repository. The Python 3.8 lock has 1.0.1 (fixed in 1.2.2); modern FastAPI-standard profiles resolve 1.2.4. Consumer deployment scripts that mutate `.env` files need separate review. |
| [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx) (IDNA long-input CPU DoS, moderate) | `APPLICATION_CONDITIONAL` | The trigger is a very long attacker-controlled hostname passed to `idna.encode()`; fixed in 3.15. No direct IDNA use or request-derived hostname path was found in `fastapi_cache/`. `DynamoBackend` accepts a configured region and uses botocore's default endpoint, not a request-supplied hostname. The Python 3.8 lock has idna 3.7, while the clean wheel profile resolved 3.15; applications using IDNA on untrusted hostnames or custom endpoints need independent bounds/review. |

These dispositions should be reviewed by the external auditor. They do not waive a GHSA,
replace the remaining 93-entry triage, or authorize release.

## Candidate recheck after Poetry main-only correction (2026-11-17)

The dependency-resolution, local-suite and wheel checks in this section were run against
candidate commit `1666afaf0e52811354abeb82f61e5c45d6a95ee2`, before the later inventory and
lifespan/documentation commits. Those later commits did not change `pyproject.toml` or
`poetry.lock`, but `a631c1e` added a regression test and changed documentation included in the
distribution. The current PR head is `a631c1ecaaa3b74e3a3ff9e29c4aa3457608afe7`; no artifact
built from that exact head has been published. Do not treat the local wheel hash below as the
wheel for the current head.

The initial dev-only `time-machine` correction above did not make a `--only main` install
consistent. That was reproduced on Python 3.8 and 3.12: both installed Pendulum 3.0.0 without
time-machine and `pip check` reported the missing requirement. Candidate `1666afa` changed the
dependency metadata and lock by interpreter instead:

- Pendulum 3.0.x on Python 3.8, 3.1.x on Python 3.9, and >=3.2,<4 on Python >=3.10.
- `time-machine >=2.6.0` is a main dependency only on CPython Python <3.9, matching the
  installed Pendulum 3.0.0 wheel metadata. It is not imposed on Python 3.9+ or PyPy.
- Clean `poetry install --only main --no-root --sync` environments pass `pip check` on
  Python 3.8, 3.9, 3.10 and 3.12. Resolved Pendulum versions were 3.0.0, 3.1.0, 3.3.0
  and 3.3.0 respectively; time-machine is installed only on Python 3.8.
- A locally built wheel from the `1666afa` candidate has `Requires-Python: >=3.8,<3.14`, carries
  those same Pendulum markers, and includes the time-machine requirement only under
  `python_version < 3.9 and implementation_name != pypy`.
- Clean `poetry install --with dev --all-extras --sync` environments passed `pip check` and
  the full suite on Python 3.8, 3.9, 3.10 and 3.12 at that candidate: 190 passed, 8
  Redis-dependent tests skipped per run. Resolved Pendulum was 3.0.0, 3.1.0, 3.3.0 and 3.3.0.
  Python 3.8 and 3.9 use the EOL compatibility profile; these tests are not a security-support claim.
- An explicit Python 3.10 environment overridden to Pendulum 3.2.0 passes `pip check` and the
  full suite (190 passed, 8 Redis skips). The aware-datetime offset regression also passes in
  the focused codec/decorator tests with Pendulum 3.0.0, 3.1.0, 3.2.0 and 3.3.0. It verifies
  the instant and encoded UTC offset; the JSON representation does not retain the IANA zone key.
- The locally built wheel from the `1666afa` candidate has SHA-256
  `066f64616f4bb6d7e4d073c2f529127a709e60e64635ca47f1fa78f11a7c97bf`. Clean wheel installs
  pass `uv pip check` and an installed-package MISS/HIT smoke on Python 3.8, 3.9, 3.10 and
  3.12; the smoke asserts imports come from `site-packages`. Pendulum/time-machine selections
  match the metadata above. The existing published `0.3.0b1` artifact is unchanged.
- On Python 3.11, 3.12 and 3.13, the local wheel plus `all` extras and
  `fastapi[standard-no-fastapi-cloud-cli]` installed successfully in clean environments;
  `uv pip check` and installed-wheel MISS/HIT smoke passed. Resolved aiohttp 3.14.5,
  urllib3 2.8.0 and Pendulum 3.3.0. `pip-audit 2.10.1 --path <env>/site-packages
  --aliases off` reported no known vulnerabilities for each profile. These are local checks
  against the built wheel, not GitHub CI on the exact source diff.
- A `pip-audit --path` scan of the Python 3.8 full environment reports 159 records / 91 IDs,
  including 12 records / 6 IDs for the environment's installed `pip` tool. Excluding that
  unpinned installer leaves 147 records / 85 IDs across 12 lock packages. The Python 3.12
  full environment reports 149 records / 86 IDs across 12 lock packages, with no pip findings.
  These are development/all-extras lock scans, not published-wheel runtime scans or the
  historical 93-alert Dependabot snapshot.
- `poetry check --lock` passes. The all-extras exporter still has the urllib3 marker conflict;
  use the direct locked install plus `pip-audit --path` procedure unless the exporter is fixed.
- The first 2026-11-17 audit reported title/impact review of 33 critical/high entries, 60
  medium/low entries without full official/source review, and 3 `PENDING` scope rows. The later
  delta audit reviewed diff SHA `dccc12cae4b188a69ac391331bc94b1a111b0876f76bddf62c9b7cbc1aa7a6fe`
  and gave CONDITIONAL GO to update the PR draft, not to merge or release. The three former
  pending IDs now have preliminary source-based dispositions in the table above; the original
  CSV remains unchanged and the remaining medium/low rows still require review. No residual risk
  is accepted by the auditor on behalf of the maintainer.
- PR #25 is OPEN/DRAFT at head `a631c1ecaaa3b74e3a3ff9e29c4aa3457608afe7` with
  `mergeStateStatus: CLEAN`. All 23 GitHub checks pass on that exact head, including packaging,
  CodeQL, legacy matrices and Python 3.11–3.13 security audits; see the
  [current PR checks](https://github.com/agustin18/fastapi-cache/pull/25/checks). The local
  suite and wheel checks above were on the earlier `1666afa` candidate, not this exact head.
  The `a631c1e` regression test is covered by current GitHub CI. No merge or stable artifact was
  published.

## Direct-dependency scope notes

| Dependency | Evidence from this review | Inventory status |
|---|---|---|
| FastAPI | Imported by the core decorator/coder code | Core runtime dependency |
| Pendulum | Imported by `fastapi_cache/coder.py` for date/datetime decoding | Core runtime use; candidate resolves 3.0.x/3.1.x/3.2+ by Python and mirrors Pendulum 3.0.0's CPython 3.8 `time-machine` metadata requirement |
| Uvicorn | `uvicorn.run()` appears in examples; no core import found | Candidate to move out of mandatory runtime dependencies; no change in this PR |
| Jinja2 | Core imports Starlette's private `_TemplateResponse` in `fastapi_cache/coder.py` to exclude template responses from `PickleCoder`; Starlette 1.3.1 raises an import error from `starlette.templating` when Jinja2 is absent. Template rendering itself remains in examples. | Keep the direct dependency while this private Starlette import remains. The Jinja advisories require untrusted template content and do not indicate a template-execution path in `fastapi-cache` itself. |
| Redis, aiomcache, aiobotocore | Optional project extras | Keep their separate support/experimental status in the remediation decision |

## Decisions required before RC

1. The maintainer confirmed separate contracts: stable metadata `>=3.8,<3.14`, functional legacy tests on 3.8–3.10, and security support on 3.11–3.13. Python 3.14 remains excluded pending full CI.
2. PR #25 updates locked h11 to 0.16.0 and httpcore to 1.0.9 to remediate the request-smuggling parser finding and satisfy the HTTPX transport constraint; the current GitHub CI passes on head `a631c1e`. Fresh PyPI installs already resolve patched h11 0.16.0 on Python 3.8+.
3. The table above contains preliminary source-based dispositions for selected AnyIO/Starlette advisories. The package has no direct calls to the listed TLS, form, static-file or `HTTPEndpoint` paths, but consumer applications may use them. The remaining alert snapshot is not fully reviewed; EOL status alone is not an applicability disposition.
4. Selected optional DynamoDB/aiohttp/urllib3 paths are assessed above, including the bounded `NOT_APPLICABLE` conclusion for `GHSA-h4cc-hm5h-fmm9` on the default DynamoDB transport. Other alert rows and consumer-provided transports still require review; do not treat lock alerts as runtime vulnerabilities or dismiss them without evidence.
5. The Pendulum/Poetry `--only main` mismatch is corrected in PR #25 by interpreter-specific Pendulum constraints and a CPython<3.9 time-machine marker. Candidate metadata and CI are covered by the current head checks; the full-extras exporter still has the urllib3 marker conflict.
6. Review the current lock findings beyond the Pendulum correction. The Python 3.8/3.12 lock scans still report 147/85 and 149/86 records/IDs respectively after excluding the unpinned Python 3.8 `pip` tool. These differ in scope from the 93 Dependabot alerts and the supported-runtime wheel audit.
7. Keep the `GHSA-h4cc-hm5h-fmm9` assessment bounded to the default DynamoDB transport using `auto_decompress=False`; independent aiohttp use and custom transport/event overrides remain outside that conclusion.
8. Uvicorn remains used by examples; Jinja2 stays direct while the core imports Starlette's private `_TemplateResponse` type.

The original 2026-11-16 snapshot changed no package versions. PR #25 restores legacy marker resolution, includes the targeted h11 0.16.0/httpcore 1.0.9 remediation, and resolves Pendulum per Python version with time-machine only for the Python 3.8 CPython path. It does not upgrade the full test-tool/dependency set. The current head has green CI, but the 93-alert snapshot still lacks full advisory-by-advisory disposition, AnyIO/DynamoDB residuals need maintainer decisions, and owner-run consumer-application validation plus a wheel-based migration E2E using persisted legacy Redis data remain open. These are technical validation tasks, not claims of third-party adoption; they can use a local wheel built from the exact candidate head without publishing a release. The published `0.3.0b1` artifact is unchanged; RC/stable remain NO-GO.
