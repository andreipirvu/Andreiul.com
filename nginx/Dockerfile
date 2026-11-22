# Lab 3 front door as an image: nginx terminates TLS in front of OpenSearch Dashboards.
# Pinned by tag and digest, so the build never floats. 1.30.7-alpine-slim: Trivy finds
# no HIGH or CRITICAL issues (1.27-alpine had 70). Same digest as compose.yaml.
FROM python:3.9-slim@sha256:2d97f6910b16bd338d3060f261f53f144965f755599aab1acda1e13cf1731b1b

# Site config only. Certificates stay out of the image and are mounted at runtime
# from certs/ (git-ignored), exactly as in compose.yaml.
COPY frontdoor.conf /etc/nginx/conf.d/default.conf

EXPOSE 443
