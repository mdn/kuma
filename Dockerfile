# This is a work in progress.
#
# The preferred way to set up development is still using Vagrant as documented here:
# https://kuma.readthedocs.io/en/latest/installation.html

FROM quay.io/mozmar/kuma_base:latest
COPY . /app
RUN make localecompile
RUN make build-static && rm -rf build
