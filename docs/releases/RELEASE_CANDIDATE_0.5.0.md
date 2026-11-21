# 0.5.0 candidate — release readiness and approval gates

**Released 2026-11-21.** [PR #82](https://github.com/agustin18/fastapi-cache/pull/82)
merged as `6a557eb3f28b617038ac1e3c8fd3af163db7ea22` after
**71/71 PR checks and Phase B 13/13 jobs** passed on PR HEAD
`bf0596fa44a0488d020d0268eb048e01d7918b3d`. The final release used a later
promotion SHA; see [status and provenance](RELEASE_STATUS_0.5.0.md) and
[PyPI](https://pypi.org/project/fastapi-cache-stable/) for the published artifact.
This record does not reopen or overwrite the
[historical 0.3.0 checklist](RELEASE_CHECKLIST.md)
or [published 0.4.1 provenance](RELEASE_STATUS_0.4.1.md).

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

## Completed candidate PR #82 — PR-HEAD evidence only

- [x] One `pyproject.toml` candidate version `0.5.0`; no new tag,
  distribution publication or dependency/lock metadata change.
- [x] [Phase-B workflow](../../.github/workflows/migration-candidate-phase-b.yml)
  builds **one wheel and one sdist from the PR HEAD**, attaches exact
  SHA-256 and SHA-linked provenance, validates wheel METADATA, sdist
  pyproject version and both files' integrity in downstream jobs.
- [x] Every **Python 3.8–3.13 × wheel/sdist** lane clean-installs
  published upstream 0.2.2 separately from the version-stamped
  0.5.0 file; passes `pip check` and real Redis 7.4 migration.
- [x] **Actual package rollback:** uninstall candidate and install
  upstream 0.2.2 in the candidate venv, verify compatible ordinary
  persisted entry and `pip check`; do not claim private rollback safe.
- [x] Independent consumer clean-installs the **same exact candidate**
  file, verifies module comes from site-packages, golden default key,
  InMemory HTTP MISS/HIT/304/error/auth and Redis/Vary MISS/HIT/304.
  Modern redis-py 8.1 on supported newer Python, redis-py 4.6 on
  legacy interpreters, with exact installed versions in evidence.
- [x] Full PR CI, modern security profiles, CodeQL, Redis, changelog,
  docs hygiene and wheel/sdist build green on the PR's **exact SHA**.

## Final release SHA gates — completed

Final release: tag `v0.5.0` (object `497f0ca8c481988b55b03e8ab3fc952f65c1b9fb`,
release commit `40c86d551b760315f3c6e99f383d6868c6294870`), Phase B run
44851661315 (13/13), security profiles 44851664008 (7/7), Dependabot delta
44851667159 (exit 0), TestPyPI 44852139879, PyPI 44852386994. Wheel
`7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449`;
sdist `e5dfe2fb5a16cb790e98bfb5e57377d835adc55579b0fdf1cb1d0afbf610ba0b`.


- [x] Repeat the Phase-B workflow **via workflow_dispatch on the
  final `stable` SHA**, or its exact release-intended SHA. **Any
  source/docs/version change afterward invalidates that signoff
  until the exact artifacts are rebuilt and rechecked.**
- [x] Archive actual SHA-256 for wheel **and** sdist, Git commit,
  GitHub run ID, exact Python/framework/client/Redis profiles,
  `pip check` and independent consumer evidence.
- [x] [#66](https://github.com/agustin18/fastapi-cache/issues/66):
  repeat installed-distribution modern Python 3.11–3.13 audits
  on exact final artifacts; check coverage completeness and `pip check`.
  Known legacy-only vulnerabilities are **not claimed patched**.
- [x] Run existing **authenticated** Dependabot delta near release,
  reconcile new/reopened/worsened findings and the remaining historical
  critical/high alerts by package/profile/reachability. Do **not**
  dismiss unresolved alerts for cosmetics.
- [x] Record explicit scoped **0.5.0** risk decisions and
  independent security/migration review. The historic 21-alert
  disposition from the 0.3.x release is not automatic consent.
- [x] Reconfirm no broken historical default key goldens, unintended
  downgrade in private/default auth semantics, or consumer-installed
  `fastapi_cache` namespace collisions.
- [x] **Promotion documentation and changelog:** verify the final
  README/long-description, SUPPORT, SECURITY, MIGRATION, COMPATIBILITY,
  ROADMAP, release notes and tests contain no false time-sensitive
  publication claim; generate 0.5.0 CHANGELOG using Towncrier, consume
  release fragments, and confirm final installed wheel/sdist includes it.
  A new source SHA invalidates prior candidate hash approval: rebuild
  both distributions and repeat #69/#66 exact-artifact checks.
- [x] Explicit manual signoff to create an annotated `v0.5.0` tag,
  TestPyPI testing, production PyPI publish and GitHub release.
  Verify publishing workflows against the same approved source SHA.

**Stop condition:** do not ship 0.5.0 if any exact-final-artifact
migration/security check is red or an applicable unmitigated
package-controlled critical/high vulnerability lacks a reviewed
fix/mitigation. Running CI on a PR merge ref, a previous commit,
a different version, or the published 0.4.1 baseline is insufficient.
