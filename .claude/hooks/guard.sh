#!/usr/bin/env bash
# Picks a Python 3 interpreter and runs guard.py. Fails closed (exit 2) if
# none is available, so a missing interpreter never disables the guard.
DIR="$(cd "$(dirname "$0")" && pwd)"
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    exec "$py" "$DIR/guard.py"
  fi
done
echo "aegis guard: no Python 3 found; blocking (failing closed)" >&2
exit 2
