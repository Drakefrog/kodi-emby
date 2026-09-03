.PHONY: bootstrap build test preview clean sync-emby-next-gen sync-embycon sync-arctic-fuse-3
bootstrap:
	python3 tools/validate.py --sources-only
build:
	python3 tools/build_repo.py
test:
	python3 tools/validate.py
	python3 -m unittest discover -s tests -v
preview: build test
	python3 -m http.server --directory dist 8000
clean:
	rm -rf build dist
sync-emby-next-gen:
	python3 tools/sync_upstream.py emby-next-gen
sync-embycon:
	python3 tools/sync_upstream.py embycon
sync-arctic-fuse-3:
	python3 tools/sync_upstream.py arctic-fuse-3
