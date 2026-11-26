# 0.8.0 release status — promotion candidate

**Status:** promotion candidate, not published. No annotated tag, Phase B
final run, TestPyPI artifact or PyPI artifact exists for 0.8.0 yet. The
current published release remains [0.7.2](RELEASE_STATUS_0.7.2.md).

| Item | Current state |
| --- | --- |
| Source version | `0.8.0` |
| Published docs marker | `0.7.2` (unchanged) |
| Current published release | `0.7.2` |
| Final source SHA | Pending freeze after promotion merge |
| Final Phase B | Not run |
| Exact wheel/sdist hashes | Not built for publication |
| TestPyPI | Not run |
| PyPI | Not run |
| Annotated tag | Not created |

The C4 candidate evidence is descriptive only and is not publication
evidence. The #153 0.8.0 re-run did not reproduce the earlier 3.02x p50
outlier; the residual remains accepted and #100 remains open. The final
Phase B must build the exact released source. The release is blocked until
the gates in [RELEASE_CANDIDATE_0.8.0.md](RELEASE_CANDIDATE_0.8.0.md) are
completed and separately authorized.
