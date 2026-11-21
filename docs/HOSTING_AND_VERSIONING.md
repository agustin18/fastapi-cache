# Hosting and versioning the documentation

The published package remains [fastapi-cache-stable 0.5.0](https://pypi.org/project/fastapi-cache-stable/0.5.0/). **This document describes the proposed deployment**; a PR merge alone does not make a documentation URL public.

## Why GitHub Pages?

[fastapi-stream-lease](https://github.com/agustin18/fastapi-stream-lease) already uses [GitHub Pages](https://agustin18.github.io/fastapi-stream-lease/) with an automated documentation build, the same repository-owner account and a familiar Material-style interface. Our existing Zensical site already provides mobile navigation, search, light/dark modes, code-copy controls and checked internal links. **Do not replace Zensical just to change hosting.**

GitHub Pages can serve our Zensical-built static documentation without a separate documentation hosting service or account. Selection is based on our operational requirements, not a comparison with another project's hosting.

**Proposed canonical URL (not confirmed live):** https://agustin18.github.io/fastapi-cache/

## Deployment steps (maintainer approval required)

1. Review [#48](https://github.com/agustin18/fastapi-cache/issues/48) and the docs deployment PR. The workflow `.github/workflows/docs-pages.yml` has **only** a `workflow_dispatch` trigger; it does not deploy on a merge or other repository push.
2. In the GitHub repository settings, enable **Pages → Build and deployment → Source: GitHub Actions**. In **Settings → Environments → github-pages**, restrict deployment branches to **only `stable`** (selected branches), and optionally require reviewer approval. **The environment branch restriction is a security requirement**, not merely an optional approval: a maintainer with write access can dispatch a workflow from another branch, including a workflow that changes its own `if` guard.
3. Trigger the workflow explicitly on the reviewed `stable` branch. Both jobs refuse to run unless `github.ref == 'refs/heads/stable'`. The **read-only** build job installs pinned Zensical, generates static HTML, checks **all local links/anchors**, verifies the install/migration/reference entry points, and uploads the Pages artifact. Only the separate deploy job can request `pages: write` and `id-token: write`; it runs after the build and any required environment approval.
4. Inspect the GitHub Actions published deployment URL and open the actual website. Do **not** assume the expected URL is reachable: Pages' unique-domain setting can affect the final address.
5. Independently check the home page, `getting-started/`, `migration/`, `reference/api/`, `reference/alternatives/`, site search, mobile dark mode, and links to the real 0.5.0 PyPI artifact and GitHub release. Verify navigation from a phone-sized viewport; confirm the information in every page matches the released artifact.
6. **Only after successful publication**, add the verified website URL to the root README, PyPI metadata on a future release (do not republish an immutable old version), social posts, and launch tracker [#88](https://github.com/agustin18/fastapi-cache/issues/88). Keep issue #48 open until verification is recorded.

## Historical versions

The current root documentation documents **published 0.5.0 only**. Don't edit it to advertise future APIs before 0.6.0 actually ships. A site update on `stable` is not evidence that a new PyPI version was released.

At 0.6.0, **do not overwrite the historical 0.5.0 docs silently**. Evaluate a reproducible snapshot built from Git tag `v0.5.0` and hosted at a separate `/v0.5.0/` path, and keep an unambiguous current-version alias. Validate all relative links inside both snapshots and the navigation between versions before adding a selector.

Zensical currently supports a **transitional fork of `mike`** for versioned MkDocs documentation. This is not yet equivalent to native versioning, and the fork must be evaluated, pinned to a reviewed source revision and tested before adding it to a deployment pipeline. Alternative: explicit, immutable per-version static builds from tags and a small top-level versions page. Decide the final strategy independently under #48.

## Repository and package boundaries

- Static docs tooling and GitHub Pages tokens are **not runtime dependencies**.
- Workflow permissions default to none. The build job has `contents: read` only, checkout persists no credentials, and only the deploy job obtains `pages: write` and `id-token: write`. Protect the `github-pages` environment by limiting deployments to branch `stable`; the codebase and PyPI release jobs stay separate.
- Do not automatically deploy from feature PRs or unsafe forks. Existing PR workflows only upload short-lived preview artifacts.
- Documentation must never promise universal tenant isolation, Redis Cluster namespace clearing, automatic private-response migration or Python 3.14 support in 0.5.0.

## Sources

- [Zensical publication guide](https://zensical.org/docs/publish-your-site/)
- [Zensical versioning with mike](https://zensical.org/docs/compatibility/mkdocs/mike/)
- [fastapi-stream-lease Pages workflow](https://github.com/agustin18/fastapi-stream-lease/blob/main/.github/workflows/docs.yml)
- [FastAPI-CacheX hosted documentation](https://fastapi-cachex.readthedocs.io/en/stable/)
