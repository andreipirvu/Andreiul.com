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

## Recorded on 2026-11-22

```
ghcr.io/misp/misp-docker/misp-modules                          latest    sha256:08d4cf35861fe2ee753023a207bb5380506f078750559620ae7f9736e186dea3   d7b3f8d74bb8   2 days ago      1.35GB
ghcr.io/misp/misp-docker/misp-core                             latest    sha256:33627106f4962082fd7c58ac0cd15576c55c8ae672ca311699fe652e59c432dc   0459c8d0e752   2 days ago      1.68GB
ghcr.io/misp/misp-docker/misp-nginx                            latest    sha256:4c1c78e634b56e96e8a801f6e325642faaa5ae236fe71f97fad0831148c796f3   fae207cf7995   2 days ago      186MB
```

Feed: CIRCL OSINT Feed, enabled and fetched on 2026-11-22.
