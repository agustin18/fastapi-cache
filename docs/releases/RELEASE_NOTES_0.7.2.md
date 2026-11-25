# 0.7.2 release notes — DRAFT / NOT PUBLISHED

The proposed patch extends standard CPython support through 3.14, following
the passing diagnostic qualification in #142. Latest published: [0.7.1](RELEASE_STATUS_0.7.1.md).

- Proposed package range: `>=3.8,<3.15`; Redis extra retains the existing
  client bounds and extends the modern marker through 3.14.
- Proposed functional scope: Python 3.8–3.14; 3.8–3.10 legacy only.
- Proposed best-effort server-side security target: CPython 3.11–3.14,
  conditional on the exact installed-artifact audits and release approval.
- No new runtime API or change to ordinary keys, ETags or serialization.
- Memcached and DynamoDB remain experimental; free-threaded 3.14t and
  Python 3.15 remain outside the qualified scope.

See [the staging checklist](RELEASE_CANDIDATE_0.7.2.md). Final release
date, provenance, hashes and publication evidence are pending.
