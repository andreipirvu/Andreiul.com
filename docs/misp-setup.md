# MISP setup (Lab 6)

MISP runs from a separate clone of `misp-docker`, next to this repository and never inside
it, on my laptop only.

## Rules of engagement

- Shodan is queried only for an IP I own or am authorised to assess: my own VPS. The IP is
  kept in `secrets/intel.enc.yaml`, never in a commit, a screenshot or this file.
- Indicators from MISP are live intelligence: `enrich/` is git-ignored, and TLP:AMBER or
  higher stays off any screenshot I share.
- The MISP key and the Shodan key exist in git only as SOPS ciphertext (R-02).

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
