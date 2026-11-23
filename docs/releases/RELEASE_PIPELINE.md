# Reusable release pipeline contract

The source distribution identity comes from `pyproject.toml`: while 0.7.0
is being developed it is `0.7.0.dev0`, distinct from the last published
`0.6.0`. The independently verified published-docs pointer lives in
`docs/releases/PUBLISHED_VERSION` and changes **only after** registry promotion.
README, install pins and the public docs describe that published artifact.

The release-owned script `scripts/release_contract.py` defaults to **final
`X.Y.Z` only** and derives the immutable Phase B bundle name. PR Phase B
explicitly passes `--allow-development` to test exact dev wheel/sdist builds,
but the `workflow_dispatch` final evidence path rejects dev versions.
A release promotion must first move `pyproject.toml` to the final
`0.7.0`, run tests, freeze SHA, and obtain fresh manual first-attempt
20-job Phase B plus independent artifact verification. Workflows do **not**
store the current release version or artifact ID.

## Safe dry-run before preparing 0.7.0

```console
python -m pytest tests/test_release_bundle.py tests/test_candidate_migration_workflow.py
python scripts/release_contract.py version
python scripts/release_contract.py artifact
```

`tests/test_release_bundle.py` runs a fully synthetic **0.7.0** manifest,
valid SHA-256 pair, provenance, first-attempt 20-job matrix and adversarial
wrong-version/hash/name/run/attempt/index variants. This verifies **validation
logic only**. It neither builds, tags nor uploads a 0.7.0 package.

On a release-intended 0.7.0 branch, first update `pyproject.toml` and the
appropriate public docs, version-sensitive test fixtures and changelog
with a reviewed promotion PR. Only after merge, freeze the actual final
`stable` SHA and run the **manual** Phase B workflow on that SHA. The
job must produce 1 wheel/sdist pair, 12 isolated Redis migration/rollback
lanes and seven installed security profiles. Record individual
distribution hashes and independently verify the downloaded files.

The publish jobs require explicit separate approvals; the annotated
matching tag must resolve to the final stable source commit. Both indices
retrieve the same versioned Phase B artifact and compare approved hashes;
PyPI additionally checks TestPyPI digest parity and a fresh authenticated
Dependabot delta. No rebuild or bypass of environment/trusted-publisher
controls is acceptable. Never reuse a 0.6.0 run or inferred archive hash.

Existing 0.6.0 tags, files and evidence remain immutable. This infrastructure
change is not an authorization to create another release.

## 0.7.0 evidence and contra-audit handoff

Before starting an actual 0.7.0 promotion, use the [candidate acceptance
checklist](RELEASE_CANDIDATE_0.7.0.md). An independent
[counteraudit request](../audit/COUNTERAUDIT_0.7.0_HANDOFF.md) is prepared as
a **template**, not a completed review. Audit the final exact SHA only after
all chosen functionality, documentation and accepted security/performance
budgets are frozen. An earlier PR-level CI pass cannot substitute for the
20-job final Phase B, first-attempt/provenance/digest gates, fresh authenticated
security delta, explicit TestPyPI/PyPI approvals and published-byte checks.
