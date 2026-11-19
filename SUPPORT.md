# Support policy

`fastapi-cache-stable` is a community-maintained, drop-in stable fork of
fastapi-cache2.

## Supported lines

- `0.3.x`: security and critical correctness fixes for 12 months after the first stable
  `0.3.0` release, on a best-effort basis and subject to maintainer capacity. The window is
  a target, not a guarantee. Security support applies to server-side CPython 3.11–3.13.
- Compatibility and security matrices are verified on server-side CPython. Pyodide, browser and
  Node runtimes are not tested or covered; this does not claim functional incompatibility.
  Applications using urllib3 in those runtimes must assess redirects themselves.
- The 12-month maintenance target begins at the first stable release; prereleases
  do not start it. Check [PyPI](https://pypi.org/project/fastapi-cache-stable/)
  and [CHANGELOG.md](CHANGELOG.md) for current publication status.
- Stable `0.3.0` installs on Python `>=3.8,<3.14`. Python 3.8–3.10 have a tested legacy
  functional-compatibility lane, but receive no security-support commitment for EOL runtimes
  or dependency versions. A critical advisory applicable to package-controlled behavior must
  be mitigated before release. If it applies only to a specific application-enabled feature or
  optional backend, the trigger and residual risk must be documented and explicitly accepted;
  EOL status alone is not a disposition.
- For the target stable `0.3.0`, DynamoDB is an experimental optional backend available only on
  Python `>=3.10`; Python 3.8/3.9 legacy compatibility is limited to Redis/InMemory and the
  documented core APIs.
- Python 3.14 remains outside the `0.3.x` metadata range until the full functional matrix passes.
- `1.x` (planned): if and when `1.0.0` is released with a co-maintainer in place, security
  and critical correctness fixes for 24 months after that release. This is a conditional
  plan, not an active commitment.
- Feature work is best effort.
- The support window is reviewed annually and may be revised with a public notice.

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
