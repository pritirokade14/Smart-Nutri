"""Import every feature's `models` module, so all mapped tables are registered on `Base`.

The app factory imports the models indirectly through the routers. Standalone jobs
(`python -m app.jobs.*`) must call this first, or foreign keys between feature tables fail
to resolve at flush time (NoReferencedTableError).
"""

from __future__ import annotations

import importlib
import pkgutil

import app.features


def import_all_models() -> list[str]:
    """Import `app.features.<name>.models` for every feature that has one; return their names."""
    loaded: list[str] = []
    for info in pkgutil.iter_modules(app.features.__path__):
        if not info.ispkg:
            continue
        name = f"app.features.{info.name}.models"
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name != name:
                raise
            continue
        loaded.append(name)
    return loaded
