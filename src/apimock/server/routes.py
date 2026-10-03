"""HTTP routing for ApiMock."""

import re
from dataclasses import dataclass
from typing import Any

from apimock.parser.models import Route, HttpMethod, ParameterLocation


@dataclass
class RouteMatch:
    route: Route
    path_params: dict[str, str]
    query_params: dict[str, list[str]]


class Router:
    """Routes HTTP requests to matching API routes."""

    def __init__(self, routes: list[Route]):
        self.routes = routes
        self._compiled_routes: list[tuple[re.Pattern, Route]] = []
        self._compile_routes()

    def _compile_routes(self) -> None:
        """Compile route patterns for matching."""
        for route in self.routes:
            pattern = self._compile_path_pattern(route.path)
            self._compiled_routes.append((pattern, route))

    def _compile_path_pattern(self, path: str) -> re.Pattern:
        """Convert OpenAPI path to regex pattern."""
        # Escape special regex chars except { }
        pattern = path
        # Replace {param} with named capture groups
        pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
        # Anchor the pattern
        pattern = f"^{pattern}$"
        return re.compile(pattern)

    def match(self, method: str, path: str, query_string: str = "") -> RouteMatch | None:
        """Match a request to a route."""
        http_method = HttpMethod(method.upper())

        # Parse query parameters
        query_params = self._parse_query(query_string)

        for pattern, route in self._compiled_routes:
            if route.method != http_method:
                continue

            match = pattern.match(path)
            if match:
                path_params = match.groupdict()
                return RouteMatch(
                    route=route,
                    path_params=path_params,
                    query_params=query_params,
                )

        return None

    def _parse_query(self, query_string: str) -> dict[str, list[str]]:
        """Parse query string into parameter dict."""
        params: dict[str, list[str]] = {}
        if not query_string:
            return params

        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
            else:
                key, value = pair, ""
            # URL decode (basic)
            key = key.replace("+", " ")
            value = value.replace("+", " ")
            params.setdefault(key, []).append(value)

        return params

    def get_all_routes(self) -> list[Route]:
        """Get all registered routes."""
        return self.routes