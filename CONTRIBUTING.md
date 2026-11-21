# Contributing

Thanks for helping maintain `fastapi-cache-stable`. This project is a drop-in fork of
`fastapi-cache2`; compatibility and small, reviewable changes matter more than feature
volume.

## Branch model

- `stable` is the only maintained and release branch. Open pull requests against it.
- `main` mirrors the upstream project. Do not open pull requests against `main`.
- Use a focused branch name:
  - `chore/quality-baseline`
  - `fix/575-error-response`
  - `fix/clear-semantics`
  - `test/pydantic-decode`
  - `docs/migration-guide`

## Development setup

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e . pytest httpx coverage diff-cover ruff==0.17.5 pre-commit
# Python >=3.10 modern Starlette TestClient profile; omit for Python 3.8/3.9 legacy tests.
if python -c "import sys; raise SystemExit(sys.version_info < (3, 10))"; then pip install httpx2; fi
pre-commit install
```

Run the local checks:

```sh
ruff check .
pytest -q
REDIS_URL=redis://localhost:6379/0 REQUIRE_REDIS=1 pytest -q tests/test_redis_clear.py
python -m build
twine check dist/*
```

The optional backend tests need their extras installed first. Without them the tests skip
instead of failing, so a plain `pytest -q` stays green but does not exercise those backends:

```sh
pip install -e ".[memcache,dynamodb]"
pytest -q tests/test_memcached_backend.py tests/test_dynamodb_backend.py
```

## Quality gates

Blocking for every pull request:

- `ruff check .`
- Functional `pytest` on Python 3.10–3.13
- `legacy-compat` on Python 3.8/3.9 with FastAPI 0.111.1 and Pydantic 1.10.27/2.8.2, plus
  Python 3.10/3.11 with Pydantic 1.10.27
- Poetry lock profiles on Python 3.8/3.9/3.10/3.12: legacy installs omit the DynamoDB extra;
  Python 3.10/3.12 lock profiles require fixed AnyIO/aiohttp versions.
- `legacy-smoke`: wheel install and MISS/HIT on Python 3.8
- `redis-clear`: Redis 7 integration tests (CI service)
- `optional-backends`: Memcached and DynamoDB unit tests with fake clients
- `security-audit`: fresh runtime+extras profile with FastAPI standard runtime extras on
  Python 3.11–3.13; development-only packages are excluded
- changed-line coverage with `diff-cover` for runtime changes
- `python -m build` and `twine check`
- clean-install smoke test for wheel and sdist
- `pre-commit run --all-files`
- Conventional Commits PR title
- no secrets, no private files, no auto-merge

Dependency/security maintenance after 0.3.0:

- Preserve the [bounded 0.3.0 GHSA decision](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
  On release candidates or dependency/security changes, collect a **fresh delta**:
  review new, reopened or materially changed findings and any newly reachable
  package-controlled path. **Do not reapprove 21 unchanged scoped advisories
  for every documentation or bugfix PR.**
- EOL Python alone never closes an applicable finding; a new exploitable
  critical/high issue in package-controlled code blocks a release until
  fixed or appropriately mitigated.
- Keep consumer-owned Starlette/AnyIO/urllib3 routes separate from our
  inspected package paths, and review experimental backend dependencies
  when those backends change. Do not dismiss alerts as fixed without evidence.
- For a released version, separate documented historical risk acceptance
  from the installed dependency inventory and the current app's threat model.

Baseline gates (ratchet, do not regress):

- `mypy` on changed Python files (blocking); full-repo `mypy`/`pyright` is a follow-up
- overall coverage
- Markdown link checks

Tool versions:

- Ruff is pinned to the `0.17.x` series in `pyproject.toml` and `poetry.lock`; CI uses
  `0.17.5`.
- Stable package metadata is `>=3.8,<3.14`. Mypy/Pyright target Python 3.11.
- Python 3.8–3.10 are legacy functional-compatibility targets with no security-support
  commitment; Python 3.11–3.13 are the security-supported matrix. Python 3.14 is excluded
  until its full functional matrix passes.
- `httpx2` is a test-only dependency for the modern Starlette TestClient profile; do not add it
  to runtime dependencies. The legacy 3.8/3.9 jobs use pinned `httpx` and FastAPI instead.
- `stable` requires a pull request and the CI checks; force pushes and branch deletion are
  blocked.
- The `pypi` environment only allows `stable` and `v*` tags and has a 5-minute wait timer.
  The timer is not a human approval step; required reviewers are a future step when a
  co-maintainer joins.

## Pull request title

Use Conventional Commits:

```text
type(scope): imperative summary
```

Examples:

```text
chore(ci): add quality gates for stable
fix(decorator): do not cache error responses (#575)
fix(backends): bound namespace clearing to key boundaries (#578)
test(codecs): cover typed decode for Pydantic and dataclasses (#576)
```

Rules:

- imperative, lowercase, no trailing period
- at most 72 characters
- reference the upstream issue or PR when applicable

## Pull request body

Use this structure:

```markdown
## Summary
## Motivation
## Behavior change
## Tests
## Compatibility
## Migration notes
## Checklist
- [ ] Tests added/updated
- [ ] Changelog fragment
- [ ] Docs updated
- [ ] No secrets
- [ ] Backward compatibility reviewed
## Related
```

- Write `None` in `Behavior change` for infrastructure-only pull requests.
- `Compatibility` covers imports, public API, cached data, headers and key format.
- `Migration notes` links to `MIGRATION.md` or says `None`.
- `Related` credits upstream issues and pull requests.

## Formatting

- Keep the existing 80-column style; do not reformat unrelated code.
- Run `ruff format` only on files you create or change.
- A dedicated style pull request may normalize the repository later; do not mix it with
  behavior changes.
- Keep imports sorted and type hints consistent with the surrounding code.
- Add docstrings to new public APIs; avoid unnecessary comments.

## Compatibility rules

- Keep the `fastapi_cache` import and the public API stable.
- Preserve the normal success path for GET endpoints.
- Treat a behavior change as a bug fix only when it is documented in `MIGRATION.md` and
  covered by a regression test.
- Do not change the cache key format, ETag format or serialization without a migration note
  and a cache-flush recommendation.
- Do not cache authenticated responses by default.
- Do not add a feature to a patch release.

## Changelog

User-facing changes need a towncrier fragment in `changelog.d/`:

```sh
# bugfix, feature, doc, removal or misc
touch changelog.d/575.bugfix.md
```

Infrastructure-only pull requests can use the `skip-changelog` label.

## Review protocol

1. Author self-review: diff, tests, docs, compatibility, secrets, size.
2. Automated gates: CI, lint, types, tests, build, smoke, changed-line coverage.
3. External review when requested: read-only review of the exact diff and evidence.
4. Address findings and re-run the gates. A material change needs a delta review.
5. Merge only with explicit maintainer approval. There is no auto-merge.

## Release

- Releases are cut from `stable` only.
- The release commit must pass the full test matrix.
- Release readiness is based on correctness, supported-runtime compatibility,
  applicable installed-distribution/integration tests, security review,
  version-accurate documentation, provenance and explicit maintainer approval.
- Maintainer-authored tests, synthetic integration fixtures and optional private
  application tests are valid technical evidence within their scope. Describe
  evidence accurately; do not expose private application details.
- **No minimum number of external consumers, deployments, testimonials or
  third-party application validations is required for releases or announcements.**
  User reports and feedback are welcome but voluntary. Do not imply independent
  adoption, production certification or universal security without evidence.
- The annotated release tag must match the version in `pyproject.toml`.
- For the 0.6.0 train, use the same reviewed wheel/sdist pair from the final
  stable Phase B run for installed security, TestPyPI and PyPI; verify exact
  source/run provenance and individual hashes. Requalify any changed artifact.
  See [the candidate checklist](docs/releases/RELEASE_CANDIDATE_0.6.0.md).
- TestPyPI publishing uses the manual `publish-testpypi.yml` workflow and the `testpypi`
  environment. It never runs on `release: published`.
- PyPI publishing is manual-only via `workflow_dispatch`; it never runs on
  `release: published`.
- PyPI publishing uses Trusted Publishing and the protected `pypi` environment.
- Do not publish without an explicit maintainer decision.

## Reporting bugs and feature requests

Open an issue on the repository. Two forms are available:

- **Bug report** for a reproducible defect. Include the package, Python, FastAPI and Pydantic
  versions, the backend, and a minimal reproduction.
- **Feature request** for a proposal. This project is a drop-in fork of `fastapi-cache2`, so
  compatibility and small changes are prioritized; a request is a proposal, not a commitment.

Do not paste passwords, tokens, cookies, private data, or AWS credentials into an issue.
Redact secrets from logs and configuration first. Blank issues are disabled so that reports
arrive with the information needed to triage them.

## Reporting security issues

Do not open a public issue for a vulnerability. Use
[GitHub private vulnerability reporting](https://github.com/agustin18/fastapi-cache/security/advisories/new).
See `SECURITY.md`.
