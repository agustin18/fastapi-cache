# K1 key filtering — proposed audit revision

Refs #49/#53. Not published; review the delta before merge. The
[0.9 RFC](https://github.com/agustin18/fastapi-cache/pull/158) is narrowed
in response to the independent review of #159.

- Only explicitly declared `Depends(provider)` or
  `Annotated[T, Depends(provider)]` with one metadata marker and no conflicting
  default are eligible. The provider must be explicit, introspectable and
  have zero signature parameters. Reject direct inputs (including implicit
  query parameters and Body/Query/Path/Header/Cookie), Security, security
  provider objects, nested/request-parameterized providers, protected names,
  missing and duplicate names. This deliberately excludes some otherwise
  valid application service providers.
- Bypass if an excluded argument was not supplied or is a scalar/None,
  if the HTTP host is missing/empty/ambiguous, or when application dependency
  overrides are active. Do not reuse previously stored filtered entries in
  these cases. Preserve explicit Request/Response, auth, custom builder and
  Vary/app-scope boundaries. Legacy path remains identical with no opt-in.
- Dependency syntax and provider arity cannot prove a dependency is safe:
  ambient ContextVars, closures, service state and identity-bearing objects
  remain application-controlled. Excluded objects MUST NOT influence the
  response, authorization, identity, tenant, locale or permissions. Do not
  use this option for user/tenant credentials or request-derived data, even
  when wrapped in a zero-argument dependency. #53 stays open.
- Direct calls are restricted to the same explicit declaration and must
  supply the excluded service argument. No changes to endpoint arguments.
- The versioned scalar key format is unchanged from the initial K1 draft.
  No 0.8.0 release artifacts, public API docs or dependency bounds are changed.

Tests cover auditor reproductions, FastAPI dependency declarations, security
providers, request inputs, explicit Request, Host, override bypass, actual
direct HIT, nonmutation and cross-process hash-seed stability. No claims of
universal tenant safety or release readiness.
