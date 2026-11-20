# fastapi-cache-stable 0.4.1 — factory-route cache isolation

> **Status: published 2026-11-20.**
> PyPI: [fastapi-cache-stable==0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/).

## What's fixed

Factory-created FastAPI handlers can share the legacy default key when they
have the same module/name, arguments and namespace, even when they serve
different routes. Published `0.4.0` can therefore replay `/a`'s cached
response from `/b`. `0.4.1` partitions the default cache key for:

- functions with code free variables (`co_freevars`);
- handlers wrapped by decorators that set `__wrapped__`, including
  `functools.wraps` wrappers whose factory values are bound as defaults;
- local functions and lambdas;
- explicitly decorated module-level handlers with `__wrapped__`.

The partition uses stable request method, case-normalized Host, mount root,
request path and the legacy digest. Unwrapped module-level handler keys,
the exported `default_key_builder` and custom builders are unchanged.
Old generated/wrapped entries are intentionally not reused; affected routes
will take an initial MISS and rotate to the new key. Read the migration guide.

## Also included

- The docs-only Towncrier classifier from #67/#71. Markdown/RST-only changes
  no longer require a fictional news fragment; source, packaging, tests,
  workflows, examples and scripts still do.
- A changelog correction for `0.4.0`: the already-shipped `uvicorn` removal
  (#44) and read-only Dependabot delta (#46) are now recorded.

## Verification

- Exact PR head: `0f26788dac3eced92e96b81045920163696deabb`.
- 48 unique GitHub checks green on the PR; the full Python/Redis matrix,
  lint, typecheck, security audits, wheel/sdist and CodeQL passed.
- Dedicated HTTP regression for factory closures, `functools.wraps` and
  default-bound values: `/a → A`, `/b → B`, MISS/MISS/HIT/HIT.
- Seeded old cache entries are not read; ordinary unwrapped module-level
  keys remain identical; `clear(namespace=...)` is covered with InMemory
  and Redis 7.
- Final 0.4.1 wheel/sdist hashes, TestPyPI/PyPI runs and provenance are
  recorded in the [release status](RELEASE_STATUS_0.4.1.md) after publication.

## Limits

Generated-route keys include Host and require edge Host validation
(`TrustedHostMiddleware` or equivalent) to avoid fragmentation/resource
exhaustion; Host is case-normalized only, not port/alias normalized. Hidden
`contextvars`, middleware, tenant identity and other request context remain
the application's responsibility and are tracked in #53. Separate
applications sharing a host/path/backend prefix still need distinct prefixes.
Duplicate module-level names and direct non-ASGI `@cache` calls are not
covered by this patch. Do not treat a cache key as an authorization boundary.

## Install after publication

```sh
python -m pip uninstall -y fastapi-cache2
python -m pip install "fastapi-cache-stable[redis]==0.4.1"
python -m pip check
```

Do not run this before confirming that `0.4.1` exists on PyPI.
