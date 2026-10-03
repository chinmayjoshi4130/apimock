"""Tests for HTTP server and routing."""

import pytest
import asyncio
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from apimock.parser.openapi import parse_file
from apimock.mock.generator import create_generator
from apimock.server.app import create_server
from apimock.server.routes import Router, RouteMatch
from apimock.parser.models import HttpMethod, Route, Parameter, ParameterLocation


class TestRouter:
    """Tests for request routing."""

    @pytest.fixture
    def routes(self):
        api = parse_file("openapi.yaml")
        return api.routes

    @pytest.fixture
    def router(self, routes):
        return Router(routes)

    def test_match_get_users(self, router):
        """Match GET /users."""
        match = router.match("GET", "/users", "")
        assert match is not None
        assert match.route.path == "/users"
        assert match.route.method == HttpMethod.GET
        assert match.path_params == {}
        assert match.query_params == {}

    def test_match_get_users_with_id(self, router):
        """Match GET /users/{id}."""
        match = router.match("GET", "/users/42", "")
        assert match is not None
        assert match.route.path == "/users/{id}"
        assert match.path_params == {"id": "42"}

    def test_match_post_users(self, router):
        """Match POST /users."""
        match = router.match("POST", "/users", "")
        assert match is not None
        assert match.route.method == HttpMethod.POST

    def test_match_patch_users(self, router):
        """Match PATCH /users/{id}."""
        match = router.match("PATCH", "/users/123", "")
        assert match is not None
        assert match.route.method == HttpMethod.PATCH
        assert match.path_params == {"id": "123"}

    def test_match_delete_users(self, router):
        """Match DELETE /users/{id}."""
        match = router.match("DELETE", "/users/999", "")
        assert match is not None
        assert match.route.method == HttpMethod.DELETE
        assert match.path_params == {"id": "999"}

    def test_match_with_query_params(self, router):
        """Match with query string."""
        match = router.match("GET", "/users", "limit=10&offset=0")
        assert match is not None
        assert match.query_params == {"limit": ["10"], "offset": ["0"]}

    def test_no_match_unknown_path(self, router):
        """No match for unknown path."""
        match = router.match("GET", "/unknown", "")
        assert match is None

    def test_no_match_wrong_method(self, router):
        """No match for wrong HTTP method."""
        match = router.match("PUT", "/users", "")
        assert match is None

    def test_case_insensitive_method(self, router):
        """Method matching is case-insensitive."""
        match = router.match("get", "/users", "")
        assert match is not None
        assert match.route.method == HttpMethod.GET

    def test_get_all_routes(self, router):
        """Get all registered routes."""
        all_routes = router.get_all_routes()
        assert len(all_routes) == 5


class TestServerIntegration:
    """Integration tests for the HTTP server."""

    @pytest.fixture
    def server(self):
        api = parse_file("openapi.yaml")
        generator = create_generator(api, seed=42)
        server = create_server(api, generator, host="127.0.0.1", port=0, quiet=True)
        return server

    @pytest.mark.asyncio
    async def test_get_users(self, server):
        """Test GET /users endpoint."""
        # We can't easily test the full server in this setup
        # This is a placeholder for integration tests
        pass

    def test_server_creation(self, server):
        """Test server can be created."""
        assert server.host == "127.0.0.1"
        assert server.port == 0  # Will be assigned
        assert server.delay == 0
        assert server.quiet is True


class TestRouteModels:
    """Tests for route model handling."""

    def test_route_creation(self):
        """Create route with all components."""
        route = Route(
            path="/test/{id}",
            method=HttpMethod.GET,
            parameters=[
                Parameter(name="id", location=ParameterLocation.PATH, required=True, schema={"type": "integer"}),
                Parameter(name="filter", location=ParameterLocation.QUERY, schema={"type": "string"}),
            ],
            request_body=None,
            responses=[],
            summary="Test route",
        )
        assert route.path == "/test/{id}"
        assert route.method == HttpMethod.GET
        assert len(route.parameters) == 2
        assert route.parameters[0].name == "id"
        assert route.parameters[1].name == "filter"


class TestServerRoutes:
    """Tests for server route handling."""

    def test_compile_path_pattern(self):
        """Test path pattern compilation."""
        from apimock.server.routes import Router

        router = Router([])
        # Test simple path
        pattern = router._compile_path_pattern("/users")
        assert pattern.match("/users")
        assert not pattern.match("/users/")

        # Test path with parameter
        pattern = router._compile_path_pattern("/users/{id}")
        match = pattern.match("/users/42")
        assert match
        assert match.group("id") == "42"

        # Test multiple parameters
        pattern = router._compile_path_pattern("/users/{id}/posts/{postId}")
        match = pattern.match("/users/123/posts/456")
        assert match
        assert match.group("id") == "123"
        assert match.group("postId") == "456"

    def test_parse_query_string(self):
        """Test query string parsing."""
        from apimock.server.routes import Router

        router = Router([])
        params = router._parse_query("a=1&b=2&b=3")
        assert params == {"a": ["1"], "b": ["2", "3"]}

        params = router._parse_query("")
        assert params == {}

        params = router._parse_query("key=")
        assert params == {"key": [""]}

        params = router._parse_query("novalue")
        assert params == {"novalue": [""]}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])