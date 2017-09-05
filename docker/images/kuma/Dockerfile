FROM quay.io/mozmar/kuma_base:latest

ARG REVISION_HASH
# Make the git commit hash permanently available within this image.
ENV REVISION_HASH $REVISION_HASH

COPY . /app
# the following is needed until the --user flag is added to COPY
# see https://github.com/moby/moby/issues/30110
USER root
RUN chown -R kuma /app
USER kuma

ENV DJANGO_SETTINGS_MODULE=kuma.settings.prod

RUN make localecompile
RUN make build-static && rm -rf build
