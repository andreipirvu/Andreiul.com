# Module 4A project stack (Lab 3). Run from the repository root in WSL2 or Linux.
# Ports come from .env; the admin password from secrets/opensearch.enc.yaml (R-02).
.PHONY: env secrets up down health template replay hits intel exposure cert chain test lint

# .env holds ports and image digests. Create it from the example, and add any key that a
# later lab introduced to .env.example (existing values are never overwritten).
env:
	@[ -f .env ] || { cp .env.example .env && echo "created .env from .env.example"; }
	@grep -E '^[A-Z_]+=' .env.example | while IFS='=' read -r k v; do \
	  grep -q "^$$k=" .env || { echo "$$k=$$v" >> .env && echo "added $$k to .env"; }; done

# Decrypt every SOPS secret for compose; owner-only, deleted by make down (R-02).
# Lab 6 adds secrets/intel.enc.yaml (MISP and Shodan keys) next to the admin password.
secrets:
	umask 077 && for f in secrets/*.enc.yaml; do sops -d "$$f"; done | sed 's/: /=/' > .env.secrets

up: env secrets
	@[ -f certs/frontdoor.crt ] && [ -f certs/frontdoor.key ] || \
	  { echo "certs/frontdoor.* missing: start step-ca and run 'make cert' (Lab 3 Part C)"; exit 1; }
	mkdir -p data enrich
	@# Logstash refuses to start without its dictionary; an empty one is valid (Lab 6).
	@[ -f enrich/ioc_ip.yml ] || echo '{}' > enrich/ioc_ip.yml
	docker compose --env-file .env --env-file .env.secrets up -d
	@$(MAKE) -s template

# Stopping needs no secret; the placeholder only satisfies compose's ${...:?} check.
down:
	OPENSEARCH_INITIAL_ADMIN_PASSWORD=unused docker compose --env-file .env down -v && rm -f .env.secrets

# Cluster health. The password goes to curl on stdin, never on the command line.
health:
	@set -a; . ./.env; . ./.env.secrets; set +a; \
	printf 'user = "admin:%s"\n' "$$OPENSEARCH_INITIAL_ADMIN_PASSWORD" | \
	curl -sk -K- "https://localhost:$$OPENSEARCH_PORT/_cluster/health?pretty"

# Index template before the first suricata-* index exists (Lab 5 Part E). Retries
# while OpenSearch finishes starting; the password goes to curl on stdin.
template:
	@set -a; . ./.env; . ./.env.secrets; set +a; \
	for i in $$(seq 1 30); do \
	  out=$$(printf 'user = "admin:%s"\n' "$$OPENSEARCH_INITIAL_ADMIN_PASSWORD" | \
	    curl -sk -K- -X PUT "https://localhost:$$OPENSEARCH_PORT/_index_template/suricata" \
	    -H 'Content-Type: application/json' --data @config/opensearch/suricata-template.json); \
	  echo "$$out" | grep -q '"acknowledged":true' && { echo "template: $$out"; exit 0; }; sleep 5; \
	done; echo "template not applied: $$out"; exit 1

# Feed the Lab 5 samples to Logstash (picked up within about 15 seconds).
replay:
	mkdir -p data
	cp tests/samples/eve_dns_txt_positive.json tests/samples/eve_dns_txt_negative.json data/

# Count the hits of a converted rule: make hits RULE=dns_long_txt
RULE ?= dns_long_txt
hits:
	@set -a; . ./.env; . ./.env.secrets; set +a; \
	printf 'user = "admin:%s"\n' "$$OPENSEARCH_INITIAL_ADMIN_PASSWORD" | \
	curl -sk -K- "https://localhost:$$OPENSEARCH_PORT/suricata-*/_search?filter_path=hits.total.value,hits.hits._source.dns.question.name" \
	  -H 'Content-Type: application/json' --data @detections/opensearch/$(RULE).json; echo

# Lab 6: pull MISP indicators into enrich/ioc_ip.yml (never committed, R-04).
intel:
	@set -a; . ./.env.secrets; set +a; python3 scripts/misp_pull.py

# Lab 6: one Shodan snapshot of my own authorised IP into exposure/ (never committed, R-05).
exposure:
	@set -a; . ./.env.secrets; set +a; python3 scripts/exposure_check.py

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
