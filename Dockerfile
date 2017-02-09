# This is a work in progress.
#
# The preferred way to set up development is still using Vagrant as documented here:
# https://kuma.readthedocs.io/en/latest/installation.html

FROM quay.io/mozmar/kuma_base:latest
COPY . /app
# the following is needed until the --user flag is added to COPY
# see https://github.com/docker/docker/pull/28499
USER root
RUN chown -R kuma /app
USER kuma

ENV DJANGO_SETTINGS_MODULE=kuma.settings.prod

RUN make localecompile
RUN make build-static && rm -rf build
