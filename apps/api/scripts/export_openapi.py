"""Print the OpenAPI schema of the app to stdout (used by `just contract`).

Never reads apps/api/.env and never connects to a database.
"""

import json

from app.core.config import Settings
from app.main import create_app


def render_openapi() -> str:
    settings = Settings(environment="test", _env_file=None)
    spec = create_app(settings).openapi()
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    print(render_openapi(), end="")
