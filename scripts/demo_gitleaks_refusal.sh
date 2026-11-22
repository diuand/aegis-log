#!/usr/bin/env bash
# Evidence and CI self-test: gitleaks refuses a commit that carries a key.
# A fresh fake key in the aegk_ format is generated each run, so the test
# cannot pass by matching a stored value. Exit 0 means "the key was refused".
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

FAKE="aegk_$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)"
git init -q "$WORK/repo"
cd "$WORK/repo"
git config core.autocrlf false
git config user.email demo@example.invalid
git config user.name demo
cp "$ROOT/.gitleaks.toml" .
printf 'INTEL_API_KEY = "%s"\n' "$FAKE" > settings.py
git add settings.py .gitleaks.toml

echo "\$ git add settings.py   # contains a freshly generated fake aegk_ key"
echo "\$ gitleaks git --pre-commit --staged --redact --config .gitleaks.toml"
gitleaks git --pre-commit --staged --redact --no-banner --no-color --verbose --config .gitleaks.toml 2>&1 \
  | grep -E "RuleID|File:|leaks found|Secret:" | sed 's/^/  /'
code=${PIPESTATUS[0]}
echo "  exit code: $code"
if [[ "$code" -eq 1 ]]; then
  echo "RESULT: commit refused, the key never enters history"
  exit 0
fi
echo "RESULT: NOT refused, gitleaks did not catch the key" >&2
exit 1
