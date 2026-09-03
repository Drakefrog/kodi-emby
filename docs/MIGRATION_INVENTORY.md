# Migration inventory

| Work item | Origin | Files in canonical source | Contract/test |
|---|---|---|---|
| dynamic pagination / sorting / Fuse query routing / season-series details | Next-Gen `737a55d..5d2aa07` | `sources/emby-next-gen/{database,helper,hooks,emby}` | patch queue applies; ZIP identity contract |
| Infuse identity and authenticated image proxy | 4 uncommitted live files | `emby/api.py`, `emby/http.py`, `helper/utils.py`, `hooks/webservice.py` | patch queue + ZIP exclusions |
| video helper | installed addon snapshot | `sources/plugin.video.emby-next-gen` | repository contract |
| Fuse search / widgets / recommendations / people detail | EmbyCon `c1e3a2e..d445bca` | `sources/embycon/plugin.video.embycon/resources/lib/{detail_routes.py,detail_utils.py,functions.py}` | `OPEN_DETAIL` cross-plugin test |
| nested Info handoff | EmbyCon stash `6a16be8` | same three EmbyCon files | `OPEN_DETAIL` contract |
| person dialog + Home bridge | Fuse `3d5ba82`, `c89780b` | `sources/arctic-fuse-3/1080i` | Fuse/EmbyCon plugin URL contract |
| live Fuse widget changes | working tree content audit | `Dialog_DialogCustom.xml`, `Dialog_DialogPlot.xml`, `Includes_Actions.xml`, `Includes_DialogInfo.xml`, `Includes_Expressions.xml`, `Includes_Info.xml`, `Includes_Lists.xml`, `Includes_Paths.xml`, `Includes_Search.xml`, `script-skinviewtypes-includes.xml`, `shortcuts/generator/data/setup/search_path.xml`, `shortcuts/skinvariables-shortcut-searchwidgets.json` | source-to-live checksum audit + patch queue |

`language/resource.language.ar_sa/strings.po` was copied because it has a content diff, but is not attributed to the Emby integration. Deleted `.git*`, `.github`, MAL image files, and `.git.broken-backup` were intentionally not migrated: they are installation/upstream metadata removals or generated debris, not runtime changes. Upstream workflows, tests, Git metadata, bytecode and backups are excluded from ZIPs.
