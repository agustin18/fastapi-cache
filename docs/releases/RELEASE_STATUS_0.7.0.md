# 0.7.0 release status and provenance

**Published:** 2026-11-24 on [PyPI](https://pypi.org/project/fastapi-cache-stable/0.7.0/)
and [GitHub Releases](https://github.com/agustin18/fastapi-cache/releases/tag/v0.7.0).

## Final release record

| Item | Evidence |
|---|---|
| Final source SHA | `df884644f11eb0e36ae5d74721009fc8e4470c4b` |
| Annotated tag | `v0.7.0` |
| Phase B | [run 45252714837](https://github.com/agustin18/fastapi-cache/actions/runs/45252714837), attempt 1, 20/20 jobs |
| TestPyPI | [run 45296557093](https://github.com/agustin18/fastapi-cache/actions/runs/45296557093), hashes matched |
| PyPI | [run 45296858482](https://github.com/agustin18/fastapi-cache/actions/runs/45296858482), hashes matched |
| Wheel SHA-256 | `4c6338a27ac663a26ae23cfca975005736282764609aacba4e7e7febcde1a8a3` |
| Sdist SHA-256 | `ebefd6a0010a55fd73603e2fd882562951358d98954ce0de1a49114aad1a38b1` |
| Security review | [issue #126](https://github.com/agustin18/fastapi-cache/issues/126) |

The AI technical counteraudit and maintainer human review are recorded in
#126. The AI review is supplementary evidence, not third-party human
certification. The 21 open Dependabot alerts were classified as application
or legacy conditional; the tested all-extras profile resolves patched
`urllib3==2.8.0`, and the tested security profiles report zero known
third-party findings. `fastapi-cache-stable` itself is skipped by `pip-audit`
until indexed, so source/artifact review remains documented.

The previous `0.6.0` record remains immutable. This release makes no
performance, p95/p99, default Redis retry-latency or HA claim.

> **Known PyPI metadata caveat:** the published 0.7.0 long description was
> built from the pre-publication README and still says the latest release is
> 0.6.0. The repository README is corrected, but PyPI release metadata is
> immutable; correcting the project page requires a future release.
