from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class RouteNotFound(LookupError):
    """Raised when no route matches an HTTP method and path."""


RouteHandler = Callable[[Any], Any]


@dataclass(frozen=True)
class _Route:
    method: str
    path: str
    handler: RouteHandler
    prefix: bool


class Router:
    """Small method/path router for the stdlib HTTP backend."""

    def __init__(self) -> None:
        self._routes: list[_Route] = []

    def add(
        self,
        method: str,
        path: str,
        handler: RouteHandler,
        *,
        prefix: bool = False,
    ) -> None:
        self._routes.append(_Route(method.upper(), path, handler, prefix))

    def resolve(self, method: str, path: str) -> RouteHandler:
        wanted = method.upper()
        for route in self._routes:
            if route.method != wanted:
                continue
            if route.prefix and path.startswith(route.path):
                return route.handler
            if not route.prefix and path == route.path:
                return route.handler
        raise RouteNotFound(f"no route for {wanted} {path}")
