# 0.4.1 release status and evidence

**Status:** release preparation; not published yet.
This file will be updated with the final tag, TestPyPI/PyPI workflow runs,
artifact hashes and provenance after the maintainer-authorized publication.

## Release scope

Factory-generated and wrapped FastAPI handler cache-key isolation (#68),
including `functools.wraps` handlers with default-bound values; the
docs-only Towncrier gate (#67/#71) and a changelog correction for the
already-shipped 0.4.0 changes (#44/#46). No versioned metadata ranges or
Redis backend semantics change.

## Pre-publication verification

- Exact PR head: `0f26788dac3eced92e96b81045920163696deabb`.
- 48 unique checks green on the PR; full Python 3.8–3.13/Redis matrix,
  lint, typecheck, security audits, wheel/sdist and CodeQL passed.
- Factory collisions fixed in HTTP InMemory and real Redis 7 tests;
  default-bound `functools.wraps` regression covered; old keys not reused;
  module-level unwrapped keys unchanged; namespace clearing covered.
- Final 0.4.1 wheel/sdist build, installation, hashes, TestPyPI/PyPI runs
  and provenance remain pending.
