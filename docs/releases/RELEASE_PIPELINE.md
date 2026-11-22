# Reusable release pipeline contract

The package's final release version comes from `pyproject.toml`. The
release-owned script `scripts/release_contract.py` validates the package
identity and final `X.Y.Z` version and derives the immutable Phase B bundle
name. Workflows do **not** store the current release version or artifact ID.

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
