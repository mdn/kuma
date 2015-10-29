#!/bin/sh

cd $(dirname $0)

git submodule update --init --recursive

# create the container that will build the static 
# assets

# clean out the static folder
rm -r static/*

# make sure the build container is updated
# the build container only includes the necessary 
# system dependencies to build out the static assets
docker build -t kuma:builder -f Dockerfile-builder .

# Build the static assets by volume mounting the 
# current source code
docker run -it --rm=true -v "$PWD:/app" kuma:builder \
    sh -c './manage.py collectstatic --noinput && ./manage.py compilejsi18n'

tar \
   --create \
   --exclude-vcs \
   --exclude=./media \
   --exclude=./kumascript \
   --exclude=./kuma/static \
   --exclude=./vendor/*/docs \
   --exclude=./provisioning \
   --exclude=./etc \
   --exclude=./docker \
   --exclude=./configs \
   --to-stdout . | \
   docker build -t kuma:latest -f Dockerfile-production -
