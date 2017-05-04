FROM quay.io/mozmar/kuma_base:latest
COPY . /app
# the following is needed until the --user flag is added to COPY
# see https://github.com/moby/moby/issues/30110
USER root
RUN chown -R kuma /app
USER kuma

ENV DJANGO_SETTINGS_MODULE=kuma.settings.prod

RUN make localecompile
RUN make build-static && rm -rf build
