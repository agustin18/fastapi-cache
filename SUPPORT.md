# Support policy

`fastapi-cache-stable` is a community-maintained, drop-in stable fork of
fastapi-cache2.

## Supported lines

- `0.4.x`: `0.4.0` published **2026-11-20**; `0.4.1` patch prepared for the same line. Best-effort security
  and critical correctness maintenance targets **2027-11-20**
  (12 months), subject to maintainer capacity. This is a target, not
  a contractual guarantee, for server-side CPython 3.11–3.13.
- `0.3.x`: `0.3.0` and `0.3.1` were published **2026-11-19**; this remains
  the migration line. Its best-effort security/critical maintenance target
  is **2027-11-19**, subject to capacity.
- Compatibility and security matrices are verified on server-side CPython.
  Pyodide, browser and Node runtimes are not tested or covered; this does not
  claim functional incompatibility. Applications using urllib3 in those
  runtimes must assess redirects themselves.
- Check [PyPI](https://pypi.org/project/fastapi-cache-stable/) and
  [CHANGELOG.md](CHANGELOG.md) for current versions. Stable `0.4.x` installs
  on Python `>=3.8,<3.14`. Python 3.8–3.10 have a tested legacy
  functional-compatibility lane, but receive no security-support commitment
  for EOL runtimes or dependency versions. A critical advisory applicable to
  package-controlled behavior must be mitigated before release. If it applies
  only to a specific application-enabled feature or optional backend, the
  trigger and residual risk must be documented and explicitly accepted; EOL
  status alone is not a disposition.
- In released `0.4.x`, the experimental DynamoDB extra requires Python
  `>=3.10`; Python 3.8/3.9 legacy compatibility is limited to Redis/InMemory
  and the documented core APIs.
- Redis client support is Python-conditional: 4.x through 6.1.x on Python
  3.8, through 7.0.x on 3.9 and through 8.1.x on 3.10–3.13. Redis standalone
  is verified; TLS/Sentinel/Cluster/failover are not certified.
- Python 3.14 remains outside the `0.4.x` metadata range until the full
  functional matrix passes.
- `1.x` (planned): if and when `1.0.0` is released with a co-maintainer in
  place, security and critical correctness fixes for 24 months after that
  release. This is a conditional plan, not an active commitment.
- Feature work is best effort.
- The support window is reviewed annually and may be revised with a public
  notice.

## Legacy compatibility is not security maintenance

Python 3.8–3.10 support is provided only to ease upgrades of existing
`fastapi-cache2` users. Those Python versions are EOL and some supported
dependency resolutions retain security advisories. The fork may not
call the affected APIs, but consumer applications may. **Do not rely
on this library to repair Starlette, AnyIO or other application
dependencies automatically.** Prefer CPython 3.11–3.13 with current
compatible packages for production.

See [the version/security matrix](COMPATIBILITY.md),
[our public security policy](SECURITY.md), and
[the dated advisory assessment](audit/security/MAINTAINER_RISK_ACCEPTANCE_20261119.md).
A scoped risk decision does not dismiss a GitHub advisory and does not
establish security support for an EOL Python runtime.

## Handover

- A co-maintainer is required before `1.0.0`. If none is available, `1.0.0` will not be
  released and the 24-month window does not start.
- If the maintainer cannot continue, the project will be handed to a co-maintainer or moved
  to maintenance mode with a public notice.
- The code is Apache-2.0 and can be forked.

## Security

See `SECURITY.md`.
