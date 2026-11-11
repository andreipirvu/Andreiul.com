# Deploy nginx pentru www.andreiul.com

Serverul (Contabo, Ubuntu 22.04, nginx 1.18) găzduiește trei site-uri:

| Site | Fișier pe server | Atins de acest folder? |
|------|------------------|------------------------|
| `andreiul.com`, `www.andreiul.com` | `/etc/nginx/sites-available/andreiul` (primul bloc) | Da: headere de securitate și CSP |
| `jobs.andreiul.com` (NexusJobs) | același fișier, al doilea bloc | Nu: copiat neschimbat |
| `birds.andreiul.com` | `/etc/nginx/sites-available/birds` | Nu |

| Fișier din repo | Unde merge pe server | Ce face |
|-----------------|---------------------|---------|
| `conf.d/security.conf` | `/etc/nginx/conf.d/security.conf` | `server_tokens off` pentru toate site-urile (R-04). E deja instalat. |
| `snippets/security-headers.conf` | `/etc/nginx/snippets/security-headers.conf` | HSTS, nosniff, X-Frame-Options etc. (R-05) |
| `sites-available/andreiul` | `/etc/nginx/sites-available/andreiul` | Fișierul complet, cu CSP pe pagină și blocarea `/nexusjobs/` (R-05, R-08) |

## Testare înainte de deploy

`bash deploy/nginx/test-config.sh` reproduce structura de pe server (inclusiv site-ul birds)
și rulează `nginx -t`. CI-ul îl rulează la fiecare pull request.

## Instalare (pe server, ca root)

Din folderul repo-ului clonat pe server, sau după ce copiezi cele două fișiere cu `scp`:

```bash
# 1. backup
cp /etc/nginx/sites-available/andreiul /root/andreiul.nginx.$(date +%F-%H%M).bak

# 2. verifică dacă fișierul de pe server s-a schimbat față de ce e în repo (afară de
#    blocul andreiul.com). Diferențele așteptate sunt doar în primul bloc server.
diff /etc/nginx/sites-available/andreiul deploy/nginx/sites-available/andreiul

# 3. instalare și test
cp deploy/nginx/snippets/security-headers.conf /etc/nginx/snippets/
cp deploy/nginx/sites-available/andreiul /etc/nginx/sites-available/andreiul
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

## Certbot

Liniile marcate `# managed by Certbot` sunt identice cu cele de pe server. Reînnoirea
automată (`certbot renew`) nu rescrie fișierul, deci modificările rămân.
Dacă rulezi din nou `certbot --nginx` pentru un domeniu nou, verifică după aceea cu `diff`.

## HSTS

`max-age` e de un an, fără `includeSubDomains`, ca să nu impună HTTPS pe subdomenii
viitoare. După câteva săptămâni fără probleme poți adăuga `includeSubDomains`.
