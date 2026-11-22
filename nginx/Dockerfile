# Lab 3 front door as an image: nginx terminates TLS in front of OpenSearch Dashboards.
# Pinned by tag and digest, so the build never floats. 1.30.7-alpine-slim: Trivy finds
# no HIGH or CRITICAL issues (1.27-alpine had 70). Same digest as compose.yaml.
FROM nginx:1.30.7-alpine-slim@sha256:8c950211a641ec5b23f265450517001f6bcca533666120ebe36cb4cff3d00a55

# Site config only. Certificates stay out of the image and are mounted at runtime
# from certs/ (git-ignored), exactly as in compose.yaml.
COPY frontdoor.conf /etc/nginx/conf.d/default.conf

EXPOSE 443
