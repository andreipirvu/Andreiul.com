# andreiul.com

Sursa site-ului personal [www.andreiul.com](https://www.andreiul.com): portofoliul lui Andrei Pirvu,
Software Product Owner în securitatea cibernetică pentru automotive.

## Structură

| Fișier | Ce este |
|--------|---------|
| `site/index.html` | Pagina principală: experiență, studii, certificări, proiecte, contact |
| `site/styles.css`, `site/main.js` | Stilurile și scriptul paginii principale (meniu mobil, animații, scroll) |
| `site/app.html` | SnipLearn, aplicație de învățare în pași mici (în dezvoltare) |
| `site/crypto.html` | Weather Cipher, criptare bazată pe vremea din Sibiu |
| `site/calendaruni.html` | Uni Calendar, planificator pentru master și licență |
| `site/CV_Pirvu_Andrei.pdf` | CV-ul descărcabil |

Site-ul e static (HTML, CSS și JavaScript, fără build) și e servit de nginx.

## Securitate

Controalele sunt adaptate după [secops-demo](https://github.com/cybrd0ne/secops-demo).
Fiecare răspunde unui risc din [`RISK-REGISTER.md`](RISK-REGISTER.md).

| Ce | Unde |
|----|------|
| Scanare de secrete (gitleaks) la commit și în CI | `.pre-commit-config.yaml`, `.github/workflows/ci.yml` |
| Subresource Integrity pe scripturile de pe CDN | `site/app.html`, `scripts/check_sri.py` |
| Configurație nginx cu CSP pe pagină, HSTS, fără versiune expusă | `deploy/nginx/` |
| Monitorizare săptămânală a headerelor live | `.github/workflows/site-monitor.yml` |
| Doar pull request-uri pe `main` | `.github/workflows/governance.yml` |
| Acțiuni GitHub fixate pe SHA, actualizate de Dependabot | `.github/` |
| Protecția fișierelor secrete pentru Claude Code | `.claude/` |
| Raportarea vulnerabilităților | `SECURITY.md`, `site/.well-known/security.txt` |

Pentru lucru local: `pip install pre-commit && pre-commit install`.

## Istoric

Versiunile anterioare (Dad Joke Generator) rămân în istoricul git.
