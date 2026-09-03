# Operations

Run `make bootstrap`, `make build`, `make test`; use `make preview` for a local HTTPS-independent repository preview. `versions.json` is the single version source: staging turns `X.Y.Z` and revision `N` into Kodi-sortable `X.Y.Z.N`.

After Pages is enabled for this private source repository, install `dist/repository.drakefrog.kodi-emby/1.0.0.1/repository.drakefrog.kodi-emby-1.0.0.1.zip` in Kodi. In each add-on's **Versions** page select **Drakefrog Kodi Emby** to change origin. Upgrade normally; select the preceding listed version to roll back. To stop releases, disable the Pages environment or the release workflow—upstream checks only open review PRs and never deploy.

Review `UPSTREAM_SYNC_REPORT.md` in an automation PR, import vendor changes deliberately, update `upstreams.json`, test, then merge. Do not run upstream workflows as release authority. GitHub Pages must be configured to use **GitHub Actions**; if private-repository Pages is not anonymously reachable on the account plan, keep the source repository private and do not change visibility.
