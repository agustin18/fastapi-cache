# Roadmap: what is next?

**0.6.0 is published.** It includes optional per-instance bounded InMemory,
conservative credential-header handling and the exact-artifact release
pipeline. See the [published evidence](reference/releases.md) and
[compatibility](reference/compatibility.md). Features listed below are
**planned**, not available with a 0.6.0 install.

## Release priorities (proposals, not deadlines)

| Target | Work | Quality boundary |
|---|---|---|
| 0.7.0 | [#100 installed benchmarks](https://github.com/agustin18/fastapi-cache/issues/100), [#96 local single-flight](https://github.com/agustin18/fastapi-cache/issues/96), [#50 opt-in events](https://github.com/agustin18/fastapi-cache/issues/50) | Complete release-pipeline refactor and designs [#99](https://github.com/agustin18/fastapi-cache/issues/99)/[#103](https://github.com/agustin18/fastapi-cache/issues/103) **first**; bounded cancellation and no private data in events |
| 0.7.x | [#51 Python 3.14](https://github.com/agustin18/fastapi-cache/issues/51) when compatible, [#55 FIPS](https://github.com/agustin18/fastapi-cache/issues/55), bounded backend corrections | Preserve documented ordinary cache keys and old Python functional-compatibility lanes |
| 0.8.0 | [#99 app-scoped configuration](https://github.com/agustin18/fastapi-cache/issues/99), [#97 tags](https://github.com/agustin18/fastapi-cache/issues/97), [#103 app caching](https://github.com/agustin18/fastapi-cache/issues/103), [#49 safe parameter filtering](https://github.com/agustin18/fastapi-cache/issues/49) | Opt-in compatibility, independent lifespans, key/tenant correctness, invalidation races |
| 0.9.0 | [#98 bounded stale](https://github.com/agustin18/fastapi-cache/issues/98), advanced Redis resilience/HA and distributed coordination research [#102](https://github.com/agustin18/fastapi-cache/issues/102) | Never assume Cluster namespace clear, unlimited stale retention or automatic tenant isolation |
| 1.0 | Stable public API and reviewable support policy | Co-maintainer/support commitments are separate decisions; no unsupported long-term guarantees |

Basic Redis timeout, disconnect and cancellation qualification under #102 is
a candidate for 0.7.0, not a claim of TLS, Sentinel or Cluster support.

## How we decide what ships

Reproducible installed wheel/sdist tests, supported-runtime compatibility,
privacy and failure/cancellation tests, performance baselines, truthful
documentation and explicit maintainer approval are release gates. There is
**no external adoption quota** or required hosted site for publication.

[Project roadmap](https://github.com/agustin18/fastapi-cache/blob/stable/ROADMAP.md)
contains historical details and proposed work.
[#48](https://github.com/agustin18/fastapi-cache/issues/48) tracks optional
GitHub Pages hosting and immutable historical documentation; the generated site
is not assumed live until a verified deployment.
