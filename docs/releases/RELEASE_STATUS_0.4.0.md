# 0.4.0 release status and evidence

**Status:** published **2026-11-20**.
This is a post-release evidence record, not a substitute for reviewing
present-day vulnerability status or a guarantee about consumer applications.

## Immutable release identifiers

- PyPI package: [fastapi-cache-stable==0.4.0](https://pypi.org/project/fastapi-cache-stable/0.4.0/)
- GitHub Release: [v0.4.0](https://github.com/agustin18/fastapi-cache/releases/tag/v0.4.0)
- Annotated tag `v0.4.0`: object `5dc45644084fa4d54b6060d1d32b37a8e1bd9c41`;
  peeled release commit `8d2dfe2ec5c74dbfac394b468a6bf13445f920d1`.
- `stable` was at that release commit when TestPyPI/PyPI were published.
- [TestPyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44670736227): success.
- [Production PyPI workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44670980627): success.

## Published distribution digests

| File | SHA-256 |
|---|---|
| `fastapi_cache_stable-0.4.0-py3-none-any.whl` | `dfb887cc79e10b2d9dd91d1c516a35f1266dcf60e37cfcf52fd553d06158bbeb` |
| `fastapi_cache_stable-0.4.0.tar.gz` | `53e6635c78f10ae0c206891216c10f0689eea7cc3e87181a70f9540a71f696b2` |

The final local build, TestPyPI, PyPI and the production workflow artifact all
produced these exact bytes. PyPI provenance binds both files to `stable`,
commit `8d2dfe2ec5c74dbfac394b468a6bf13445f920d1` and run `44670980627`, with
transparency entries. TestPyPI published the same bytes; installation from both
indexes and the final local wheel passed `pip check` and the smoke checks.

## Verification

- Final-wheel and sdist metadata, conditional Redis requirements, clean
  installations and `pip check` are part of the release workflow.
- The final wheel is exercised against Redis real-server profiles and the
  installed-wheel FastAPI consumer probe.
- The final wheel was also checked in a disposable `real-estate-arg` worktree
  with redis-py 4.6.0, 7.2.1, 8.1.0 and rollback to 4.6.0; 48 tests passed per
  profile, `pip check` passed, and the consumer used RedisBackend against a
  real standalone Redis 7.4.7. This is maintainer evidence, not an archived
  independent consumer CI job.
- Pre-production Dependabot delta: 120 historical/current records, 21
  unchanged open alerts, no new or reopened material findings, exit 0.
- The prior `0.3.x` artifacts remain immutable.

## Scope and residual risks

Standalone Redis, RESP2/RESP3, ACL authentication and binary caching with
`decode_responses=False` are in scope. Redis Cluster, Sentinel/failover, TLS
and managed-provider transports are not certified; Cluster namespace clearing
remains `NotImplementedError`. The explicit-`Request` bypass from 0.3.1 is
inherited by 0.4.0; `Vary` and hidden context remain tracked in issue #53.
The 21 open GHSA acceptance remains scoped to the 0.3.x/0.4.x reviewed
evidence and is not a claim that those advisories are fixed.

Next work is tracked in [ROADMAP.md](../../ROADMAP.md).
