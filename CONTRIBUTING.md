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
pre-commit install
```

Run the local checks:

```sh
ruff check .
pytest -q
python -m build
twine check dist/*
```

## Quality gates

Blocking for every pull request:

- `ruff check .`
- `pytest` on Python 3.10–3.13
- changed-line coverage with `diff-cover` for runtime changes
- `python -m build` and `twine check`
- clean-install smoke test for wheel and sdist
- `pre-commit run --all-files`
- Conventional Commits PR title
- no secrets, no private files, no auto-merge

Baseline gates (ratchet, do not regress):

- `mypy` on changed Python files (blocking); full-repo `mypy`/`pyright` is a follow-up
- overall coverage
- `pip-audit`
- Markdown link checks

Tool versions:

- Ruff is pinned to the `0.17.x` series in `pyproject.toml` and `poetry.lock`; CI uses
  `0.17.5`.
- Mypy and Pyright target Python 3.10; the package metadata still allows 3.8/3.9 until the
  first beta reconciliation.
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
- The tag must match the version in `pyproject.toml`.
- PyPI publishing uses Trusted Publishing and the protected `pypi` environment.
- Do not publish without an explicit maintainer decision.

## Reporting security issues

Do not open a public issue for a vulnerability. Use GitHub private vulnerability reporting
once it is enabled for the repository. See `SECURITY.md`.
