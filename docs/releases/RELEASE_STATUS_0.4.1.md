# 0.4.1 release status and evidence

**Status:** published **2026-11-20**.
This is a post-release evidence record, not a guarantee about consumer applications.

## Release scope

Factory-generated and wrapped FastAPI handler cache-key isolation (#68),
including `functools.wraps` handlers with default-bound values; the
docs-only Towncrier gate (#67/#71) and a changelog correction for the
already-shipped 0.4.0 changes (#44/#46). No versioned metadata ranges or
Redis backend semantics change.

## Release identifiers and evidence

- Exact PR head: `0f26788dac3eced92e96b81045920163696deabb`.
- 48 unique checks green on the PR; full Python 3.8–3.13/Redis matrix,
  lint, typecheck, security audits, wheel/sdist and CodeQL passed.
- Factory collisions fixed in HTTP InMemory and real Redis 7 tests;
  default-bound `functools.wraps` regression covered; old keys not reused;
  module-level unwrapped keys unchanged; namespace clearing covered.
- Annotated tag `v0.4.1`: object `2977b1ab3613fcbe2405eab5605fb37f0e4e713b`;
  peeled release commit `ed1000bc09f7a17e3d93767e97d55eef77f5605b`.
- [TestPyPI workflow 44771878983](https://github.com/agustin18/fastapi-cache/actions/runs/44771878983): success.
- [Production PyPI workflow 44772219414](https://github.com/agustin18/fastapi-cache/actions/runs/44772219414): success.
- Wheel SHA-256 `a68c770ebdd6dff06e7a6b282b71be1a60dc020b7d3f0b971c307a83489d708d`;
  sdist SHA-256 `e171db38e12b8a5b1815a5d781018b39d4af883be0d65ed01a6162cfeb0417af`.
- TestPyPI, PyPI and the workflow artifact were byte-identical. PyPI provenance
  binds both files to `stable`, commit `ed1000bc09f7a17e3d93767e97d55eef77f5605b`
  and run `44772219414`; transparency entries verified.
- Direct PyPI installation, sdist installation and `pip check` passed; the
  factory/`functools.wraps` default-bound regression passed on the final wheel.
- The pre-publication Dependabot delta reported 120/120 records, 21 unchanged
  open alerts and no new material findings.
