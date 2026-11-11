# Deploy nginx pentru www.andreiul.com

Configurația din acest folder închide R-04 (versiunea expusă) și R-05 (headere de securitate).
Serverul rulează acum nginx 1.18 pe Ubuntu 20.04 și nu trimite niciun header de securitate.

## Înainte de deploy

Compară cu configurația actuală de pe server și ajustează dacă diferă:

```bash
sudo nginx -T | less                  # configurația activă completă
ls /etc/letsencrypt/live/             # numele certificatului
```

Configurația presupune:
- fișierele site-ului în `/var/www/andreiul.com` (conținutul folderului `site/`);
- certificatul certbot în `/etc/letsencrypt/live/andreiul.com/`;
- `www.andreiul.com` ca adresă canonică (`andreiul.com` face redirect).

## Instalare

```bash
sudo cp snippets/security-headers.conf /etc/nginx/snippets/
sudo cp /etc/nginx/sites-available/andreiul.com /etc/nginx/sites-available/andreiul.com.bak   # backup
sudo cp andreiul.com.conf /etc/nginx/sites-available/andreiul.com
sudo nginx -t && sudo systemctl reload nginx
```

Dacă `nginx -t` dă eroare, nu reîncărca: repune backup-ul și trimite-mi mesajul.

Copiază și `site/.well-known/security.txt` în `/var/www/andreiul.com/.well-known/`.

## Verificare

```bash
bash scripts/check-live-headers.sh https://www.andreiul.com
```

Sau din GitHub: Actions → site-monitor → Run workflow.

Deschide apoi fiecare pagină în browser cu DevTools → Console deschis. Un mesaj
„Refused to load …” înseamnă că CSP-ul blochează ceva de care pagina are nevoie.

## HSTS

`max-age` e setat la un an. După ce site-ul merge fără probleme câteva săptămâni pe HTTPS,
poți adăuga `; preload` și înscrie domeniul pe hstspreload.org. Înscrierea e greu de anulat,
așa că nu te grăbi.

## Upgrade Ubuntu 20.04 → 24.04

Ubuntu 20.04 nu mai primește actualizări standard. Pașii, după un backup sau snapshot:

```bash
sudo apt update && sudo apt full-upgrade
sudo do-release-upgrade          # 20.04 → 22.04, apoi rulează din nou pentru 24.04
```

Configurația folosește `listen 443 ssl http2`, care merge pe nginx 1.18 și 1.24.
