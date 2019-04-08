#!/bin/bash

SSL_DIR=$(dirname $0)
BASENAME="developer.127.0.0.1.nip.io"
SSL_KEY="$SSL_DIR/$BASENAME.key"
SSL_CRT="$SSL_DIR/$BASENAME.crt"
SSL_CFG="$SSL_DIR/$BASENAME.config"

if [[ ! -f "$SSL_KEY" || ! -f "$SSL_CRT" ]]; then
    openssl req \
        -x509 \
        -sha256 \
        -nodes \
        -newkey rsa\:2048 \
        -days 365 \
        -config $SSL_CFG \
        -keyout $SSL_KEY \
        -out $SSL_CRT
else
    echo "$SSL_KEY and $SSL_CRT already exist."
fi
