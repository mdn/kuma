FROM python:2.7-slim@sha256:1405fa2f8e9a232e2f60cafbb2b06ca2f1e0f577f4b4c397c361d6dba59fd24e

WORKDIR /app

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        mime-support \
        build-essential \
        libxml2-dev \
        libxslt1.1 \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Defaults
ENV PYTEST_PROCESSES 5
ENV PRIVACY "public restricted"
ENV TESTS_PATH /app/tests
ENV RESULTS_PATH /app/results

COPY ./requirements /app/requirements

# Install requirements
RUN pip install --no-cache-dir -r requirements/test.txt

COPY tests /app/tests
