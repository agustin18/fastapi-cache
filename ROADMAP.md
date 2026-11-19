# Roadmap — fastapi-cache-stable

These are **proposals**, not dates, guarantees or features included in 0.3.0.
The top priority is a trustworthy first stable release for existing
`fastapi-cache2` users: tested migration, explicit changes, supported
dependency profiles and conservative security fixes. Avoid adding features
to the already-reviewed 0.3.0 runtime without a verified regression and a
fresh RC.

| Priority / candidate line | Proposed improvement | Why it matters | Release strategy |
|---|---|---|---|
| P0 / 0.3.0 | Final security signoff, fresh Dependabot review, final wheel scan and clean-install evidence | Clear documented first stable contract | No new runtime behavior |
| P1 / 0.3.1 | Fast regression fixes, diagnostic events/logging, clearer migration examples | Build trust with first users | Backward-compatible patches |
| **P1 / 0.4.x** | **Redis-py 5/6 compatibility matrix** | Upstream 0.2.2 uses 5.x, fork 0.3.x tests 4.x; currently a material migration gap | Opt-in/version-range expansion only after Redis tests |
| **P1 / 0.4.x** | Safe configurable key-builder parameter exclusion | Avoid volatile injected session objects causing permanent cache MISS | Opt-in, never exclude identity/tenant dimensions automatically |
| P1 / 0.4.x | Observability for MISS/HIT/BYPASS/errors and benchmarks | Real performance comparisons and production diagnosis | No breaking defaults |
| P2 / 0.5.x | Stampede prevention with single-flight/local and Redis locking | Avoid duplicate expensive recomputations under concurrency | Explicitly opt in; TTL/lock expiry/failure tests |
| P2 / 0.5.x | Tag-based/key-pattern invalidation and namespace lifecycle | Common upstream feature requests | Preserve current namespace boundaries |
| P2 / future | App-scoped configuration instead of process-global singleton | Multi-app/test isolation | Major-version design if API breaks |
| P2 / future | Better optional backend parity (Memcached TTL / DynamoDB clear), Redis Cluster constraints | Reduce experimental functionality | Ship each with real integration tests |
| P2 / future | Python 3.14 full matrix, dependency simplification (Pendulum/Uvicorn) | Broader modern adoption and smaller transitive surface | No claim of support until validated |
| Research | Advanced HTTP caching (Vary/stale-while-revalidate), POST opt-in, alternative backends | Compete beyond migration-oriented use cases | Security/HTTP correctness review required |

## Not part of 0.3.0

- Zero-vulnerability guarantees across all possible consuming applications.
- Security maintenance for Python 3.8–3.10 or Pyodide/browser runtimes.
- Redis-py 5/6, tag invalidation, stampede protection or redis-cluster
  namespace clearing.
- A public promise of better performance than fastapi-cache2, cashews or
  FastAPI-CacheX without reproducible comparative measurements.

## How priorities change

Prefer reproduced user bugs, installs that fail on documented versions,
dependency CVEs directly affecting package-controlled paths and migration
feedback over speculative new features. When upgrading dependencies, test
a real consumer and guard the default cache-key format and authenticated
request privacy contract.

Tracking and discussion belongs in GitHub issues/PRs. An accepted proposal
is not part of a release until CI and its published artifact are verified.
