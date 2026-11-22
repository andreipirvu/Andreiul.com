# MISP setup (Lab 6)

MISP runs from a separate clone of `misp-docker`, next to this repository and never inside
it, on my laptop only.

## Rules of engagement

- Shodan is queried only for an IP I own or am authorised to assess: my own VPS. The IP is
  kept in `secrets/intel.enc.yaml`, never in a commit, a screenshot or this file.
- Indicators from MISP are live intelligence: `enrich/` is git-ignored, and TLP:AMBER or
  higher stays off any screenshot I share.
- The MISP key and the Shodan key exist in git only as SOPS ciphertext (R-02).

## TLS for the MISP web server

Current misp-docker runs nginx in its own container, which refuses to start when
`BASE_URL` is `https://` and no certificate is mounted. A self-signed certificate for
`localhost` goes into `ssl/` of the misp-docker clone (`cert.pem`, `key.pem`) before the
first start:

```bash
mkdir -p ssl && openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout ssl/key.pem -out ssl/cert.pem
```

`make intel` then talks to MISP without certificate verification (`MISP_CA` empty), which
is acceptable only because MISP runs on the same machine.

## Images actually pulled

misp-docker runs floating `latest` images by default. What was pulled on the day:

<!-- Paste the output of: docker images --digests | grep misp -->

| Date | Output |
|------|--------|
| YYYY-MM-DD | ... |

## Feed

| Feed | Enabled | Fetched on | Events with attributes |
|------|---------|------------|------------------------|
| CIRCL OSINT Feed | yes | YYYY-MM-DD | ... |

## Admin account

The default `admin@admin.test` / `admin` password was changed at first login. The API key
was created under Administration, List Auth Keys, and stored only in
`secrets/intel.enc.yaml`.
