# CPython 3.14 qualification — diagnostic evidence plan

Status: **NOT RUN / draft recognition**. No Python 3.14 support claim,
release metadata change, publication authorization or runtime fix.

Base: `dcff6c39bd133ebe36b6acc78d557cc1196a8636` (merged #141). Issue #51.
The qualification workflow records the exact tested head SHA in each evidence
archive; this file does not claim an unknown future commit hash.

## Baseline and reproducibility

The published 0.7.1 range is `>=3.8,<3.14`; the modern Redis marker also
ends at 3.14. The existing metadata tests intentionally reject a 3.14
support claim. The workflow builds original distributions and, on 3.14,
builds separate diagnostic distributions from a git archive with only the
two temporary Python ceilings relaxed. Neither checkout nor lock is edited.
The original version is retained for the tests; diagnostic artifacts must
never be uploaded to a package index or substituted for Phase B.

Run the workflow **CPython 3.14 qualification (experimental)** against the
draft PR head. Download the named evidence archives and inspect commands,
Python versions, source SHA, hashes, dependency freezes, test counts, skip
reasons and the audit inventory. For the unchanged full source suite on
3.14, dependencies are resolved normally from the relaxed diagnostic
distribution, then only the original project wheel is reinstalled with
`--no-deps --ignore-requires-python` to exercise the unchanged metadata
assertions. This is explicitly not an ordinary 3.14 consumer install.
Installed consumer probes run first against clean diagnostic wheel/sdist
installs from outside the checkout. The 3.11 control uses the original
metadata throughout.

## Required and conditional lanes

| Lane | Expected evidence | Initial status |
|---|---|---|
| 3.11 wheel + Redis 7.4 control | Full unchanged suite, installed probes, pip check | NOT RUN |
| 3.14 wheel + Redis 7.4 | Same suite, installed probes, builds and hashes | NOT RUN |
| 3.14 sdist + Redis 7.4 | Same suite, installed probes, builds and hashes | NOT RUN |
| 3.14 optional all-extras wheel | Installs and fake-client Memcached/DynamoDB tests | NOT RUN |
| 3.14 core security | Runtime-only inventory, pip check, pip-audit completeness | NOT RUN |
| 3.14 Redis security | Same with Redis extra | NOT RUN |
| 3.14 all-extras security | Experimental optional graph audit | NOT RUN |

No existing CI lane, test or lock profile is removed or weakened. No
`continue-on-error` is used. Optional backend failures must be reviewed
and explicitly scoped; they are not silently treated as passes. No real
Memcached/DynamoDB service conformance is claimed. All diagnostics must
be reviewed, including any skips; the final evidence report must replace
NOT RUN with actual PASS/FAIL/NOT RUN and include exact commands/results.
The current execution environment has no local CPython 3.14/Redis service
or direct GitHub network access; remote CI is the first execution.

## Release staging — not this PR

Only after successful qualification and review, separately reconcile
Requires-Python, Redis markers, classifiers, Poetry lock consistency,
support tables, wheel/sdist metadata tests and documentation. Keep 3.8–3.10
functional legacy and the existing security-support matrix intact. A new
3.14 security claim requires applicable installed exact-artifact audits.
Update Phase B's strict job set, verifier and negative tests coherently:
the historical 20-job matrix cannot qualify 3.14. Select a compatible
modern framework profile or independently qualify cross-interpreter
migration and rollback if the historical profile does not install.

No public API, default key, ETag, serialization or behavior change, no
major dependency upgrade and no weakened gate is approved. Stop and
re-scope if any is needed. Free-threaded 3.14t and 3.15 are out of scope.
No tags, uploads or new release version are authorized here.
