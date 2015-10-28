# This is a work in progress.
#
# The preferred way to set up development is still using Vagrant as documented here:
# http://kuma.readthedocs.org/en/latest/installation.html

FROM python:2.7.10

RUN useradd --create-home --home-dir /app --shell /bin/bash app
WORKDIR /app

RUN apt-get update && \
  apt-get install -y \
    libtidy-0.99-0

COPY requirements/compiled.txt /app/requirements/compiled.txt

RUN pip install --build ./build --no-cache-dir \
    --disable-pip-version-check \
    -r requirements/compiled.txt

COPY . /app
