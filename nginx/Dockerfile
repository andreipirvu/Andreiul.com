# Lab 3 front door as an image: nginx terminates TLS in front of OpenSearch Dashboards.
# Pinned by tag and digest, so the build never floats; Dependabot proposes updates and
# the scan job fails on HIGH or CRITICAL (1.27-alpine had 70). compose.yaml must run the
# same digest: tests/test_pinning.py fails when the two differ.
FROM nginx:1.31.8-alpine-slim@sha256:4c734d33ee731135dc9f2349914a34551c920f4451fca8bb05bf5880eb9079e8

# Site config only. Certificates stay out of the image and are mounted at runtime
# from certs/ (git-ignored), exactly as in compose.yaml.
COPY frontdoor.conf /etc/nginx/conf.d/default.conf

EXPOSE 443
