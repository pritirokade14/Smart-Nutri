"""Route introspection for tests (FastAPI >= 0.16x nests included routers)."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import iter_route_contexts


@dataclass(frozen=True)
class ApiRoute:
    path: str
    methods: frozenset[str]
    dependant: Dependant

    def calls(self) -> set[Callable[..., Any]]:
        """Every dependency callable, including nested sub-dependencies."""
        found: set[Callable[..., Any]] = set()
        stack = list(self.dependant.dependencies)
        while stack:
            dep = stack.pop()
            if dep.call is not None:
                found.add(dep.call)
            stack.extend(dep.dependencies)
        return found

    def top_level_calls(self) -> list[Callable[..., Any]]:
        return [d.call for d in self.dependant.dependencies if d.call is not None]


def api_routes(app: FastAPI) -> Iterator[ApiRoute]:
    for rc in iter_route_contexts(app.routes):
        dependant = getattr(rc, "dependant", None)
        if dependant is None:
            continue
        yield ApiRoute(rc.path, frozenset(rc.methods or ()), dependant)
