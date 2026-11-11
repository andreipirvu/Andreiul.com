#!/usr/bin/env bash
# Check the live site for the controls in RISK-REGISTER.md (R-04, R-05, R-06).
# Exit 1 if any check fails. Usage: scripts/check-live-headers.sh [https://www.andreiul.com]
set -uo pipefail

base="${1:-https://www.andreiul.com}"
host="${base#https://}"
fail=0

ok()  { printf 'PASS  %s\n' "$1"; }
bad() { printf 'FAIL  %s\n' "$1"; fail=1; }

headers="$(curl -sS -D - -o /dev/null --max-time 20 "$base/")" || { echo "cannot reach $base"; exit 1; }
header() { printf '%s' "$headers" | tr -d '\r' | grep -i "^$1:" | head -1 | cut -d' ' -f2-; }

# R-04: no version in the Server banner.
server="$(header server)"
if printf '%s' "$server" | grep -Eq '[0-9]+\.[0-9]+'; then
  bad "Server header exposes a version: '$server'"
else
  ok  "Server header has no version ('${server:-absent}')"
fi

# R-05: security headers.
for h in strict-transport-security content-security-policy x-content-type-options referrer-policy permissions-policy; do
  if [ -n "$(header "$h")" ]; then ok "$h present"; else bad "$h missing"; fi
done
csp="$(header content-security-policy)"
xfo="$(header x-frame-options)"
if printf '%s' "$csp" | grep -q "frame-ancestors 'none'" || [ -n "$xfo" ]; then
  ok "clickjacking protection (frame-ancestors / X-Frame-Options)"
else
  bad "no clickjacking protection"
fi
if printf '%s' "$csp" | grep -q "script-src[^;]*'unsafe-inline'"; then
  bad "main page CSP allows inline script"
fi

# HTTP must redirect to HTTPS.
code="$(curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 20 "http://$host/")"
case "$code" in
  301\ https://*|308\ https://*) ok "HTTP redirects to HTTPS ($code)";;
  *) bad "HTTP does not redirect to HTTPS (got: $code)";;
esac

# Sensitive paths must not be served.
for p in /.git/HEAD /.git/config /.env /.DS_Store; do
  c="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$base$p")"
  if [ "$c" = "200" ]; then bad "$p is served (200)"; else ok "$p not served ($c)"; fi
done

# R-06: security.txt published (RFC 9116).
c="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$base/.well-known/security.txt")"
if [ "$c" = "200" ]; then ok "/.well-known/security.txt published"; else bad "/.well-known/security.txt missing ($c)"; fi

exit "$fail"
