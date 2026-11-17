# Support policy

`fastapi-cache-stable` is a community-maintained, drop-in stable fork of
fastapi-cache2.

## Supported lines

- `0.3.x`: security and critical correctness fixes for 12 months after the first stable
  `0.3.0` release, on a best-effort basis and subject to maintainer capacity. The window is
  a target, not a guarantee. Stable `0.3.0` supports Python `>=3.11,<3.14` only.
- The already-published `0.3.0b1` retains its original metadata for historical migration on
  Python 3.8–3.10; those interpreters are outside the stable security-support scope.
- `1.x` (planned): if and when `1.0.0` is released with a co-maintainer in place, security
  and critical correctness fixes for 24 months after that release. This is a conditional
  plan, not an active commitment.
- Feature work is best effort.
- The support window is reviewed annually and may be revised with a public notice.

## Handover

- A co-maintainer is required before `1.0.0`. If none is available, `1.0.0` will not be
  released and the 24-month window does not start.
- If the maintainer cannot continue, the project will be handed to a co-maintainer or moved
  to maintenance mode with a public notice.
- The code is Apache-2.0 and can be forked.

## Security

See `SECURITY.md`.
