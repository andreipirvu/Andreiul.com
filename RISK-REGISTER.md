# Risk Register: andreiul.com

This repository is two things at once: the source and server configuration of the live
site www.andreiul.com, and my Module 4A project, built lab by lab from the
[secops-demo](https://github.com/cybrd0ne/secops-demo) instructions. The project stack
(OpenSearch, Logstash, MISP) runs locally with Docker and never on the production server.

Every control in this repository answers a row here, and every pull request cites the
risk IDs it closes. R-01 to R-09 keep the course numbering. R-10 and above are risks of
the live website.

Score likelihood (L) and impact (I) from 1 to 5 (see Scales). Inherent score is L × I.
Residual likelihood (RL) and impact (RI) are scored again after the control. A row marked
Implemented or Verified points to something a reviewer can open in this repository.

## Register

| ID | Register | Asset | Threat / technique | ATT&CK | L | I | Inherent | Control | RL | RI | Residual | Evidence | Status |
|----|----------|-------|--------------------|--------|---|---|----------|---------|----|----|----------|----------|--------|
| R-01 | Operational | `main` branch | An AI agent or I commit code that bypasses review | — | 4 | 4 | 16 (High) | Ruleset: pull request and status checks required, no direct push, no force push; governance workflow fails on any commit to `main` without a merged PR; `no-commit-to-branch` pre-commit hook | 1 | 4 | 4 (Low) | `.github/workflows/governance.yml`; `.pre-commit-config.yaml`; `docs/ruleset-main.json` (Lab 4) | Implemented |
| R-02 | Operational | Repository secrets | A plaintext key or password is committed | T1552.001 | 4 | 5 | 20 (High) | gitleaks in pre-commit and in CI over the full history; `.gitignore` for env files, keys and certificates; Claude Code guard blocks reading secret paths; SOPS/age so only ciphertext is committed | 2 | 3 | 6 (Low) | `.pre-commit-config.yaml`; `.github/workflows/ci.yml`; `.claude/`; `.sops.yaml` and `secrets/*.enc.yaml` (Lab 3) | Implemented |
| R-03 | Internal | Logstash enrichment pipeline | Malformed or unmapped log input breaks normalisation and detections go blind | — | 3 | 4 | 12 (Medium) | Detection as code: Sigma rules with positive and negative samples, rule tests and pipeline tests in CI on every pull request | 1 | 4 | 4 (Low) | `detections/`; `tests/` (Lab 5) | Open |
| R-04 | External | Network telemetry | Traffic to or from known-malicious IPs goes unflagged | T1071 | 4 | 4 | 16 (High) | MISP indicators pulled into a Logstash `translate` lookup; matching events tagged `threat_match` and risk-scored | 2 | 3 | 6 (Low) | `scripts/misp_pull.py`; `pipelines/suricata.conf` (Lab 6) | Open |
| R-05 | External | Public nginx (www.andreiul.com and the lab front door) | Exposed service or version banner indexed by Shodan | T1595.002 | 3 | 3 | 9 (Medium) | `server_tokens off` on the server (applied 2026-11-11); weekly `site-monitor` checks the banner; Shodan snapshot of the server IP (Lab 6), alert on change (Lab 7) | 1 | 3 | 3 (Low) | `deploy/nginx/conf.d/security.conf`; `.github/workflows/site-monitor.yml`; `scripts/exposure_check.py` (Lab 6) | Implemented |
| R-08 | Operational | CI pipeline | A third-party action's tag is moved to malicious code | T1195.001 | 3 | 4 | 12 (Medium) | Every action pinned to a full commit SHA; repository setting requires SHA pinning; zizmor audits the whole repository; Dependabot with a 7-day cooldown | 1 | 4 | 4 (Low) | `.github/workflows/`; `.github/dependabot.yml`; settings screenshots (Lab 4) | Implemented |
| R-09 | Operational | Repository secrets in CI | A fork pull request runs a workflow that reads secrets | T1552 | 2 | 5 | 10 (Medium) | Only `pull_request` triggers, never `pull_request_target`; read-only default token, widened per job; approval required for all external contributors | 1 | 5 | 5 (Low) | `.github/workflows/`; settings screenshots (Lab 4) | Implemented |
| R-10 | External | Website pages | A compromised CDN script (cdnjs) runs on the site | T1195.002 | 2 | 4 | 8 (Medium) | Subresource Integrity (SHA-384) on every third-party script, checked in pre-commit and CI | 1 | 4 | 4 (Low) | `site/app.html`; `scripts/check_sri.py` | Verified |
| R-11 | External | Website visitors | XSS, clickjacking or HTTPS downgrade for lack of security headers | T1189 | 3 | 3 | 9 (Medium) | Per-page Content-Security-Policy (no inline script on the main page), HSTS, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy | 1 | 3 | 3 (Low) | `deploy/nginx/`; `site/main.js`; `scripts/check-live-headers.sh` | Verified |
| R-12 | External | Site reputation | A researcher who finds a flaw has no way to report it | — | 3 | 2 | 6 (Low) | `/.well-known/security.txt` (RFC 9116) and private vulnerability reporting | 1 | 2 | 2 (Low) | `site/.well-known/security.txt`; `SECURITY.md` | Verified |
| R-13 | Internal | Secrets of applications hosted on the same server | Application files served by the web server expose credentials | T1552.001 | 4 | 5 | 20 (High) | Application paths and dotfiles blocked in nginx; credentials rotated; checked weekly by `site-monitor` | 1 | 5 | 5 (Low) | `deploy/nginx/sites-available/andreiul`; `scripts/check-live-headers.sh` | Implemented |

R-06 and R-07 are reserved for the course numbering.

## How each control lands in the repository

**R-01.** GitHub refuses a direct push to `main`. On top of that, `governance.yml` fails
whenever a commit reaches `main` without a merged pull request, and the
`no-commit-to-branch` hook stops the mistake locally before it reaches the remote.

**R-02.** gitleaks refuses a commit that carries a key, and CI scans the whole history
again, because a local hook can be skipped. Secrets the project needs (the OpenSearch admin
password, the MISP and Shodan keys) exist in git only as SOPS ciphertext; the age private
key stays on my machine.

**R-03.** Every rule ships with a positive sample, a negative sample with a realistic near
miss, a rule test and a pipeline test that runs the real Logstash. A change that breaks
normalisation fails the pull request.

**R-04.** Indicators from MISP land in a lookup file that Logstash reads with `translate`.
A record whose destination matches is tagged and scored; a clean record is untouched.

**R-05.** The live server no longer reports its nginx version, and `site-monitor` checks
that weekly. Lab 6 adds a Shodan snapshot of the server's own IP, which Lab 7 diffs.

**R-08 and R-09.** A moved tag cannot run here, because every `uses:` names a commit SHA
and GitHub refuses unpinned actions. Workflows that run code from pull requests get a
read-only token and no secrets.

**R-10 to R-13** protect the live site. Their controls were deployed and checked in the
browser on 2026-11-11.

## Renumbering (2026-11-22)

The register was renumbered to follow the course IDs. Commits and pull requests made
before this date cite the old IDs:

| Before | After | Topic |
|--------|-------|-------|
| R-01 | R-01 | Review bypass on `main` |
| R-02 | R-02 | Secrets in the repository |
| R-03 | R-10 | CDN scripts (SRI) |
| R-04 | R-05 | nginx version banner |
| R-05 | R-11 | Security headers |
| R-06 | R-12 | security.txt |
| R-07 | R-08 | Moved action tags |
| R-08 | R-13 | Application secrets served by the web server |

## Scales

| Score | Likelihood | Impact |
|-------|-----------|--------|
| 1 | Rare: no realistic path with current controls | Negligible: no effect on C, I or A |
| 2 | Unlikely: needs unusual conditions or insider error | Minor: contained, fixed in hours, no data exposure |
| 3 | Possible: plausible within the project lifetime | Moderate: one component degraded, limited exposure |
| 4 | Likely: expected without the control | Major: detections blind or secrets exposed |
| 5 | Almost certain: already observed or trivially triggered | Severe: full compromise of the project or its credentials |

## Status values

Open, Implemented (the control exists), Verified (the evidence was reviewed), Accepted
(risk left as is, with the reason in the Control column).
