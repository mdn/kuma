VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
BASE_IMAGE_NAME ?= kuma_base
KUMA_IMAGE_NAME ?= kuma
REGISTRY ?= quay.io/
IMAGE_PREFIX ?= mozmar
BASE_IMAGE ?= ${REGISTRY}${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:${VERSION}
BASE_IMAGE_LATEST ?= ${REGISTRY}${IMAGE_PREFIX}/${BASE_IMAGE_NAME}\:latest
IMAGE ?= $(BASE_IMAGE_LATEST)
KUMA_IMAGE ?= ${REGISTRY}${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:${VERSION}
KUMA_IMAGE_LATEST ?= ${REGISTRY}${IMAGE_PREFIX}/${KUMA_IMAGE_NAME}\:latest
TEST ?= test #other options in docker-compose.test.yml
DEIS_PROFILE ?= dev-usw
DEIS_APP ?= mdn-dev
DEIS_BIN ?= deis
WORKERS ?= 1
DB_PASS ?= kuma # default for ephemeral demo DBs

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

compilejsi18n:
	@ echo "## Generating JavaScript translation catalogs ##"
	@ mkdir -p build/locale
	@ python manage.py compilejsi18n

collectstatic:
	@ echo "## Compiling (Sass), collecting, and building static files ##"
	@ python manage.py collectstatic --noinput

build-static: compilejsi18n collectstatic

install:
	@ echo "## Installing $(requirements) ##"
	@ pip install $(requirements)

clean:
	rm -rf .coverage build/
	find kuma -name '*.pyc' -exec rm {} \;
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
	cd locale; ./compile-mo.sh .

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

deis-create:
	DEIS_PROFILE=${DEIS_PROFILE} ${DEIS_BIN} create ${DEIS_APP} --no-remote || \
	${DEIS_BIN} apps | grep -q ${DEIS_APP}

deis-config:
	DEIS_PROFILE=${DEIS_PROFILE} ${DEIS_BIN} config:set -a ${DEIS_APP} $(shell cat .env-dist) || true

deis-create-and-or-config:
	make deis-create || echo already created
	sleep 5
	make deis-config

deis-pull:
	DEIS_PROFILE=${DEIS_PROFILE} ${DEIS_BIN} pull ${KUMA_IMAGE} -a ${DEIS_APP}

deis-scale-worker:
	DEIS_PROFILE=${DEIS_PROFILE} ${DEIS_BIN} ps:scale worker=${WORKERS} -a ${DEIS_APP}

k8s-migrate:
	kubectl --namespace ${DEIS_APP} exec \
	$(shell kubectl --namespace ${DEIS_APP} get pods | grep ${DEIS_APP}-cmd | awk '{print $$1}') \
	python manage.py migrate

wait-mysql:
	bash -c "if ! kubectl -n ${DEIS_APP} get pods | grep mysql | grep -q Running; then sleep 2; make wait-mysql; fi"

deis-migrate: wait-mysql
	DEIS_PROFILE=${DEIS_PROFILE} ${DEIS_BIN} run -a ${DEIS_APP} python manage.py migrate

tag-latest:
	docker tag ${BASE_IMAGE} ${BASE_IMAGE_LATEST}
	docker tag ${KUMA_IMAGE} ${KUMA_IMAGE_LATEST}

push-latest: push tag-latest
	docker push ${BASE_IMAGE_LATEST}
	docker push ${KUMA_IMAGE_LATEST}

up:
	docker-compose up -d

bash: up
	docker exec -it kuma_web_1 bash

shell_plus: up
	docker exec -it kuma_web_1 ./manage.py shell_plus

compose-test:
	docker-compose -f docker-compose.yml -f docker-compose.test.yml run $(TEST)
	docker-compose -f docker-compose.yml -f docker-compose.test.yml stop

# Those tasks don't have file targets
.PHONY: test coveragetest locust clean locale install compilejsi18n collectstatic localetest localeextract localecompile localerefresh
