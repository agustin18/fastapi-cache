# Published releases and evidence

Release tags are immutable reference points. The repository's `stable` branch may contain later documentation or unreleased work. Bounded InMemory is published in **0.7.2**; it is not part of a 0.5.0 artifact.

| Release | Status | Highlights |
|---|---|---|
| [0.7.2](https://pypi.org/project/fastapi-cache-stable/0.7.2/) | Published 2026-11-25 | Standard CPython 3.14 compatibility; no runtime or API changes |
| [0.7.1](https://pypi.org/project/fastapi-cache-stable/0.7.1/) | Published 2026-11-24 | Metadata-only correction over 0.7.0; rebuilds the PyPI long description |
| [0.7.0](https://pypi.org/project/fastapi-cache-stable/0.7.0/) | Published 2026-11-24 | Exact TTL boundary, decode-before-304, Redis tuple contract and release-quality evidence |
| [0.6.0](https://pypi.org/project/fastapi-cache-stable/0.6.0/) | Published 2026-11-21 | Bounded InMemory, targeted privacy fixes and exact release-bundle checks |
| [0.5.0](https://pypi.org/project/fastapi-cache-stable/0.5.0/) | Published 2026-11-21 | Opt-in `vary_headers`, strict artifact migration and security gates |
| [0.4.1](https://pypi.org/project/fastapi-cache-stable/0.4.1/) | Published 2026-11-20 | Generated/factory-route cache key isolation |
| [0.4.0](https://pypi.org/project/fastapi-cache-stable/0.4.0/) | Published 2026-11-20 | Redis-py 4–8 conditional compatibility |
| [0.3.1](https://pypi.org/project/fastapi-cache-stable/0.3.1/) | Historical | Explicit-Request/default-builder cache bypass |
| [0.3.0](https://pypi.org/project/fastapi-cache-stable/0.3.0/) | Historical | Initial stable migration line |

## 0.7.2 provenance

- Annotated tag `v0.7.2`, final Phase B, TestPyPI/PyPI runs and SHA-256 values are recorded in the [0.7.2 release status](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_STATUS_0.7.2.md).

## 0.7.1 provenance

- Annotated tag `v0.7.1` -> `c6f46da82595c808866c9b944a5f931e07ceeb4b`
- Phase B `45302769038` (20 of 20); TestPyPI `45303059177`; PyPI `45303318025`
- Wheel `54d64e3f24110f434d2a1b765006e528302d5550ad0b4ce20b8eb706a49e9aa3`
- Sdist `c3fa245c9212ec292c43523e1402baad75da4571bbac0832380020c2205426d5`
- [0.7.1 release status](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_STATUS_0.7.1.md)

## 0.7.0 provenance

- Annotated tag `v0.7.0` -> `df884644f11eb0e36ae5d74721009fc8e4470c4b`
- Phase B `45252714837` (20 of 20); TestPyPI `45296557093`; PyPI `45296858482`
- Wheel `4c6338a27ac663a26ae23cfca975005736282764609aacba4e7e7febcde1a8a3`
- Sdist `ebefd6a0010a55fd73603e2fd882562951358d98954ce0de1a49114aad1a38b1`

## 0.6.0 provenance

| Artifact | SHA-256 |
|---|---|
| Wheel | `60be61f68908bb8621a53c902baed2b61c9e894cffa95d8df0e9dd71c5bc4b5e` |
| Sdist | `c0f8f8b872d337b432afd1340dbe8b9b1800933dfed9c3f3c14ad232153408f2` |

The annotated `v0.6.0` tag points to commit `6b6924a61bbcc0ba602da514accb4c563806742f`. Final release evidence: Phase B run `44944620217` (20 of 20), TestPyPI run `44944911074`, PyPI run `44945090377`.

## 0.5.0 provenance

| Artifact | SHA-256 |
|---|---|
| Wheel | `7f30d074e222aaf4471d13105e1282b97d2968549bc4b727b941837272b10449` |
| Sdist | `e5dfe2fb5a16cb790e98bfb5e57377d835adc55579b0fdf1cb1d0afbf610ba0b` |

The annotated `v0.5.0` tag points to commit `40c86d551b760315f3c6e99f383d6868c6294870`. Final release CI included 13/13 exact wheel/sdist migration/rollback jobs, 7/7 installed security profiles and a fresh authenticated Dependabot delta with 21 unchanged historical alerts. These findings are **bounded acceptance**, not claims that all vulnerabilities or consumer configurations are risk-free.

- [Release status, hashes and workflow links](https://github.com/agustin18/fastapi-cache/blob/stable/docs/releases/RELEASE_STATUS_0.5.0.md)
- [Maintainer's signed scope decision](https://github.com/agustin18/fastapi-cache/issues/66#issuecomment-7055377740)
- [GitHub Release](https://github.com/agustin18/fastapi-cache/releases/tag/v0.5.0)
- [CHANGELOG](https://github.com/agustin18/fastapi-cache/blob/stable/CHANGELOG.md)

The release is **not** a certification of arbitrary authenticated applications, Redis Cluster, TLS/Sentinel or private-response rollback.
