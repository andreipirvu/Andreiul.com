# Module 4A project stack (Lab 3). Run from the repository root in WSL2 or Linux.
# Ports come from .env; the admin password from secrets/opensearch.enc.yaml (R-02).
.PHONY: env secrets up down health cert chain test lint

# .env holds only ports (and later image digests); create it from the example once.
env:
	@[ -f .env ] || { cp .env.example .env && echo "created .env from .env.example"; }

# Decrypt the SOPS secret for compose; owner-only, deleted by make down (R-02).
secrets:
	umask 077 && sops -d secrets/opensearch.enc.yaml | sed 's/: /=/' > .env.secrets

up: env secrets
	@[ -f certs/frontdoor.crt ] && [ -f certs/frontdoor.key ] || \
	  { echo "certs/frontdoor.* missing: start step-ca and run 'make cert' (Lab 3 Part C)"; exit 1; }
	docker compose --env-file .env --env-file .env.secrets up -d

# Stopping needs no secret; the placeholder only satisfies compose's ${...:?} check.
down:
	OPENSEARCH_INITIAL_ADMIN_PASSWORD=unused docker compose --env-file .env down -v && rm -f .env.secrets

# Cluster health. The password goes to curl on stdin, never on the command line.
health:
	@set -a; . ./.env; . ./.env.secrets; set +a; \
	printf 'user = "admin:%s"\n' "$$OPENSEARCH_INITIAL_ADMIN_PASSWORD" | \
	curl -sk -K- "https://localhost:$$OPENSEARCH_PORT/_cluster/health?pretty"

# Front door certificate from the lab CA (step-ca must be running, Lab 3 Part C).
cert:
	mkdir -p certs
	step ca certificate frontdoor.lab certs/frontdoor.crt certs/frontdoor.key \
	  --san frontdoor.lab --san localhost \
	  --ca-url https://localhost:8443 --root "$$(step path)/certs/root_ca.crt" --force

# Show the chain the front door serves: frontdoor.lab -> Intermediate CA -> Root CA.
chain:
	@set -a; . ./.env; set +a; \
	openssl s_client -connect "localhost:$$HTTPS_PORT" -servername localhost -showcerts </dev/null 2>/dev/null | grep -E "^ *[0-9] s:|^ *i:"

# Pipeline tests read LOGSTASH_IMAGE from .env and skip without it (R-03).
test:
	set -a; [ ! -f .env ] || . ./.env; set +a; python3 -m pytest -q tests/

lint:
	pre-commit run --all-files
