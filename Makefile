# Use username as signal that we're in the vagrant box
ifeq (vagrant, ${USER})
IN_VAGRANT := 1
else
IN_VAGRANT := 0
endif

# Note: these targets should be run from the kuma vm
django-tests: in_vagrant
	python manage.py test

performance-tests: in_vagrant
	locust -f tests/performance/smoke.py --host=https://developer.allizom.org

install:
	python scripts/peep.py install -r requirements/default.txt

# Note: this target should be run from the host machine with selenium running
browser-tests: on_host
	pushd tests/ui ; ./node_modules/.bin/intern-runner config=intern-local d=developer.allizom.org b=firefox; popd

clean:
	find kuma -name '*.pyc' -exec rm {} \;

# On host: run coverage and display HTML
# On VM: run coverage
coverage:
	echo ${USER}
	if [ ${IN_VAGRANT} -eq 0 ]; then \
		vagrant ssh --command "\
		coverage erase; \
		coverage run ./manage.py test; \
		coverage report; \
		coverage html"; \
		python -c "import webbrowser, os.path; name='file://' + os.path.abspath('htmlcov/index.html'); webbrowser.open(name)"; \
	else \
		coverage erase; \
		coverage run ./manage.py test; \
		coverage report; \
		coverage html; \
	fi

in_vagrant:
	@if [ ${IN_VAGRANT} -eq 0 ]; then echo "*** Run in vagrant ***"; exit 1; fi

on_host:
	@if [ ${IN_VAGRANT} -eq 1 ]; then echo "*** Run on host ***"; exit 1; fi

locale:
	@mkdir -p locale/$(LOCALE)/LC_MESSAGES && \
		for pot in locale/templates/LC_MESSAGES/* ; do \
			msginit --no-translator -l $(LOCALE) -i $$pot -o locale/$(LOCALE)/LC_MESSAGES/`basename -s .pot $$pot`.po ; \
		done

# Those tasks don't have file targets
.PHONY: django-tests performance-tests browser-tests clean in_vagrant on_host coverage locale install
