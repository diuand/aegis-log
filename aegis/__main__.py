"""`make run` entry point: python -m aegis"""

from aegis import create_app
from aegis.config import load_settings


def main() -> None:
    settings = load_settings()
    app = create_app(settings)
    app.run(host=settings.host, port=settings.port, debug=True)


if __name__ == "__main__":
    main()
