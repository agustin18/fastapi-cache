# 0.6.0 privacy risk disposition — review draft

**NOT a release approval.** 0.5.0 remains published. This document
records proposed scope and required evidence for #53/#92. Review the
exact corrective PR and then the final promotion SHA and distributions.
Do not infer an accepted final risk decision from this draft.

## Package-controlled gates

| ID | Ownership / impact | Proposed action and verification | Disposition |
|---|---|---|---|
| P1 | Package; credential-header classification, confidentiality | Inspect every Authorization/Cookie occurrence; retain default bypass before backend reads/writes. Test synthetic duplicate headers, including one empty and one nonempty. Existing normal/empty-header tests remain. | Fix staged; exact-head and independent review pending |
| P2 | Package; HTTP intermediary policy, confidentiality | For cached HTTP results on authentication-opt-in routes, generate private, no-store on MISS/HIT/304, including anonymous requests to those routes and returned Response objects. Server-side storage remains governed by the explicit identity-aware builder. | Fix staged; exact-head and independent review pending |
| P3 | Package; explicit Request with default builder and explicit header variations | Preserve read/write bypass, versioned hashed Vary keys, all declared field values and no storage of uncovered Vary/private/no-store on evaluated responses. Regression tests and Redis fixtures. | Verify final artifact; no blanket safety claim |
| P4 | Package; legacy key/namespace migration | Preserve ordinary keys; ensure protected requests do not access previous unsafe entries. Verify selective cleanup, unrelated entries and ordinary-data rollback. | Final artifact proof required |

These changes do not authenticate a request. Reject ambiguous credentials
in the application's authentication layer. HTTP policy on responses for
which the decorator bypasses caching is the application's responsibility.
Changing generated headers cannot purge an intermediary's existing cached
responses; invalidate those caches when migrating affected routes.

## Residual requirements for callers

| ID | Ownership / impact | Required consumer action | Proposed disposition |
|---|---|---|---|
| A1 | Application; hidden context, custom authentication and role/tenant state, confidentiality | Authenticate/authorize before cache lookup. Use validated identity, role, tenant and every representation dimension in a reviewed key, or do not decorate the endpoint. The synthetic hidden-context test characterizes the unsafe configuration and explicit no-cache alternative. | Accept only with documented action and independent review |
| A2 | Application/infrastructure; forwarded identity, Host and proxy trust | Strip untrusted forwarding headers; trust only configured intermediaries; validate host, identity and tenant. Never infer authorization from Vary. | Same |
| A3 | Shared; attacker-controlled cardinality, availability | Normalize/limit header values, request size and rates; use bounded TTLs, memory quotas/eviction and optional local entry cap. Hashing does not authenticate or bound entry count. | Same |
| A4 | Shared; stale/legacy private Redis or intermediary entries, confidentiality | Rotate affected prefixes or perform selective purge before serving; invalidate intermediary caches; do not restore unsafe historical caching on rollback. Never flush unrelated data. | Same; block if protected path reads unsafe data |
| A5 | Package design/application deployment; process-global configuration, isolation | One reviewed configuration per process. Separate processes/backends/prefixes when isolation is required; do not reset or force-reconfigure a live process shared by unrelated apps. App-scoped redesign is future #99. | Same; no claim of per-app isolation |
| A6 | Application/backend trust; deserialization | Do not use PickleCoder with attacker-controlled/untrusted cache bytes, credentials or backend access. | Same |

A private/no-store result or Vary discovered only after executing an
endpoint is not a retroactive invalidation of a previously cached shared
entry; cache hits skip endpoint execution. Dynamic privacy policies must
be evaluated before lookup or the application must bypass caching.
Neither the library nor this risk record guarantees that all hidden
response inputs are detectable.

## Evidence and decision gates

- Source-level regression suites: tests/test_auth_privacy.py,
  tests/test_vary_headers.py, migration Phase B and exact installed security.
- Candidate CI and synthetic fixtures are not third-party adoption.
- The final record must include exact source SHA, both artifact SHA-256
  values, successful run IDs, new/reopened advisory disposition, reviewer
  decision and independent review of the scoped residuals. Historical
  0.5.0 risk acceptance is not consent for 0.6.0.
- Any demonstrable unmitigated package-controlled private replay is
  NO-GO. Fix it instead of labeling it application-owned.
- Reconsider upon new auth/cache behavior, configuration redesign,
  reproduced cross-tenant issue or relevant vulnerability.

**Current decision: pending independent counteraudit and final-artifact
acceptance.** No tag or publication is authorized by this document.
