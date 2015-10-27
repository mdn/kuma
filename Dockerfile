FROM python:2.7

# This is a work in progress.

# app will run as the app user
RUN useradd --create-home --home-dir /app --shell /bin/bash app
WORKDIR /app

# run these as root
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt && \
    rm -rf /root/.cache/

COPY . /app

USER app
