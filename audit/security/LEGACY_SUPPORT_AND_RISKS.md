# Legacy Python compatibility and dependency security

**For fastapi-cache-stable 0.3.x.** The library deliberately keeps tested
functional compatibility with older Python interpreters, but that is **not**
equivalent to maintaining or fixing the vulnerabilities of their entire
dependency stacks. A compatible install is not a security certification.

| Python interpreter | Installation / functional tests | Security maintenance commitment | Recommended use |
|---|---|---|---|
| CPython 3.8 / 3.9 | Legacy CI, pinned FastAPI/Pydantic combinations, wheel smoke | **None**; known vulnerable AnyIO/Starlette versions remain in examined profiles | Migration bridge only; plan interpreter upgrade |
| CPython 3.10 | Legacy functional compatibility | **None** (Python 3.10 is EOL) | Migration bridge; plan upgrade |
| **CPython 3.11–3.13** | Verified functional matrix and published-wheel scans | **Best-effort 0.3.x security support** per [SUPPORT.md](../../SUPPORT.md) | **Recommended for production** within tested use cases |
| Python 3.14 and other runtimes | Not verified for this release | None for this release | Do not assume support |

The library requires Python `>=3.8,<3.14` for 0.3.x. This does not promise
that every optional extra or application dependency can be installed on every
interpreter in that range. DynamoDB is experimental, requires Python 3.10+,
and is not part of the Python 3.8/3.9 core-compatibility contract.

## What is inherited from fastapi-cache2?

`fastapi-cache2==0.2.2` and this fork both depend on FastAPI, which itself
uses Starlette and AnyIO. **If a consuming application installs an affected
version of a dependency and exercises the advisory's vulnerable path, the
risk can exist regardless of which cache distribution it chooses.**

It is **not correct** to claim that the two cache packages always install
identical or equally vulnerable dependencies. Each has its own requirement
ranges, extras and resolver result. For example, the **published** upstream `fastapi-cache2==0.2.2`
uses `redis ^4.2.0rc1`, the **same** client range as this fork's `0.3.x`
(which verifies redis-py 4.6.0). A later, **unreleased** upstream `main`
change uses `redis ^5.0.8`. Redis-py 5/6 support is planned work, not a
verified promise for either published package. Comparing two installations requires inspecting
their **actual installed versions and the application's lockfile**.

## Known legacy advisory examples

**Critical AnyIO [GHSA-82r6-8w77-94w6](https://github.com/advisories/GHSA-82r6-8w77-94w6)**
concerns affected AnyIO TLS connections involving internationalized hostnames.
The tested Python 3.8/3.9 legacy/Poetry profiles install AnyIO 4.5.2; the
fix is in AnyIO 4.14.2, which cannot be installed on those older interpreters.
The cache package does not directly implement the vulnerable `TLSStream` flow,
but **consumer applications and other dependencies may**. Do not assume that
normal caching use eliminates application-side TLS risk.

**High Starlette [GHSA-7f5h-v6xp-fcq8](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8)**
concerns `FileResponse` / `StaticFiles` on affected Starlette versions.
The Python 3.8/3.9 lock includes Starlette 0.44.0, which is affected.
The fork no longer mounts the unused `StaticFiles(directory="./")` route
in its Redis example. **A downstream application serving files with an
affected Starlette version is not repaired by installing this cache fork.**
The fix for this advisory starts in Starlette 0.49.1.

Other Starlette issues depend on application-owned form parsing, URL/path
handling or Windows file-serving routes. Some `urllib3` GHSA occur in the
historical development/optional dependency graph; no direct vulnerable
`urllib3` call was found in the inspected cache package path. This
finding does **not** clear independently used `urllib3` by the consumer.

For the point-in-time 2026-11-19 capture, see the
[21 open GHSA and proposed bounded decisions](MAINTAINER_RISK_ACCEPTANCE_20261119.md),
the [full 95-row register](SECURITY_ADVISORY_TRIAGE.csv) and the
[exact published RC2 wheel security scan](RC2_EXACT_PYPI_WHEEL_AUDIT_20261119.md).

## Practical security guidance for applications

1. **Prefer Python 3.11–3.13** and install current compatible FastAPI,
   Starlette, AnyIO and other runtime dependencies. Maintain your
   application's lockfile and vulnerability scanning. An import-compatible
   cache migration is not a substitute for an application security review.
2. If a Python upgrade is impossible, **inventory the actual installed
   dependencies** and match individual GHSA to reachable features. Restrict
   untrusted TLS destinations and file/form-serving paths where feasible;
   assess patches or compensating controls rather than assuming legacy
   installations are safe.
3. Never co-install `fastapi-cache2` and `fastapi-cache-stable`, since both
   distribute the `fastapi_cache` Python module. Test `pip check`, actual
   cache behavior and rollback in an isolated copy of the consumer.
4. With the default cache configuration, `Authorization` and `Cookie`
   headers bypass caching. Other custom authentication methods may require
   application-level isolation or a suitable identity-aware key builder.
5. Do not use `PickleCoder` with untrusted cache contents: malicious
   pickled bytes can execute code on deserialization.

## Maintainer release-security decision

For the published 0.3.0 release, the maintainer's decision was to
**accept only the specifically scoped residual risks** in the 21 open GHSA, while
keeping their raw Dependabot state as `open` where applicable. A conditional
or not-applicable finding means *not reachable in the inspected package path*
or *outside the supported profile*, not globally patched or risk-free.

Acceptance of an advisory **does not extend** the security support commitment
to Python 3.8–3.10 and **does not cover** consumer-owned network connections,
file-serving, form parsing, URL handling, independent `urllib3` use or
untrusted pickles. These remain the deploying application's responsibility.

The maintainer-directed decision is documented in
[the dated assessment](MAINTAINER_RISK_ACCEPTANCE_20261119.md)
and [PR #42 discussion](https://github.com/agustin18/fastapi-cache/pull/42#issuecomment-7016369125).
This was an explicit release authorization, not a GitHub vulnerability
dismissal or a promise about consumer applications. The
[release status](../../docs/releases/RELEASE_STATUS_0.3.0.md) records the agent-reported
Dependabot delta check before publication; recheck new, reopened or
materially changed applicable advisories in future releases.
