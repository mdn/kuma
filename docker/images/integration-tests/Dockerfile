FROM python:2.7-slim@sha256:c18974c4384a0ee6bb68086a4ac807c3a713a98302ea8dfb3117829385a59694

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
