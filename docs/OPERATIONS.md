# Operations

## Build and validate

Run `make bootstrap`, `make build`, and `make test`; use `make preview` for a
local HTTPS-independent repository preview. `versions.json` is the single
version source: staging turns `X.Y.Z` and revision `N` into Kodi-sortable
`X.Y.Z.N`. Kodi archive URLs are exactly
`https://drakefrog.github.io/kodi-emby/<addon-id>/<addon-id>-<version>.zip`.

After Pages is enabled, install
`dist/repository.drakefrog.kodi-emby/repository.drakefrog.kodi-emby-1.0.0.1.zip`
in Kodi. In each add-on's **Versions** page select **Drakefrog Kodi Emby** to
change origin.

## Controlled release from `main`

GitHub Pages must be configured to use **GitHub Actions**, and the
`github-pages` environment should remain restricted to the `main` branch. The
release workflow deploys only when a commit is pushed to `main` whose commit
message starts exactly with `release:`. This keeps the deployment ref on
`main`, which satisfies the environment branch policy, while making release
intent explicit and reviewable.

Use this sequence for every release:

1. Prepare the source/version changes, then run `make build test` locally.
2. Review the complete diff and commit the release state on `main` with a
   message such as `release: publish 1.0.0.2`.
3. Push `main` to GitHub. The push starts the release workflow; verify that the
   workflow checks out `main`, builds `dist`, and completes the Pages
   deployment.
4. Install or upgrade from the published repository in Kodi and record the
   release commit and version in the change log or release notes.

The workflow also keeps `workflow_dispatch` as an emergency/manual fallback.
Select `main`, enter exactly `RELEASE` in its required input, and start the
run. Manual runs from any other ref are rejected by the job condition.
Ordinary commits on `main` do not deploy.
`release-*` tags are retained as historical version and rollback references,
but pushing a tag does not trigger Pages deployment.

## Rollback and stop procedures

Kodi's repository master XML exposes one current version per unique add-on id,
so it cannot offer a reliable previous-version picker. Each build retains the
previous ZIP and lists it in `rollback.json`; manually install that exact
historical URL to roll back. To rebuild a prior controlled release, use its
`release-*` tag as the historical source, restore that state into a new commit
on `main` with a `release:` message, and push `main`; the tag itself remains a
reference and never deploys directly. Do not create, move, or delete tags as
part of this procedure.

For an emergency stop, disable the Pages environment or the release workflow.
The upstream checks only open review PRs and never merge or deploy. Do not run
upstream workflows as release authority.

## Upstream updates

To prepare an upgrade locally, run exactly one of
`make sync-emby-next-gen`, `make sync-embycon`, or
`make sync-arctic-fuse-3`. The command clones upstream to a temporary
directory, archives its new tip, replays the committed patch queue, and first
assembles a complete transaction tree. It then renames each canonical path
while retaining `.sync-backup`; any exception restores already-swapped paths.
Inspect `UPSTREAM_SYNC_REPORT.md`, `git diff`, run `make build test`, and commit
the result on a review branch. If any patch conflicts, the command leaves
sources/vendor untouched, writes a conflict report, and exits non-zero; resolve
by manually applying the reject to a copy, regenerating the patch queue, then
rerunning tests. Merge the reviewed change to `main`; only add the `release:`
prefix when it is intentionally ready for publication.

The video helper provenance is in `helpers.json`. Its upstream does not expose
a reliable version feed, so its upgrade is a deliberate manual review. The
installed audio/image helper directories contain only icon assets and have no
`addon.xml`; they are intentionally **not** published.
