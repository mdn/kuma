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

clean:
	find kuma -name '*.pyc' -exec rm {} \;


in_vagrant:
	@if [ ${IN_VAGRANT} -eq 0 ]; then echo "*** Run in vagrant ***"; exit 1; fi

on_host:
	@if [ ${IN_VAGRANT} -eq 1 ]; then echo "*** Run on host ***"; exit 1; fi

# Those tasks don't have file targets
.PHONY: django-tests performance-tests browser-tests clean in_vagrant on_host
