# CPython 3.14 qualification — diagnostic evidence record

Status: **PASS for the diagnostic qualification scope (2026-11-25)**.
No Python 3.14 support claim, release metadata change, publication authorization
or runtime fix. Final release artifacts require separate qualification.

Base: `dcff6c39bd133ebe36b6acc78d557cc1196a8636` (merged #141). Issue #51.
Tested source: `4dcfc0e3ec0496b92d10ff6b965364c50abdc32d`.
[Qualification run 45695855256](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256): **7/7 successful jobs**.
Each downloaded evidence archive records this exact source SHA. The subsequent
evidence-only documentation commit does not change the qualification workflow,
package source, tests, lock or metadata. Its own CI is required before merge.

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

## Results and evidence

CPython 3.14.10 (standard GIL-enabled build) was tested against a CPython
3.11.18 control. The real Redis service was 7.4.12; redis-py was 8.1.0.
The commands are recorded in the qualification workflow and its run logs.
All seven evidence ZIPs were downloaded and inspected.

| Lane | Result | Evidence archive ID |
|---|---|---|
| 3.11 wheel + Redis 7.4 control | PASS — 591 passed, 18 skipped | [15061565756](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15061565756) |
| 3.14 wheel + Redis 7.4 | PASS — 591 passed, 18 skipped | [15061620660](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15061620660) |
| 3.14 sdist + Redis 7.4 | PASS — 591 passed, 18 skipped | [15060787162](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15060787162) |
| 3.14 optional all-extras wheel | PASS — 17 passed, 0 skipped (fake clients) | [15061910104](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15061910104) |
| 3.14 core security | PASS — 18 installed, 17 third-party audited, 0 findings | [15061790352](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15061790352) |
| 3.14 Redis security | PASS — 19 installed, 18 third-party audited, 0 findings | [15060356930](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15060356930) |
| 3.14 all-extras security | PASS — 35 installed, 34 third-party audited, 0 findings | [15061585643](https://github.com/agustin18/fastapi-cache/actions/runs/45695855256/artifacts/15061585643) |

JUnit reports record 609 collected tests, no failures or errors in each
full-suite lane. The 18 skips have the same reasons as the control:
aiobotocore, aiomcache and fastapi_pagination are not installed in the
core/Redis test profile. The separate optional lane runs the 17 fake-client
tests without skips. The installed InMemory and Redis Vary consumer probes
passed for the control and both 3.14 distribution lanes; import paths are
under site-packages. All functional lanes passed pip check and twine check.

### Original and diagnostic distribution identity

The original SHA-256 manifests match the published 0.7.1 record in all
four functional evidence archives:

- Wheel: `54d64e3f24110f434d2a1b765006e528302d5550ad0b4ce20b8eb706a49e9aa3`
- Sdist: `c3fa245c9212ec292c43523e1402baad75da4571bbac0832380020c2205426d5`

The temporary 3.14 diagnostic distributions have distinct identities:

- Wheel: `18901e4c66540f7128e0fb811b8a0687880b1b5000ca0779e6625959757b6247`
- Sdist: `a76389589dc7e3f52a62697a8e0a40285d72945f2553e4656dd66c82dae116eb`

All three security archives record the same diagnostic wheel SHA-256.
These hashes are runner-recorded manifests, not a new independent rebuild
or download of the distribution bytes. The ZIPs contain evidence, not the
release distribution pair. Never publish the diagnostic distributions.

### Security and failure history

The earlier [run 45694397934](https://github.com/agustin18/fastapi-cache/actions/runs/45694397934)
on `e8b7705fff304d8e4ebe0e8815d095667834646d` passed all four
functional lanes but failed all three security lanes because the command
used `python -m pip-audit`. No audit JSON or completed validator result was
produced. The correction calls the installed `pip-audit` console script
for both version and audit invocations. The validator was not relaxed.

On the corrected run, pip-audit 2.10.1 reports zero findings and zero
skipped records in each diagnostic environment. The existing strict
validator passed all three inventories; the first-party package is
present in each report and is excluded from the third-party count. This
is point-in-time installed dependency evidence, not certification of the
unpublished 0.7.2 artifact or its source. The diagnostic distribution uses
the already-published 0.7.1 version identity.

### Limits and recommendation

No existing CI lane, test or lock profile is removed or weakened. No
`continue-on-error` is used. Real Memcached/DynamoDB service conformance,
free-threaded 3.14t, Python 3.15, the final 0.7.2 lock resolution,
exact-artifact Phase B and its fresh authenticated security delta are
**NOT RUN / out of scope for this diagnostic**. No runtime incompatibility
was found in the exercised scope; no runtime fix is required by this
evidence. Local CPython 3.14/Redis execution was unavailable; qualification
was performed by GitHub Actions.

**Recommendation:** GO for independent review of the diagnostic
qualification record, conditional on the complete PR CI and exact diff
review. Do not widen the published support contract or publish from this
PR. The subsequent staging PR must establish the release-shaped matrix
and validate the exact final artifacts separately.

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
