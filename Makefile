VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
BASE_IMAGE_NAME ?= kuma_base
KUMA_IMAGE_NAME ?= kuma
REGISTRY ?= quay.io/
IMAGE_PREFIX ?= mozmar
BASE_IMAGE ?= ${REGISTRY}${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:${VERSION}
BASE_IMAGE_LATEST ?= ${REGISTRY}${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:latest
KUMA_IMAGE ?= ${REGISTRY}${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:${VERSION}
KUMA_IMAGE_LATEST ?= ${REGISTRY}${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:latest

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
	@ mkdir -p build/locale
	@ python manage.py compilejsi18n

collectstatic:
	@ echo "## Collecting and building static files ##"
	@ mkdir -p build/assets
	@ python manage.py collectstatic --noinput

build-static: compilecss compilejsi18n collectstatic

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
	# For generating a new file to let locales name localizable
	python manage.py translate_locales_name
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

pull-base:
	docker pull ${BASE_IMAGE}

pull-kuma:
	docker pull ${KUMA_IMAGE}

pull-base-latest:
	docker pull ${BASE_IMAGE_LATEST}

pull-kuma-latest:
	docker pull ${KUMA_IMAGE_LATEST}

pull-latest: pull-base-latest pull-kuma-latest

build-base:
	docker build -f Dockerfile-base -t ${BASE_IMAGE} .

build-kuma:
	docker build -t ${KUMA_IMAGE} .

build: build-base build-kuma

push-base:
	docker push ${BASE_IMAGE}

push-kuma:
	docker push ${KUMA_IMAGE}

push: push-base push-kuma

tag-latest:
	docker tag -f ${BASE_IMAGE} ${BASE_IMAGE_LATEST}
	docker tag -f ${KUMA_IMAGE} ${KUMA_IMAGE_LATEST}

push-latest: push tag-latest
	docker push ${BASE_IMAGE_LATEST}
	docker push ${KUMA_IMAGE_LATEST}

up:
	docker-compose up -d

bash: up
	docker exec -it kuma_web_1 bash

shell_plus: up
	docker exec -it kuma_web_1 ./manage.py shell_plus

# Those tasks don't have file targets
.PHONY: test coveragetest intern locust clean locale install compilecss compilejsi18n collectstatic localetest localeextract localecompile localerefresh
