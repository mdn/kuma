FROM python:2.7-slim@sha256:58b8f53af8d228fe1a99364afd393e1b225d4d8af88c2d0f9f81b62164031953

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
