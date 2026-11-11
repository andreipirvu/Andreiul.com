#!/usr/bin/env bash
# Validate deploy/nginx with `nginx -t` in a throwaway prefix, using a self-signed
# certificate in place of the real Let's Encrypt one. Ports move to 127.0.0.1:18080/18443
# and IPv6 listeners are dropped, so the test needs no root and no IPv6.
# Used by CI and runnable locally.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/snippets" "$work/certs" "$work/logs" "$work/www"
cp "$here/snippets/security-headers.conf" "$work/snippets/"

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=www.andreiul.com" \
  -keyout "$work/certs/privkey.pem" -out "$work/certs/fullchain.pem" 2>/dev/null

sed -e "s#/etc/letsencrypt/live/andreiul.com#$work/certs#g" \
    -e "s#/var/www/andreiul.com#$work/www#g" \
    -e "/listen \[::\]/d" \
    -e "s#listen 80;#listen 127.0.0.1:18080;#" \
    -e "s#listen 443 #listen 127.0.0.1:18443 #" \
    "$here/andreiul.com.conf" > "$work/site.conf"

cat > "$work/nginx.conf" <<EOF
pid $work/nginx.pid;
error_log $work/logs/error.log;
events {}
http {
  access_log off;
  include $work/site.conf;
}
EOF

nginx -t -p "$work" -c "$work/nginx.conf"
