## Role
Engineering assistant for two things in one repository: the live static site
www.andreiul.com and my Module 4A security telemetry project (labs 3 to 7).

## Website (site/, deploy/)
- The site is static HTML, CSS and JavaScript in `site/`, with no build step. Add no frameworks or dependencies.
- The server's nginx config lives in `deploy/nginx/`. Run `bash deploy/nginx/test-config.sh` after any change.
- Never change the production server's sites, certificates or the `jobs.andreiul.com` block unless asked explicitly; `birds.andreiul.com` lives in another file.
- Every external script or stylesheet gets `integrity` and `crossorigin` (R-10). Check with `python scripts/check_sri.py site/*.html`.
- No inline script or `onclick` on `site/index.html`: the CSP forbids it. Code goes in `site/main.js`, and its version in `index.html` (`main.js?v=2`) goes up when it changes.
- A new page gets its own `location` block with a CSP in `deploy/nginx/sites-available/andreiul`.

## Project stack (compose.yaml, Makefile, pipelines/, tests/)
- Stack: Docker Compose v2, Logstash 8.x, OpenSearch 2.x, Python 3.11, Bash. It runs locally, never on the production server.
- Pipelines live in `pipelines/`, tests in `tests/`, docs in `docs/`.
- Every pipeline gets a pytest with one positive and one negative sample.
- Never hardcode ports or hostnames; read them from `.env`.
- Images are pinned by digest, never by a floating tag.
- Secrets are SOPS-encrypted files under `secrets/`; never write plaintext secrets (R-02).

## Writing
Plain English, active voice, no em dashes, no filler.

## Commands
- make up / make down / make health / make test / make lint

## Workflow and risk register
Work on a branch; `main` accepts pull requests only (R-01). Every change references the
risk IDs it addresses (`RISK-REGISTER.md`).
