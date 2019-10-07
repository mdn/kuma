ifeq ($(shell which git),)
# git is not available
VERSION ?= undefined
KS_VERSION ?= undefined
export KUMA_REVISION_HASH ?= undefined
export KUMASCRIPT_REVISION_HASH ?= undefined
else
# git is available
VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
KS_VERSION ?= $(shell cd kumascript && git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
export KUMA_REVISION_HASH ?= $(shell git rev-parse HEAD)
export KUMASCRIPT_REVISION_HASH ?= $(shell cd kumascript && git rev-parse HEAD)
endif
BASE_IMAGE_NAME ?= kuma_base
KUMA_IMAGE_NAME ?= kuma
KUMASCRIPT_IMAGE_NAME ?= kumascript
IMAGE_PREFIX ?= mdnwebdocs
BASE_IMAGE ?= ${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:${VERSION}
BASE_IMAGE_PY3 ?= ${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:py3
BASE_IMAGE_LATEST ?= ${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:latest
IMAGE ?= $(BASE_IMAGE_LATEST)
KUMA_IMAGE ?= ${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:${VERSION}
KUMA_IMAGE_LATEST ?= ${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:latest
KUMASCRIPT_IMAGE ?= ${IMAGE_PREFIX}/${KUMASCRIPT_IMAGE_NAME}\:${KS_VERSION}
KUMASCRIPT_IMAGE_LATEST ?= ${IMAGE_PREFIX}/${KUMASCRIPT_IMAGE_NAME}\:latest

target = kuma
requirements = -r requirements/local.txt
# set Django settings module if not already set as env var
export DJANGO_SETTINGS_MODULE ?= kuma.settings.testing

# Note: these targets should be run from the kuma vm
test:
	py.test $(target)

coveragetest: clean
	py.test --cov=$(target) --no-cov-on-fail $(target)
	# Generate the coverage.xml file from the .coverage file
	# so we don't need to `pip install codecov`.
	coverage xml

coveragetesthtml: coveragetest
	coverage html

locust:
	locust -f tests/performance/smoke.py --host=https://developer.allizom.org

webpack:
	@ echo "## Running webpack ##"
	@ npm run webpack:prod

compilejsi18n:
	@ echo "## Generating JavaScript translation catalogs ##"
	@ mkdir -p build/locale
	@ python manage.py compilejsi18n

compile-react-i18n:
	@ echo "## Generating React translation catalogs ##"
	@ mkdir -p build/locale
	@ python manage.py compilejsi18n -d react -f json

collectstatic:
	@ echo "## Compiling (Sass), collecting, and building static files ##"
	@ python manage.py collectstatic --noinput

build-static: webpack compilejsi18n compile-react-i18n collectstatic

install:
	@ echo "## Installing $(requirements) ##"
	@ pip install $(requirements)

clean:
	rm -rf .coverage build/ tmp/emails/*.log
	find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -delete
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
	cd locale; ../scripts/compile-mo.sh .

localerefresh: localeextract localetest localecompile build-static

pull-base:
	docker pull ${BASE_IMAGE}

pull-kuma:
	docker pull ${KUMA_IMAGE}

pull-kumascript:
	docker pull ${KUMASCRIPT_IMAGE}

pull-base-latest:
	docker pull ${BASE_IMAGE_LATEST}

pull-kuma-latest:
	docker pull ${KUMA_IMAGE_LATEST}

pull-latest: pull-base-latest pull-kuma-latest

build-base:
	docker build -f docker/images/kuma_base/Dockerfile -t ${BASE_IMAGE} .

build-base-py3:
	docker build -f docker/images/kuma_base/Dockerfile-py3 -t ${BASE_IMAGE_PY3} .

build-kuma:
	docker build --build-arg REVISION_HASH=${KUMA_REVISION_HASH} \
	-f docker/images/kuma/Dockerfile -t ${KUMA_IMAGE} .

build-kumascript:
	docker build --no-cache \
	--build-arg REVISION_HASH=${KUMASCRIPT_REVISION_HASH} \
	-f kumascript/docker/Dockerfile -t ${KUMASCRIPT_IMAGE} .

build-kumascript-with-all-tags:
	docker build --no-cache \
	--build-arg REVISION_HASH=${KUMASCRIPT_REVISION_HASH} \
	-f kumascript/docker/Dockerfile -t ${KUMASCRIPT_IMAGE} \
	-t ${KUMASCRIPT_IMAGE_LATEST} .

build: build-base build-kuma build-kumascript

push-base:
	docker push ${BASE_IMAGE}

push-kuma:
	docker push ${KUMA_IMAGE}

push-kumascript:
	docker push ${KUMASCRIPT_IMAGE}

push: push-base push-kuma

tag-latest:
	docker tag ${BASE_IMAGE} ${BASE_IMAGE_LATEST}
	docker tag ${KUMA_IMAGE} ${KUMA_IMAGE_LATEST}

push-latest: push tag-latest
	docker push ${BASE_IMAGE_LATEST}
	docker push ${KUMA_IMAGE_LATEST}

up:
	docker-compose up -d

bash: up
	docker-compose exec web bash

shell_plus: up
	docker-compose exec web ./manage.py shell_plus

pythonlint:
	flake8 kuma docs tests

jslint:
	npm run eslint
	npm run stylelint
	npm run pretty

lint: pythonlint jslint

npmrefresh:
	cd /tools
	echo '{"lockfileVersion": 1}' > package-lock.json
	npm install

# Those tasks don't have file targets
.PHONY: test coveragetest locust clean locale install compilejsi18n collectstatic localetest localeextract localecompile localerefresh npmrefresh webpack compile-react-i18n
