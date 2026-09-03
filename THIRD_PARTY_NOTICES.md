# Third-party notices

This repository is an integration and distribution workspace. It is **not** a
single upstream project and this notice does not relicense the included work.
Each add-on retains its original add-on id, copyright notices, attribution and
license terms.

| Included component | Upstream | License / notice |
|---|---|---|
| Emby for Kodi Next-Gen | MediaBrowser/plugin.video.emby | Upstream license retained at `sources/emby-next-gen/LICENSE.txt` and `vendor/emby-next-gen/LICENSE.txt`. |
| EmbyCon | faush01/plugin.video.embycon | GPL-2.0-only as declared in its add-on metadata; the corresponding text is at `licenses/EmbyCon-GPL-2.0.txt`. |
| Arctic Fuse 3 | jurialmunkey/skin.arctic.fuse.3 | Upstream license retained at `sources/arctic-fuse-3/LICENSE.txt` and `vendor/arctic-fuse-3/LICENSE.txt`. |
| Next-Gen video helper | MediaBrowser/plugin.video.emby | Distributed with its original metadata and attribution. |

`vendor/` is a verifiable unmodified upstream archive at the commit recorded
in `upstreams.json`; `sources/` contains the locally customized counterpart;
`patches/` records the delta. See `docs/UPSTREAMS.md` for provenance.
