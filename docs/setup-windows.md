# Running the project stack on Windows

The labs are written for macOS and Linux. On Windows everything runs inside WSL2 (Ubuntu),
with Docker Desktop providing the engine. Do this once.

## 1. WSL2 and Docker Desktop

In PowerShell as administrator:

```powershell
wsl --install -d Ubuntu-24.04
```

Install Docker Desktop, then in its Settings:
- General: "Use the WSL 2 based engine" on.
- Resources → WSL integration: enable Ubuntu-24.04.
- Resources → Advanced: give it at least 8 GB of memory (Lab 6 adds MISP: 12 GB or more).

OpenSearch needs a larger memory-map limit inside Docker's VM. In PowerShell:

```powershell
wsl -d docker-desktop sysctl -w vm.max_map_count=262144
```

This resets when Docker Desktop restarts; run it again if OpenSearch exits with
`max virtual memory areas vm.max_map_count [65530] is too low`.

## 2. Tools inside Ubuntu (WSL)

Open the Ubuntu terminal and work from your Linux home, not from `/mnt/c` (much faster,
and file permissions such as `chmod 600` work there):

```bash
sudo apt update && sudo apt install -y make git age python3-venv python3-pip curl jq

# sops 3.9+ (release package from GitHub)
SOPS=3.10.2
curl -LO "https://github.com/getsops/sops/releases/download/v${SOPS}/sops_${SOPS}_amd64.deb"
sudo apt install -y "./sops_${SOPS}_amd64.deb" && rm "sops_${SOPS}_amd64.deb"

# step CLI and step-ca (smallstep)
curl -LO https://dl.smallstep.com/cli/docs-ca-install/latest/step-cli_amd64.deb
curl -LO https://dl.smallstep.com/certificates/docs-ca-install/latest/step-ca_amd64.deb
sudo apt install -y ./step-cli_amd64.deb ./step-ca_amd64.deb && rm ./step-*_amd64.deb

sops --version && age --version && step version && docker compose version
```

## 3. The repository

```bash
cd ~ && git clone https://github.com/andreipirvu/Andreiul.com.git && cd Andreiul.com
git config core.autocrlf input
```

## 4. Lab 3 on your machine

The repository already holds the stack. These steps are the ones that must be yours:

```bash
git switch lab3/iaas

# Your age key, .sops.yaml and the encrypted admin password (R-02)
bash scripts/init-secrets.sh
git add .sops.yaml secrets/opensearch.enc.yaml
git commit -m "feat: admin secret encrypted to my age key (R-02)"
git show HEAD:secrets/opensearch.enc.yaml | head      # evidence: only ENC[...]

# The lab CA (keep it running in a second terminal)
step ca init --name "Lab Root" --dns localhost --address :8443 \
  --provisioner admin --deployment-type standalone
step-ca "$(step path)/config/ca.json"               # second terminal

# Back in the first terminal
make cert
make up
make health          # repeat until "status" is green or yellow
make down && make up
make health          # second run: same state, no manual fixes
make chain           # frontdoor.lab -> Intermediate CA -> Root CA
```

Trust the lab root in Windows so the browser accepts `https://localhost`: copy
`$(step path)/certs/root_ca.crt` to Windows (for example to `C:\Users\<you>\Downloads`),
double-click it, choose Install Certificate → Current User → "Trusted Root Certification
Authorities". Remove it at the end of the course the same way (certmgr.msc).

## 5. Evidence for Lab 3 (`docs/evidence/lab3/`)

- `health-run1.txt` and `health-run2.txt`: the output of `make health` before and after
  `make down && make up`.
- `ciphertext.txt`: `git show HEAD:secrets/opensearch.enc.yaml | head`.
- `chain.txt` (`make chain`) and a browser screenshot of the certificate chain.

Never put `.env.secrets`, `certs/` or `keys.txt` in git; `.gitignore` already blocks them.
