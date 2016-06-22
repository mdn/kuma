# This is a work in progress.
#
# The preferred way to set up development is still using Vagrant as documented here:
# http://kuma.readthedocs.org/en/latest/installation.html

FROM quay.io/mozmar/kuma_base:latest
COPY . /app
RUN mkdir -p build/assets build/locale && ./manage.py collectstatic --noinput
RUN ./manage.py update_product_details
