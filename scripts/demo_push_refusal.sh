#!/usr/bin/env bash
# Evidence: the pre-push guard refuses a direct push to main and a force push.
# Runs entirely in a temporary directory against a local bare "remote".
set -uo pipefail

HOOK="$(cd "$(dirname "$0")" && pwd)/hooks/protect_main_push.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git init -q --bare -b main "$WORK/remote.git"
git clone -q "$WORK/remote.git" "$WORK/clone" 2>/dev/null
cd "$WORK/clone"
git config core.autocrlf false
git config user.email demo@example.invalid
git config user.name demo
echo seed > seed.txt && git add seed.txt && git commit -q -m "chore: seed"
git push -q origin HEAD:main --no-verify   # the root commit exception
cp "$HOOK" .git/hooks/pre-push && chmod +x .git/hooks/pre-push

run() {
  echo "\$ $*"
  "$@" 2>&1 | sed 's/^/  /'
  echo "  exit code: ${PIPESTATUS[0]}"
  echo
}

echo "# Direct push to main"
echo change >> seed.txt && git commit -qam "feat: straight to main"
run git push origin HEAD:main

echo "# Push of a feature branch (allowed)"
git checkout -q -b feature/demo
run git push origin feature/demo

echo "# Force push that rewrites the feature branch"
git commit -q --amend -m "feat: rewritten history"
run git push --force origin feature/demo

echo "# Deleting main"
run git push origin :main
