#!/bin/sh

cd $(dirname $0)

git submodule update --init --recursive

# create the container that will build the static 
# assets

# clean out the static folder
rm -rm static/*

tar \
   --create \
   --exclude-vcs \
   --exclude=./static \
   --exclude=kumascript \
   --exclude=vendor/*/docs \
   --to-stdout . | \
   docker build -t kuma:builder -f Dockerfile-builder -

# Build the static assets
docker run -it --rm=true -v "$PWD/static:/app/static" kuma:builder \
    sh -c './manage.py collectstatic --noinput && ./manage.py compilejsi18n'

tar \
   --create \
   --exclude-vcs \
   --exclude=./media \
   --exclude=kumascript \
   --exclude=kuma/static \
   --exclude=vendor/*/docs \
   --to-stdout . | \
   docker build -t kuma:latest -f Dockerfile-production -
