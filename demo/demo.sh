#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXTRA="${1:-}"
if [[ -z "${OPENAI_API_KEY:-}" && -f "$ROOT/.env" ]]; then
  set -a; . "$ROOT/.env"; set +a
fi
UNCONFLICT="${UNCONFLICT:-uv run --quiet --project $ROOT unconflict}"

say() { printf '\n\033[1;36m$ %s\033[0m\n' "$*"; }
run() { say "$*"; eval "$@"; }

DIR="$(mktemp -d -t unconflict-demo)"
cd "$DIR"
git init -q -b main
git config user.name demo
git config user.email demo@example.com

cat > shop.py <<'EOF'
import json


def price_with_tax(cents):
    return cents * 110 // 100


def describe(item):
    return item["name"]
EOF
git add shop.py && git commit -qm "base"

git checkout -qb feature
cat > shop.py <<'EOF'
import json
import logging


def price_with_tax(cents):
    return cents * 120 // 100


def describe(item):
    return item["name"]
EOF
git commit -qam "feature: logging, VAT is 20% now"

git checkout -q main
cat > shop.py <<'EOF'
import json
import math


def price_with_tax(cents):
    return math.ceil(cents * 1.10)


def describe(item):
    return item["name"].title()
EOF
git commit -qam "main: round tax up, nicer names"

say "# plain git first"
git merge -q feature >/dev/null 2>&1 || true
run "git diff --stat; grep -c '<<<<<<<' shop.py"
git merge --abort

say "# now with unconflict as the merge driver"
run "git config merge.unconflict.driver '$UNCONFLICT driver %O %A %B %P -s %S -x %X -y %Y $EXTRA'"
run "echo '*.py merge=unconflict' > .gitattributes"
run "git merge --no-edit feature || true"
run "cat shop.py"
run "$UNCONFLICT spend | head -2"
echo
echo "(demo repo: $DIR)"
