FROM quay.io/mozmar/base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    build-essential python python-dev python-pip python-setuptools \
                    libxml2-dev libxslt1.1 libxslt1-dev zlib1g-dev

# Defaults
ENV PYTEST_PROCESSES 5
ENV PRIVACY "public restricted"
ENV TESTS_PATH /app/tests
ENV RESULTS_PATH /app/results
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

COPY ./requirements /app/requirements

# Install requirements
RUN pip install --no-cache-dir -r requirements/test.txt

COPY tests /app/tests
