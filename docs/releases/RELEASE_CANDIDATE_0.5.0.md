# 0.5.0 candidate — release readiness and approval gates

**Status: NOT RELEASED.** The latest published version remains
[0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/).
This checklist belongs to the **0.5.0** release train and does not
reopen or overwrite [historical 0.3.0 checklist](RELEASE_CHECKLIST.md)
or [0.4.1 signed provenance](RELEASE_STATUS_0.4.1.md).

## Completed prerequisites — historical, not candidate signoff

- [x] [#67](https://github.com/agustin18/fastapi-cache/issues/67)
  docs-only Towncrier CI gate closed.
- [x] [#68](https://github.com/agustin18/fastapi-cache/issues/68)
  generated/factory handler key-isolation shipped in published 0.4.1.
- [x] [#53](https://github.com/agustin18/fastapi-cache/issues/53)
  opt-in `vary_headers` contract and returned-Response `Vary`
  correction merged via [#81](https://github.com/agustin18/fastapi-cache/pull/81).
  **Issue remains open** for arbitrary hidden tenant/identity context and
  unbounded client-controlled header variation.
- [x] [#69 phase A](https://github.com/agustin18/fastapi-cache/issues/69):
  released upstream `fastapi-cache2==0.2.2` vs published fork
  `0.4.1`, golden keys, isolated venvs and Redis 7.4 rollback.
  This historical check does **not** audit 0.5.0.

## Candidate PR (#82) — must be green before merge consideration

- [ ] One `pyproject.toml` candidate version `0.5.0`; no new tag,
  distribution publication or dependency/lock metadata change.
- [ ] [Phase-B workflow](../../.github/workflows/migration-candidate-phase-b.yml)
  builds **one wheel and one sdist from the PR HEAD**, attaches exact
  SHA-256 and SHA-linked provenance, validates wheel METADATA, sdist
  pyproject version and both files' integrity in downstream jobs.
- [ ] Every **Python 3.8–3.13 × wheel/sdist** lane clean-installs
  published upstream 0.2.2 separately from the version-stamped
  0.5.0 file; passes `pip check` and real Redis 7.4 migration.
- [ ] **Actual package rollback:** uninstall candidate and install
  upstream 0.2.2 in the candidate venv, verify compatible ordinary
  persisted entry and `pip check`; do not claim private rollback safe.
- [ ] Independent consumer clean-installs the **same exact candidate**
  file, verifies module comes from site-packages, golden default key,
  InMemory HTTP MISS/HIT/304/error/auth and Redis/Vary MISS/HIT/304.
  Modern redis-py 8.1 on supported newer Python, redis-py 4.6 on
  legacy interpreters, with exact installed versions in evidence.
- [ ] Full PR CI, modern security profiles, CodeQL, Redis, changelog,
  docs hygiene and wheel/sdist build green on the PR's **exact SHA**.

## After candidate merge — exact final release SHA required

- [ ] Repeat the Phase-B workflow **via workflow_dispatch on the
  final `stable` SHA**, or its exact release-intended SHA. **Any
  source/docs/version change afterward invalidates that signoff
  until the exact artifacts are rebuilt and rechecked.**
- [ ] Archive actual SHA-256 for wheel **and** sdist, Git commit,
  GitHub run ID, exact Python/framework/client/Redis profiles,
  `pip check` and independent consumer evidence.
- [ ] [#66](https://github.com/agustin18/fastapi-cache/issues/66):
  repeat installed-distribution modern Python 3.11–3.13 audits
  on exact final artifacts; check coverage completeness and `pip check`.
  Known legacy-only vulnerabilities are **not claimed patched**.
- [ ] Run existing **authenticated** Dependabot delta near release,
  reconcile new/reopened/worsened findings and the remaining historical
  critical/high alerts by package/profile/reachability. Do **not**
  dismiss unresolved alerts for cosmetics.
- [ ] Record explicit scoped **0.5.0** risk decisions and
  independent security/migration review. The historic 21-alert
  disposition from the 0.3.x release is not automatic consent.
- [ ] Reconfirm no broken historical default key goldens, unintended
  downgrade in private/default auth semantics, or consumer-installed
  `fastapi_cache` namespace collisions.
- [ ] **Promotion documentation:** replace provisional `0.5.0 is not on
  PyPI` wording in README/long-description, SUPPORT, release notes,
  migration and version-specific guard tests with accurate release-stage
  wording **before publishing**. Ensure the package metadata contains no
  false availability claim. This creates a new source SHA: rebuild both
  artifacts, recompute SHA-256 and repeat #69 phase B and #66 exact-final-
  artifact checks. Never reuse a previously approved candidate hash.
- [ ] Explicit manual signoff to create an annotated `v0.5.0` tag,
  TestPyPI testing, production PyPI publish and GitHub release.
  Verify publishing workflows against the same approved source SHA.

**Stop condition:** do not ship 0.5.0 if any exact-final-artifact
migration/security check is red or an applicable unmitigated
package-controlled critical/high vulnerability lacks a reviewed
fix/mitigation. Running CI on a PR merge ref, a previous commit,
a different version, or the published 0.4.1 baseline is insufficient.
