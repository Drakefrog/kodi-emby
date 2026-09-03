.PHONY: bootstrap build test preview clean
bootstrap:
	python3 tools/validate.py --sources-only
build:
	python3 tools/build_repo.py
test:
	python3 tools/validate.py
preview: build test
	python3 -m http.server --directory dist 8000
clean:
	rm -rf build dist
