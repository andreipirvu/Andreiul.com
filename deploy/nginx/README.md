# Deploy nginx pentru www.andreiul.com

Serverul (Contabo, Ubuntu 22.04, nginx 1.18) găzduiește trei site-uri:

| Site | Fișier pe server | Atins de acest folder? |
|------|------------------|------------------------|
| `andreiul.com`, `www.andreiul.com` | `/etc/nginx/sites-available/andreiul` (primul bloc) | Da: headere de securitate și CSP |
| `jobs.andreiul.com` | același fișier, blocurile de după andreiul.com | Nu: nu e gestionat în acest repo |
| `birds.andreiul.com` | `/etc/nginx/sites-available/birds` | Nu |

| Fișier din repo | Unde merge pe server | Ce face |
|-----------------|---------------------|---------|
| `conf.d/security.conf` | `/etc/nginx/conf.d/security.conf` | `server_tokens off` pentru toate site-urile (R-05). E deja instalat. |
| `snippets/security-headers.conf` | `/etc/nginx/snippets/security-headers.conf` | HSTS, nosniff, X-Frame-Options etc. (R-11) |
| `sites-available/andreiul` | blocurile andreiul.com din `/etc/nginx/sites-available/andreiul` | CSP pe pagină și blocarea `/nexusjobs/` (R-11, R-13) |

## Testare înainte de deploy

`bash deploy/nginx/test-config.sh` reproduce structura de pe server (inclusiv site-ul birds)
și rulează `nginx -t`. CI-ul îl rulează la fiecare pull request.

## Instalare (pe server, ca root)

**Nu copia `sites-available/andreiul` peste fișierul de pe server.** Pe server, fișierul
conține și blocurile `jobs.andreiul.com`, care nu sunt în acest repo; o copiere completă
ar opri site-ul jobs. Până când blocurile jobs sunt mutate într-un fișier separat pe
server, se actualizează doar blocurile andreiul.com, de mână.

Din folderul repo-ului clonat pe server, sau după ce copiezi fișierele cu `scp`:

```bash
# 1. backup
cp /etc/nginx/sites-available/andreiul /root/andreiul.nginx.$(date +%F-%H%M).bak

# 2. vezi ce diferă. Liniile jobs.andreiul.com apar ca lipsă din repo: e normal,
#    rămân pe server neschimbate.
diff /etc/nginx/sites-available/andreiul deploy/nginx/sites-available/andreiul

# 3. snippet-ul se poate copia întreg; în fișierul site-ului editezi doar
#    blocurile andreiul.com, apoi testezi
cp deploy/nginx/snippets/security-headers.conf /etc/nginx/snippets/
nano /etc/nginx/sites-available/andreiul
nginx -t && systemctl reload nginx
```

Dacă `nginx -t` dă eroare, nu reîncărca. Pune backup-ul înapoi:
`cp /root/andreiul.nginx.<data>.bak /etc/nginx/sites-available/andreiul`.

Copiază și `site/.well-known/security.txt` în `/var/www/andreiul.com/.well-known/`.

## Verificare

```bash
for u in https://www.andreiul.com/ https://andreiul.com/ https://jobs.andreiul.com/ https://birds.andreiul.com/; do
  curl -s -o /dev/null -w "%{http_code}  $u\n" "$u"; done
bash scripts/check-live-headers.sh https://www.andreiul.com
```

Sau din GitHub: Actions → site-monitor → Run workflow.

Deschide apoi fiecare pagină în browser cu DevTools → Console deschis. Un mesaj
„Refused to load …” înseamnă că CSP-ul blochează ceva de care pagina are nevoie.

## Actualizarea fișierelor site-ului

`<server>` e adresa VPS-ului. Ține-o într-un alias din `~/.ssh/config`, nu în repo.

```bash
scp site/index.html site/main.js site/styles.css root@<server>:/tmp/   # din Git Bash
# pe server:
mkdir -p /root/site-backup && cp /var/www/andreiul.com/{index.html,main.js,styles.css} /root/site-backup/
cp /tmp/index.html /tmp/main.js /tmp/styles.css /var/www/andreiul.com/
```

Când se schimbă `main.js` sau `styles.css`, crește numărul din `index.html` (`main.js?v=2`), ca
browserele vizitatorilor să nu folosească o copie veche din cache.

## Certbot

Liniile marcate `# managed by Certbot` sunt identice cu cele de pe server. Reînnoirea
automată (`certbot renew`) nu rescrie fișierul, deci modificările rămân.
Dacă rulezi din nou `certbot --nginx` pentru un domeniu nou, verifică după aceea cu `diff`.

## HSTS

`max-age` e de un an, fără `includeSubDomains`, ca să nu impună HTTPS pe subdomenii
viitoare. După câteva săptămâni fără probleme poți adăuga `includeSubDomains`.
