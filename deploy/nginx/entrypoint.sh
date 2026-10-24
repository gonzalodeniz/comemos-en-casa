#!/bin/sh
set -eu

if [ -s /etc/letsencrypt/live/gonzalodeniz.com/fullchain.pem ] && [ -s /etc/letsencrypt/live/gonzalodeniz.com/privkey.pem ]; then
    cp /etc/nginx/tls.conf /etc/nginx/conf.d/default.conf
else
    cp /etc/nginx/bootstrap.conf /etc/nginx/conf.d/default.conf
fi

exec /docker-entrypoint.sh "$@"
