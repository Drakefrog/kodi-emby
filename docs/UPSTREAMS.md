# Upstream provenance and patch queues

`vendor/` contains byte-for-byte Git archives at the recorded **pure upstream** commit. `sources/` is the corresponding customized tree. `patches/<component>/0001-customizations.patch` is regenerated as the diff from vendor to source; it is reviewable with `git apply --check -p3` against a fresh upstream archive. This is the repository's vendor/patch-queue equivalent to subtree history: each base and each local delta are committed and independently verifiable.

| Component | Upstream / branch | pure baseline | source layout / attribution |
|---|---|---|---|
| Emby for Kodi Next-Gen | MediaBrowser/plugin.video.emby, `next-gen-dev-python3` | `ae994cd9c2a240411e4b96f9c26fea51c8d166a4` | `vendor/emby-next-gen`; upstream `LICENSE.txt` retained |
| EmbyCon | faush01/plugin.video.embycon, `master` | `a56033d7e22ecb0d72e432ac5e20cf38d40f4a83` | canonical source retains the addon subtree at `sources/embycon/plugin.video.embycon`; `vendor/embycon/plugin.video.embycon` is the matching upstream subtree. Attribution remains in addon metadata; the upstream revision has no top-level license file. |
| Arctic Fuse 3 | jurialmunkey/skin.arctic.fuse.3, `omega` | `1602291d5b7e3d6e8b5d583c8fbdd110d563fba7` | `vendor/arctic-fuse-3`; upstream `LICENSE.txt` retained |

The installed custom HEADs are evidence only, not upstream commits: Next-Gen `5d2aa07`, EmbyCon `d445bca`, Fuse `c89780b`. They are never used for update detection.
