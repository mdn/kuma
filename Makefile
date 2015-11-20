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

# Note: this target should be run from the host machine with selenium running
browser-tests: on_host
	pushd tests/ui ; ./node_modules/.bin/intern-runner config=intern-local d=developer.allizom.org b=firefox; popd

travis-tests:
	python manage.py compilejsi18n
	coverage run manage.py test --noinput -v2
	coverage report

isort:
	isort --recursive --atomic --apply --verbose -sp ./setup.cfg kuma/

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

# Those tasks don't have file targets
.PHONY: django-tests performance-tests browser-tests clean in_vagrant on_host travis-tests coverage isort
