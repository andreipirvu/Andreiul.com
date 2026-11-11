#!/usr/bin/env bash
# Validate deploy/nginx the way it runs on the live server: the server's nginx.conf
# layout (conf.d/*.conf, then sites-enabled/*), the andreiul site file next to a copy of
# the birds site, and certbot's includes. Real certificates are replaced by a
# self-signed one, ports move to 127.0.0.1:18080/18443 and IPv6 listeners are dropped,
# so the test needs no root and no IPv6.
#
#   bash deploy/nginx/test-config.sh          # nginx -t only (CI)
#   bash deploy/nginx/test-config.sh --serve  # also start nginx; prints the prefix dir
#                                             # (stop: nginx -p <dir> -c <dir>/nginx.conf -s stop)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
work="$(mktemp -d)"
chmod 755 "$work"
[ "${1:-}" = "--serve" ] || trap 'rm -rf "$work"' EXIT

mkdir -p "$work"/{snippets,conf.d,sites-enabled,le,logs,www/andreiul.com,www/birds}
cp "$here/snippets/security-headers.conf" "$work/snippets/"
cp "$here/conf.d/security.conf" "$work/conf.d/"
cp "$here/test/options-ssl-nginx.fixture" "$work/le/options-ssl-nginx.conf"
cp -r "$repo/site/." "$work/www/andreiul.com/"
mkdir -p "$work/www/andreiul.com/nexusjobs/frontend/dist" "$work/www/andreiul.com/nexusjobs/backend/uploads"
echo '<h1>jobs</h1>' > "$work/www/andreiul.com/nexusjobs/frontend/dist/index.html"
echo 'SECRET=test'   > "$work/www/andreiul.com/nexusjobs/backend/.env"
echo '<h1>birds</h1>' > "$work/www/birds/index.html"
chmod -R a+rX "$work"

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=andreiul.com" \
  -addext "subjectAltName=DNS:andreiul.com,DNS:www.andreiul.com,DNS:jobs.andreiul.com,DNS:birds.andreiul.com" \
  -keyout "$work/le/privkey.pem" -out "$work/le/fullchain.pem" 2>/dev/null
openssl dhparam -dsaparam -out "$work/le/ssl-dhparams.pem" 2048 2>/dev/null

rewrite() {
  sed -e "s#/etc/letsencrypt/live/[a-z.]*/#$work/le/#g" \
      -e "s#/etc/letsencrypt/#$work/le/#g" \
      -e "s#/var/www/#$work/www/#g" \
      -e "/listen \[::\]/d" \
      -e "s#listen 80;#listen 127.0.0.1:18080;#" \
      -e "s#listen 443 #listen 127.0.0.1:18443 #" "$1"
}
rewrite "$here/sites-available/andreiul" > "$work/sites-enabled/andreiul"
rewrite "$here/test/birds.fixture"       > "$work/sites-enabled/birds"

mime=/etc/nginx/mime.types
[ -f "$mime" ] || mime="$(dirname "$(command -v nginx)")/../conf/mime.types"

cat > "$work/nginx.conf" <<EOF
pid $work/nginx.pid;
error_log $work/logs/error.log;
events { worker_connections 64; }
http {
  include $mime;
  default_type application/octet-stream;
  access_log off;
  include $work/conf.d/*.conf;
  include $work/sites-enabled/*;
}
EOF

nginx -t -p "$work" -c "$work/nginx.conf"

if [ "${1:-}" = "--serve" ]; then
  nginx -p "$work" -c "$work/nginx.conf"
  echo "$work"
fi
