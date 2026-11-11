# Registrul de riscuri: andreiul.com

Fiecare control din acest repository răspunde unui rând de aici, iar fiecare pull request
menționează ID-urile riscurilor pe care le tratează. Adaptat după modelul din
[secops-demo](https://github.com/cybrd0ne/secops-demo), pentru un site static servit de nginx.

Probabilitatea (P) și impactul (I) se notează de la 1 la 5. Scorul inerent este P × I,
înainte de control; scorul rezidual este notat din nou după control.
Benzi: 1–7 Scăzut, 8–14 Mediu, 15–25 Ridicat.

| ID | Activ | Amenințare | ATT&CK | P | I | Inerent | Control | Rezidual | Dovadă | Status |
|----|-------|------------|--------|---|---|---------|---------|----------|--------|--------|
| R-01 | Branch-ul `main` | Modificare ajunsă pe `main` fără review (inclusiv de la un agent AI) | — | 3 | 4 | 12 (Mediu) | Ruleset GitHub: PR obligatoriu, verificări CI obligatorii, fără push direct; workflow `governance`; hook `no-commit-to-branch` | 4 (Scăzut) | `.github/workflows/governance.yml`, `.pre-commit-config.yaml`, ruleset (vezi SECURITY.md) | Implementat în repo; ruleset-ul se activează manual |
| R-02 | Secrete (chei, parole, tokenuri) | Secret comis în repo-ul public | T1552.001 | 4 | 5 | 20 (Ridicat) | gitleaks în pre-commit și în CI pe tot istoricul; `.gitignore` pentru `*.env`, chei, certificate; guard Claude Code care blochează citirea fișierelor secrete | 5 (Scăzut) | `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `.gitignore`, `.claude/` | Implementat |
| R-03 | Paginile site-ului | Script compromis pe CDN (cdnjs) rulează pe site | T1195.002 | 2 | 4 | 8 (Mediu) | Subresource Integrity (SHA-384) pe toate scripturile externe; verificare SRI în pre-commit și CI | 2 (Scăzut) | `site/app.html`, `scripts/check_sri.py` | Implementat |
| R-04 | Serverul nginx | Versiune expusă în header-ul `Server`, indexată de Shodan | T1595.002 | 4 | 3 | 12 (Mediu) | `server_tokens off` global (`conf.d/security.conf`); actualizări de securitate Ubuntu 22.04; monitorizare săptămânală a banner-ului | 3 (Scăzut) | `deploy/nginx/conf.d/security.conf`, `.github/workflows/site-monitor.yml` | Implementat pe server (11.11.2026) |
| R-05 | Vizitatorii site-ului | XSS, clickjacking, downgrade la HTTP din lipsa headerelor de securitate | T1189 | 3 | 3 | 9 (Mediu) | CSP pe fiecare pagină (strict pe pagina principală, fără script inline), HSTS, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy; redirect HTTP → HTTPS | 3 (Scăzut) | `deploy/nginx/`, `site/main.js` | Implementat în repo; se închide după deploy |
| R-06 | Reputația site-ului | Cine găsește o vulnerabilitate nu știe cui s-o raporteze | — | 3 | 2 | 6 (Scăzut) | `/.well-known/security.txt` (RFC 9116) și SECURITY.md | 2 (Scăzut) | `site/.well-known/security.txt`, `SECURITY.md` | Implementat în repo; live după deploy |
| R-07 | Pipeline-ul CI | Acțiune GitHub compromisă printr-un tag mutat | T1195.001 | 3 | 4 | 12 (Mediu) | Acțiuni fixate pe SHA complet; token read-only; `persist-credentials: false`; zizmor în CI; Dependabot pentru actualizări | 3 (Scăzut) | `.github/workflows/`, `.github/dependabot.yml` | Implementat |
| R-08 | Secretele NexusJobs (parola DB, `JWT_SECRET`) | Fișiere din aplicație servite public pentru că aplicația stă în webroot-ul site-ului (`/nexusjobs/backend/.env` era descărcabil) | T1552.001 | 5 | 5 | 25 (Ridicat) | `/nexusjobs/` și dotfile-urile blocate în nginx; parola DB și `JWT_SECRET` schimbate (11.11.2026); monitorizare; de făcut: mutarea aplicației din `/var/www/andreiul.com` și rulare sub un user dedicat, nu root | 6 (Scăzut) | `deploy/nginx/sites-available/andreiul`, `scripts/check-live-headers.sh` | Implementat pe server; mutarea aplicației: Deschis |

## Ce rămâne de făcut manual

- **R-05, R-06:** instalează `deploy/nginx/` pe server (pașii sunt în `deploy/nginx/README.md`),
  apoi rulează manual workflow-ul `site-monitor`. Când trece, actualizează statusul în „Verificat”.
- **R-08:** mută NexusJobs din `/var/www/andreiul.com/nexusjobs` într-un folder propriu și rulează-l
  sub un user dedicat în loc de `root`. Actualizează `root` și `alias` în blocul `jobs.andreiul.com`
  și scriptul de deploy (care trebuie să creeze `.env` cu `chmod 600`).

## Incidente

**11.11.2026, R-08.** `https://www.andreiul.com/nexusjobs/backend/.env` era public (HTTP 200) din
august. Logurile nginx (circa 14 zile) nu arată descărcări străine. Fișierul a fost blocat (404),
iar parola bazei de date și `JWT_SECRET` au fost schimbate în aceeași seară. Logurile SSH nu arată
autentificări străine.

## Valori de status

Deschis, Implementat (controlul există), Verificat (dovada a fost verificată pe live),
Acceptat (risc asumat, cu motivul în coloana Control).
