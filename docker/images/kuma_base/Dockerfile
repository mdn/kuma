FROM python:3.8.0-slim@sha256:7df1fd6bb894e03b488c01fd05eaa4dd677f5b57d800c209f7f0af9867137df9

# Set the environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # gunicorn concurrency
    WEB_CONCURRENCY=4

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    dirmngr \
    libsasl2-modules \
    gettext \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libmagic-dev \
    default-libmysqlclient-dev \
    default-mysql-client

# add non-privileged user
RUN useradd --uid 1000 --shell /bin/bash --create-home kuma \
    && mkdir -p app \
    && chown kuma:kuma /app \
    && chmod 775 /app

# install Python libraries
WORKDIR /app
COPY --chown=kuma:kuma ./pyproject.toml ./poetry.lock /app/
RUN pip install poetry~=1.1.6 \
    && POETRY_VIRTUALENVS_CREATE=false poetry install --no-root \
    && rm -rf ~/.cache/pip ~/.cache/pypoetry/cache

# setup default run parameters
USER kuma
WORKDIR /app
EXPOSE 8000
