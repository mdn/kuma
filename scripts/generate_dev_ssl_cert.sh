#!/bin/bash

SSL_DIR=$1
SERVER_NAME=$2
if [[ -z "$SSL_DIR" || -z "$SERVER_NAME" ]]; then
    echo "Generate a self-signed key and certificate for local development."
    echo "Usage: $0 <folder for files> <server name>"
    exit 1
fi

SSL_KEY="$SSL_DIR/server.key"
SSL_CRT="$SSL_DIR/server.crt"

if [[ ! -f "$SSL_KEY" || ! -f "$SSL_CRT" ]]; then
    openssl req \
        -x509 \
        -sha256 \
        -nodes \
        -newkey rsa\:2048 \
        -days 365 \
        -keyout $SSL_KEY \
        -out $SSL_CRT \
        -subj "/CN=$SERVER_NAME"
else
    echo "$SSL_KEY and $SSL_CRT already exist."
fi
