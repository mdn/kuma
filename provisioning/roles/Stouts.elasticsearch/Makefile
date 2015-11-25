.PHONY: release major minor patch

VERSION?=minor
release:
	@bumpversion $(VERSION)
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push --all
	@git push --tags
	@git checkout develop

major:
	make release VERSION=major

minor:
	make release VERSION=minor

patch:
	make release VERSION=patch
