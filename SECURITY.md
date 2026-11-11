# Politica de securitate

## Raportarea unei vulnerabilități

Raportează în privat, nu prin issue public:

- prin [GitHub Security Advisories](https://github.com/andreipirvu/Andreiul.com/security/advisories/new), sau
- pe email, la adresa din [`security.txt`](https://www.andreiul.com/.well-known/security.txt).

Răspund de obicei în câteva zile. Te rog să nu faci public problema până nu e rezolvată.

## Reguli pentru repository

- Secretele nu se comit niciodată, nici măcar temporar (R-02). gitleaks le blochează la
  commit și în CI. Un secret ajuns în istoric se consideră compromis și se revocă, nu doar se șterge.
- Orice modificare ajunge pe `main` doar prin pull request cu CI trecut (R-01).
- Scripturile externe se încarcă doar cu Subresource Integrity (R-03).
- Acțiunile GitHub sunt fixate pe SHA complet (R-07).

## Configurare GitHub (o singură dată)

Settings → Rules → Rulesets → New branch ruleset:
- Target: branch-ul `main`
- Bifează: Restrict deletions, Block force pushes, Require a pull request before merging,
  Require status checks to pass (`secret scan`, `site checks`, `nginx config test`, `workflow lint`)

Settings → Code security: activează Private vulnerability reporting, Secret scanning
și Push protection (gratuite pentru repository-uri publice).
