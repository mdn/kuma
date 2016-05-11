target = kuma
requirements = -r requirements/local.txt
# set Django settings module if not already set as env var
export DJANGO_SETTINGS_MODULE ?= kuma.settings.testing

# Note: these targets should be run from the kuma vm
test:
	py.test $(target)

coveragetest: clean
	py.test --cov=$(target) $(target)

coveragetesthtml: coveragetest
	coverage html

locust:
	locust -f tests/performance/smoke.py --host=https://developer.allizom.org

compilecss:
	@ echo "## Compiling Stylus files to CSS ##"
	@ ./scripts/compile-stylesheets

compilejsi18n:
	@ echo "## Generating JavaScript translation catalogs ##"
	@ python manage.py compilejsi18n

collectstatic:
	@ echo "## Collecting and building static files ##"
	@ mkdir -p build/assets
	@ python manage.py collectstatic --noinput

install:
	@ echo "## Installing $(requirements) ##"
	@ pip install $(requirements)

# Note: this target should be run from the host machine with selenium running
intern:
	pushd tests/ui ; ./node_modules/.bin/intern-runner config=intern-local d=developer.allizom.org b=firefox; popd

clean:
	rm -rf .coverage build/
	find kuma -name '*.pyc' -exec rm {} \;
	mkdir -p build/assets
	mkdir -p build/locale

locale:
	@mkdir -p locale/$(LOCALE)/LC_MESSAGES && \
		for pot in locale/templates/LC_MESSAGES/* ; do \
			msginit --no-translator -l $(LOCALE) -i $$pot -o locale/$(LOCALE)/LC_MESSAGES/`basename -s .pot $$pot`.po ; \
		done

localetest:
	dennis-cmd lint --errorsonly locale/

localeextract:
	python manage.py extract
	python manage.py merge

localecompile:
	cd locale; ./compile-mo.sh . ; cd --

localerefresh: localeextract localetest localecompile compilejsi18n collectstatic
	@echo
	@echo Commit the new files with:
	@echo git add --all locale\; git commit -m \"MDN string update $(shell date +%Y-%m-%d)\"

# Those tasks don't have file targets
.PHONY: test coveragetest intern locust clean locale install compilecss compilejsi18n collectstatic localetest localeextract localecompile localerefresh
