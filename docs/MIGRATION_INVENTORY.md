# Migration inventory

| Component | Included work | Evidence |
|---|---|---|
| Next-Gen service | dynamic pagination, sort/filter, Fuse search, series/season details (8 commits `737a55d..5d2aa07`) | `sources/emby-next-gen`, upstream baseline `ae994cd` |
| Next-Gen service | Infuse identity/header compatibility and authenticated image proxy (4 uncommitted files) | `emby/api.py`, `emby/http.py`, `helper/utils.py`, `hooks/webservice.py` |
| Next-Gen helpers | installed video helper plus audio/image helpers | `sources/plugin.*.emby-next-gen` |
| EmbyCon | Fuse search/details/person integration (`c1e3a2e..d445bca`) | `sources/embycon/resources/lib` |
| EmbyCon stash | nested Info handoff/real detail item route | stash `6a16be8`, applied after branch snapshot |
| Arctic Fuse 3 | person-detail shell and Home bridge (`3d5ba82`, `c89780b`) | committed source snapshot |
| Arctic Fuse 3 | dialog/actions/search widget changes | selected working-tree XML/JSON changes; deleted upstream metadata, MAL assets and `.git.broken-backup` excluded |

Upstream workflow files, tests, Git metadata, bytecode and backups are intentionally excluded from release archives.
