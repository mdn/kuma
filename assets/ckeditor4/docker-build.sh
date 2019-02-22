#!/bin/bash

USER=$(whoami)
docker run -v $(pwd):/ckeditor openjdk:8 bash -c "
cd /ckeditor/source &&
adduser --quiet --no-create-home --disabled-password --gecos '' --uid $(id -u) --gid $(id -g) $USER &&
su -c 'bash build.sh' $USER"
