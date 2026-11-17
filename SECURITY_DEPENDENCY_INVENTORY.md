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

## Poetry development lock

Using Poetry 1.8.3 with Python 3.12, `poetry install --with dev --all-extras --no-root --sync` installed 59 locked packages. `pip-audit 2.10.1 --path <venv>/lib/python3.12/site-packages --aliases off` reported 151 records (87 distinct ID strings) across 13 packages, including the optional aiohttp tree.

`pip check` on that environment reports: `pendulum 3.0.0 requires time-machine, which is not installed.` The installed Pendulum metadata requires `time-machine >=2.6.0` for CPython, while the lock records it only under Pendulum's `test` extra. This is a lock/development-environment consistency finding; the fresh PyPI install selected Pendulum 3.3.0 and passed `pip check`.

`poetry export --with dev` (without optional extras) succeeds. `poetry export --with dev --all-extras` fails in Poetry's exporter because it elects urllib3 2.2.2 while the Python <3.10 botocore marker requires `urllib3 >=1.25.4,<1.27`. The actual Poetry all-extras install completed, so this exporter failure is recorded separately from pip install behavior.

## Direct-dependency scope notes

| Dependency | Evidence from this review | Inventory status |
|---|---|---|
| FastAPI | Imported by the core decorator/coder code | Core runtime dependency |
| Pendulum | Imported by `fastapi_cache/coder.py` for date/datetime decoding | Core runtime use; lock version 3.0.0 also has the missing `time-machine` metadata issue above |
| Uvicorn | `uvicorn.run()` appears in examples; no core import found | Candidate to move out of mandatory runtime dependencies; no change in this PR |
| Jinja2 | Core imports Starlette's private `_TemplateResponse` in `fastapi_cache/coder.py` to exclude template responses from `PickleCoder`; Starlette 1.3.1 raises an import error from `starlette.templating` when Jinja2 is absent. Template rendering itself remains in examples. | Keep the direct dependency while this private Starlette import remains. The Jinja advisories require untrusted template content and do not indicate a template-execution path in `fastapi-cache` itself. |
| Redis, aiomcache, aiobotocore | Optional project extras | Keep their separate support/experimental status in the remediation decision |

## Decisions required before RC

1. The maintainer confirmed separate contracts: stable metadata `>=3.8,<3.14`, functional legacy tests on 3.8–3.10, and security support on 3.11–3.13. Python 3.14 remains excluded pending full CI.
2. PR #25 updates locked h11 to 0.16.0 and httpcore to 1.0.9 to remediate the request-smuggling parser finding and satisfy the HTTPX transport constraint; verify this lock remediation in CI. Fresh PyPI installs already resolve patched h11 0.16.0 on Python 3.8+.
3. Classify AnyIO/Starlette advisories by trigger. The library has no direct calls to AnyIO TLS APIs or Starlette form/static-file/HTTPEndpoint paths, but consumer applications may use them; EOL status alone is not an applicability disposition.
4. Triage optional DynamoDB/aiohttp/urllib3 findings by extra and Python version; do not assume lock alerts equal vulnerabilities in a default pip install.
5. Repair the Poetry lock's Pendulum `time-machine` mismatch and select a reproducible method for exporting all extras.
6. Uvicorn remains used by examples; Jinja2 stays direct while the core imports Starlette's private `_TemplateResponse` type.

The original 2026-11-16 snapshot changed no package versions. PR #25 restores legacy marker resolution and includes only the targeted h11 0.16.0/httpcore 1.0.9 lock remediation; it does not upgrade the test-tool dependency set. The remediation must pass CI and the supported security matrix before stable.
