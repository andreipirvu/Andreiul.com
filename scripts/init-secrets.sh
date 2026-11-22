#!/usr/bin/env bash
# Lab 3 Part B step 3, on my own machine: bind secrets/ to MY age key and encrypt the
# OpenSearch admin password (R-02). Only ciphertext ever reaches git; the private key
# stays in ~/.config/sops/age/keys.txt.
#
#   bash scripts/init-secrets.sh     (from the repository root)
set -euo pipefail

KEYS="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
OUT=secrets/opensearch.enc.yaml

command -v sops >/dev/null || { echo "sops is missing (needs 3.9+)"; exit 1; }
command -v age-keygen >/dev/null || { echo "age is missing"; exit 1; }

# 1. Your age key: create it once, never commit it.
if [ ! -f "$KEYS" ]; then
  mkdir -p "$(dirname "$KEYS")"
  age-keygen -o "$KEYS"
  chmod 600 "$KEYS"
  echo "Created $KEYS. Back it up: without it you cannot decrypt your own secrets."
fi
PUB="$(grep -o 'age1[0-9a-z]*' "$KEYS" | head -1)"

# 2. .sops.yaml: everything matching secrets/*.enc.yaml is encrypted to your key.
cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: secrets/.*\.enc\.yaml$
    age: $PUB
EOF
echo ".sops.yaml now encrypts to $PUB"

# 3. The admin password, read without echo and never written in plaintext.
if [ -f "$OUT" ] && [ "${1:-}" != "--force" ]; then
  echo "$OUT already exists; rerun with --force to replace it."
  exit 0
fi
echo "OpenSearch admin password: 12+ characters, upper and lower case, a digit and one"
echo "of ! @ % ^ * - _ + = . Avoid \$, #, quotes, spaces, colons and the word 'admin'."
mkdir -p secrets
read -rsp 'Admin password: ' OS_PW; echo
read -rsp 'Repeat:         ' OS_PW2; echo
[ "$OS_PW" = "$OS_PW2" ] || { unset OS_PW OS_PW2; echo "Passwords differ."; exit 1; }
[ "${#OS_PW}" -ge 12 ] || { unset OS_PW OS_PW2; echo "Too short."; exit 1; }
# OpenSearch refuses a password that resembles the user name and then quits at start-up.
case "$(printf '%s' "$OS_PW" | tr '[:upper:]' '[:lower:]')" in
  *admin*) unset OS_PW OS_PW2; echo "OpenSearch rejects passwords containing 'admin'. Choose another."; exit 1 ;;
esac
TMP="$(mktemp secrets/.enc.XXXXXX)"
printf 'OPENSEARCH_INITIAL_ADMIN_PASSWORD: %s\n' "$OS_PW" \
  | sops --encrypt --filename-override "$OUT" --input-type yaml --output-type yaml /dev/stdin > "$TMP"
unset OS_PW OS_PW2
mv "$TMP" "$OUT"   # only a complete ciphertext ever replaces the file
echo "Wrote $OUT. Check: git diff shows only ENC[...] values."
