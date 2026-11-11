## Rol
Asistent de inginerie pentru site-ul static www.andreiul.com.

## Convenții
- Site-ul e static: HTML, CSS și JavaScript în `site/`, fără build. Nu adăuga framework-uri sau dependențe.
- Configurația serverului e în `deploy/nginx/`. Rulează `bash deploy/nginx/test-config.sh` după orice modificare.
- Orice script sau stylesheet extern primește `integrity` și `crossorigin` (R-03). Verifică cu `python scripts/check_sri.py site/*.html`.
- Pe `site/index.html` nu se adaugă script inline și nici handlere `onclick`: CSP-ul îl interzice. Codul merge în `site/main.js`.
- O pagină nouă primește propriul bloc `location` cu CSP în `deploy/nginx/andreiul.com.conf`.
- Nu scrie niciodată secrete în repo (R-02).
- Lucrul se face pe branch și ajunge pe `main` doar prin pull request (R-01).

## Registrul de riscuri
Fiecare modificare menționează ID-urile de risc pe care le tratează (`RISK-REGISTER.md`).
