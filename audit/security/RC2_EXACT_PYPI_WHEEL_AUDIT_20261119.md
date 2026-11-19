# Exact published PyPI RC2 wheel — runtime security audit (2026-11-19)

**Evidence from the published, hashed wheel**, independently of the source-build CI.
This is a point-in-time audit, not a vulnerability-free guarantee, and does
**not** remove or dismiss any legacy Python/Poetry-lock Dependabot alerts.

## Source, publication and immutable hash

- Tag `v0.3.0rc2` on commit `277b6e71dac5c2807acdbc11366a7864aec1927a`.
- Version `fastapi-cache-stable==0.3.0rc2`, fetched directly from the **PyPI**
  simple index with `--no-cache-dir --no-deps --only-binary=:all:`.
- Expected and verified wheel SHA-256:
  `2c3f35e053770edd708c42e88e1d2d788bc3c2ed6e2bb3d5b8409f48b79762bf`.
- Published sdist SHA-256 (verified by publication logs but **not**
  installed for this workflow):
  `145df1aada6deafc90faa3558589b8ac91276fb14eadf28e78e250032998fa1e`.
- The [temporary exact-wheel audit workflow](https://github.com/agustin18/fastapi-cache/actions/runs/44465589850)
  completed **SUCCESS**. The temporary YAML was removed from the proposed
  final stable-readiness PR; run and retained artifacts provide provenance.

## Resolved install and audit results

Each job installed `fastapi-cache-stable[all]` **from the downloaded wheel**
plus `fastapi[standard-no-fastapi-cloud-cli]` with normal dependency
resolution (separate clean venv checked by `pip check`). A separate
`--target` install was audited with `pip-audit==2.10.1` using the same
completeness validator as repository CI. It compared installed inventory,
`wheel-METADATA.txt`, and full JSON report, refusing missing packages.

| CPython | Wheel SHA match | `pip check` | Installed distributions | Third-party audited | Findings |
|---|---|---|---:|---:|---:|
| 3.11 | PASS | PASS | 73 | 72 | 0 |
| 3.12 | PASS | PASS | 73 | 72 | 0 |
| 3.13 | PASS | PASS | 73 | 72 | 0 |

**Evidence artifacts** (Github Actions retention: 90 days):
- [Python 3.11 job](https://github.com/agustin18/fastapi-cache/actions/runs/44465589850) — artifact `exact-pypi-rc2-python-3.11`, ID `14501084868`
- [Python 3.12 job](https://github.com/agustin18/fastapi-cache/actions/runs/44465589850) — artifact `exact-pypi-rc2-python-3.12`, ID `14502585087`
- [Python 3.13 job](https://github.com/agustin18/fastapi-cache/actions/runs/44465589850) — artifact `exact-pypi-rc2-python-3.13`, ID `14502455383`

Each artifact contains `wheel.sha256`, Python version, published wheel
`METADATA`, installed package inventory and `pip-audit.json`.
The workflow logs show `No known vulnerabilities found` and
`finding_count: 0` in all three jobs.

## Interpretation, not a blanket security claim

- These results show the **modern, server-side CPython 3.11–3.13 resolver**
  profiles with all extras selected **on the scan date** have no findings
  recognized by the chosen `pip-audit` advisory database.
- The repository's Python 3.8/3.9 legacy locked profiles retain vulnerable
  AnyIO 4.5.2 and Starlette 0.44.0; they are **outside security support**.
- The scan does not exercise every consuming application's extra dependencies,
  network endpoints or custom Starlette file-serving routes.
- The source `poetry.lock` is a test/development matrix, **not the wheel's
  installed runtime lock**. Alerts in one do not automatically imply an
  affected modern wheel, but require individual scope review.
- Before promoting `0.3.0`, maintainers must sign off on the 21
  still-open advisories in the captured graph, check for newer GHSA, and
  re-run scans on the **new 0.3.0 wheel**, which will have different bytes,
  metadata and SHA-256.

See the [95-row pre-stable release ledger](STABLE_RELEASE_SECURITY_REVIEW_20261119.csv)
and [review document](STABLE_RELEASE_SECURITY_REVIEW_20261119.md).
