"""Tests for OpenAPI parser."""

import pytest
from apimock.parser.openapi import parse_file, parse_openapi, OpenApiParseError
from apimock.parser.models import HttpMethod, ParameterLocation


class TestOpenApiParser:
    """Tests for OpenAPI parsing."""

    def test_parse_valid_yaml(self):
        """Parse a valid OpenAPI YAML file."""
        api = parse_file("openapi.yaml")
        assert api.title == "Example API"
        assert api.version == "1.0.0"
        assert len(api.routes) == 5
        assert len(api.schemas) == 3

    def test_parse_valid_json(self):
        """Parse a valid OpenAPI JSON file."""
        import json
        import tempfile
        import os

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {"schema": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            fname = f.name
        try:
            api = parse_file(fname)
            assert api.title == "Test API"
            assert len(api.routes) == 1
        finally:
            os.unlink(fname)

    def test_parse_invalid_yaml(self):
        """Fail on invalid YAML."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: [")
            fname = f.name
        try:
            with pytest.raises(OpenApiParseError) as exc:
                parse_file(fname)
            assert "Failed to parse file" in str(exc.value)
        finally:
            os.unlink(fname)

    def test_parse_unsupported_version(self):
        """Fail on OpenAPI 2.x."""
        import tempfile
        import os

        spec = {
            "openapi": "2.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml
            yaml.dump(spec, f)
            fname = f.name
        try:
            with pytest.raises(OpenApiParseError) as exc:
                parse_file(fname)
            assert "Unsupported OpenAPI version" in str(exc.value)
        finally:
            os.unlink(fname)

    def test_parse_missing_file(self):
        """Fail on missing file."""
        with pytest.raises(OpenApiParseError) as exc:
            parse_file("nonexistent.yaml")
        assert "File not found" in str(exc.value)

    def test_route_discovery(self):
        """Discover all routes from spec."""
        api = parse_file("openapi.yaml")
        routes = {(r.method.value, r.path) for r in api.routes}
        expected = {
            ("GET", "/users"),
            ("POST", "/users"),
            ("GET", "/users/{id}"),
            ("PATCH", "/users/{id}"),
            ("DELETE", "/users/{id}"),
        }
        assert routes == expected

    def test_path_parameters(self):
        """Extract path parameters."""
        api = parse_file("openapi.yaml")
        route = next(r for r in api.routes if r.path == "/users/{id}" and r.method == HttpMethod.GET)
        params = {p.name: p for p in route.parameters}
        assert "id" in params
        assert params["id"].location == ParameterLocation.PATH
        assert params["id"].required is True
        assert params["id"].schema.get("type") == "integer"

    def test_query_parameters(self):
        """Handle query parameters."""
        import tempfile
        import yaml
        import os

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/search": {
                    "get": {
                        "parameters": [
                            {"name": "q", "in": "query", "schema": {"type": "string"}},
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}, "default": 10},
                        ],
                        "responses": {"200": {"content": {"application/json": {"schema": {"type": "array"}}}}},
                    }
                }
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(spec, f)
            fname = f.name
        try:
            api = parse_file(fname)
            route = api.routes[0]
            params = {p.name: p for p in route.parameters}
            assert "q" in params
            assert params["q"].location == ParameterLocation.QUERY
            assert "limit" in params
            assert params["limit"].default == 10
        finally:
            os.unlink(fname)

    def test_request_body(self):
        """Parse request body."""
        api = parse_file("openapi.yaml")
        route = next(r for r in api.routes if r.method == HttpMethod.POST and r.path == "/users")
        assert route.request_body is not None
        assert route.request_body.content_type == "application/json"
        assert route.request_body.required is True
        # Schema is resolved, so check for the actual schema content
        assert route.request_body.schema.get("type") == "object"
        assert "name" in route.request_body.schema.get("properties", {})

    def test_response_parsing(self):
        """Parse multiple responses."""
        api = parse_file("openapi.yaml")
        route = next(r for r in api.routes if r.path == "/users/{id}" and r.method == HttpMethod.GET)
        status_codes = [r.status_code for r in route.responses]
        assert 200 in status_codes
        assert 404 in status_codes

    def test_204_no_content(self):
        """Handle 204 responses without content."""
        api = parse_file("openapi.yaml")
        route = next(r for r in api.routes if r.method == HttpMethod.DELETE and r.path == "/users/{id}")
        resp_204 = next(r for r in route.responses if r.status_code == 204)
        assert resp_204.content_type == ""
        assert resp_204.schema == {}

    def test_schema_resolution(self):
        """Resolve $ref in schemas."""
        api = parse_file("openapi.yaml")
        user_schema = api.schemas["User"].schema
        assert user_schema["type"] == "object"
        assert "id" in user_schema["properties"]
        assert user_schema["required"] == ["id", "name"]

    def test_enum_values(self):
        """Extract enum values."""
        api = parse_file("openapi.yaml")
        user_schema = api.schemas["User"].schema
        role_prop = user_schema["properties"]["role"]
        assert role_prop["enum"] == ["admin", "user", "guest"]

    def test_default_values(self):
        """Extract default values."""
        api = parse_file("openapi.yaml")
        user_schema = api.schemas["User"].schema
        active_prop = user_schema["properties"]["active"]
        assert active_prop.get("default") is True


class TestParseOpenApi:
    """Tests for parse_openapi function."""

    def test_parse_dict_spec(self):
        """Parse spec from dictionary."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Dict API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {"schema": {"type": "array", "items": {"type": "string"}}}
                                }
                            }
                        }
                    }
                }
            },
        }
        api = parse_openapi(spec)
        assert api.title == "Dict API"
        assert len(api.routes) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])