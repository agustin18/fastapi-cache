# Documentation site development

The authoritative published package remains **fastapi-cache-stable 0.5.0**. The sources in site_docs/ are a searchable companion to MIGRATION.md, SECURITY.md, COMPATIBILITY.md, SUPPORT.md and the release archive.

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

The read-only Documentation site GitHub Actions workflow builds the site and uploads static output as a short-lived artifact. It does not publish GitHub Pages, mutate PyPI or create a deployment. A public website and true multi-version hosting require separate maintainer approval.

Historical releases already remain navigable at [docs/releases](releases/README.md); source on stable is not immutable documentation for older wheels.

## Authoring contract

- Primary guides describe published behavior. Features from unmerged PRs must be visibly labeled proposed.
- Show the distribution name fastapi-cache-stable, the import fastapi_cache and Python legacy/security support boundaries accurately.
- Migration walkthroughs cover uninstalling fastapi-cache2, application lockfiles, tenant safety, targeted namespace cleanup and bounded rollback.
- Snippets declare dependencies and are runnable on the named Python/server profiles.
- Mobile navigation, readable color schemes, accessible links/contrast and reduced-motion preferences are design requirements.
- Compare release dates/hashes against [RELEASE_STATUS_0.5.0.md](releases/RELEASE_STATUS_0.5.0.md), not source version on stable.

The site uses [Zensical](https://zensical.org/) for search, responsive navigation and a modern theme.