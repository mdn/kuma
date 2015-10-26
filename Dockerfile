# This is a work in progress.
#
# The preferred way to set up development is still using Vagrant as documented here:
# http://kuma.readthedocs.org/en/latest/installation.html

FROM python:2.7

RUN apt-get update && \
  apt-get install -y \
    nodejs \
    nodejs-legacy \
    npm \
    libtidy-0.99-0 \
    libtidy-dev \
    mysql-client  # Only for local dev.

WORKDIR /app
COPY . /app

RUN pip install --build ./build --cache-dir ./cache --no-deps \
    -r requirements/compiled.txt && \
    rm -r build cache

RUN npm install -g \
    fibers@1.0.1 \
    clean-css@2.2.16 \
    csslint@0.10.0 \
    jshint@2.7.0 \
    stylus@0.49.2 \
    uglify-js@2.4.13
