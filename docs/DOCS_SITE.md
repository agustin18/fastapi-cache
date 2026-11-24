# Documentation site development

The authoritative published package remains **fastapi-cache-stable 0.7.1**. The sources in site_docs/ are a searchable companion to MIGRATION.md, SECURITY.md, COMPATIBILITY.md, SUPPORT.md and the release archive.

## Preview locally

Use a separate docs virtual environment on Python 3.11+:

~~~console
python -m venv .venv-docs
. .venv-docs/bin/activate
python -m pip install "zensical==0.1.3"
zensical serve
~~~

Open http://127.0.0.1:8000/. Build the static pages:

~~~console
zensical build
~~~

The generated site/ directory is not committed. The documentation tool is **not a runtime dependency** of the library.

## PR previews

The read-only Documentation site GitHub Actions workflow builds the site and uploads static output as a short-lived artifact. The separate Pages workflow deploys only from `stable`. The live site is <https://agustin18.github.io/fastapi-cache/>; multi-version hosting remains a separate follow-up.

Historical releases already remain navigable at [docs/releases](releases/README.md); source on stable is not immutable documentation for older wheels.

## Authoring contract

- Primary guides describe **published** behavior. Features merged into `stable` but absent from the latest PyPI artifact must be labeled **merged source, not released**, with a distinct next-release section. Features in unmerged PRs stay proposed.
- Show the distribution name fastapi-cache-stable, the import fastapi_cache and Python legacy/security support boundaries accurately.
- Migration walkthroughs cover uninstalling fastapi-cache2, application lockfiles, tenant safety, targeted namespace cleanup and bounded rollback.
- Snippets declare dependencies and are runnable on the named Python/server profiles.
- Mobile navigation, readable color schemes, accessible links/contrast and reduced-motion preferences are design requirements.
- Compare the current published release against [RELEASE_STATUS_0.7.1.md](releases/RELEASE_STATUS_0.7.1.md). Use older provenance records only for historical artifacts; source on `stable` is not publication evidence.

The site uses [Zensical](https://zensical.org/) for search, responsive navigation and a modern theme.

## Public hosting

The workflow `.github/workflows/docs-pages.yml` publishes the same Zensical
site as [fastapi-stream-lease](https://github.com/agustin18/fastapi-stream-lease)
on documentation-relevant pushes to `stable`; it can also be run manually.
The public URL is <https://agustin18.github.io/fastapi-cache/>. The Pages
environment is restricted to `stable`, the build job is read-only, and only
the deploy job receives Pages and OIDC permissions.

Read the exact setup, live URL checks and immutable-version policy in
[HOSTING_AND_VERSIONING.md](HOSTING_AND_VERSIONING.md).
Compare the installed API, unshipped features and alternatives in
[site_docs/reference/](../site_docs/reference/).

Zensical's versioned `mike` integration remains transitional; pin and test it
independently before offering a historical version selector.
