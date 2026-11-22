"""`make run` entry point: python -m aegis"""

import sys

from aegis import create_app
from aegis.config import load_settings

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def main() -> int:
    settings = load_settings()
    if not settings.api_key:
        print("AEGIS_API_KEY is not set. Run `make setup` (it writes a random key to .env).",
              file=sys.stderr)
        return 1
    if settings.host not in LOOPBACK:
        print("aegis-log only binds to the loopback interface.", file=sys.stderr)
        return 1
    app = create_app(settings)
    # The Werkzeug debugger executes code typed into its console: never on.
    app.run(host=settings.host, port=settings.port, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
