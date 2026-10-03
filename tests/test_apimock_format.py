"""Tests for ApiMock native format parser."""

import pytest
import tempfile
import os

from apimock.parser.apimock_format import (
    load_apimock,
    is_apimock_format,
    parse_apimock_file,
    parse_apimock,
    parse_type_spec,
    parse_endpoint,
    ApiMockFormatError,
)
from apimock.parser.models import HttpMethod, ParameterLocation


class TestApiMockFormatParser:
    """Tests for ApiMock native format parsing."""

    def test_load_apimock_yaml(self):
        """Load ApiMock format from YAML file."""
        content = """
info:
  title: Test API
  version: 1.0.0
endpoints:
  - "GET /users"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            fname = f.name
        try:
            loaded = load_apimock(fname)
            assert loaded["info"]["title"] == "Test API"
            assert "endpoints" in loaded
        finally:
            os.unlink(fname)

    def test_load_apimock_json(self):
        """Load ApiMock format from JSON file."""
        content = {
            "info": {"title": "Test API", "version": "1.0.0"},
            "endpoints": [{"method": "GET", "path": "/users"}]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json
            json.dump(content, f)
            fname = f.name
        try:
            loaded = load_apimock(fname)
            assert loaded["info"]["title"] == "Test API"
        finally:
            os.unlink(fname)

    def test_load_apimock_missing_file(self):
        """Fail on missing file."""
        with pytest.raises(ApiMockFormatError) as exc:
            load_apimock("nonexistent.mock")
        assert "File not found" in str(exc.value)

    def test_is_apimock_format(self):
        """Detect ApiMock format."""
        valid1 = {"endpoints": []}
        valid2 = {"routes": []}
        invalid = {"openapi": "3.0.0", "info": {}, "paths": {}}
        
        assert is_apimock_format(valid1) is True
        assert is_apimock_format(valid2) is True
        assert is_apimock_format(invalid) is False

    def test_parse_type_spec_primitives(self):
        """Parse primitive type specifications."""
        # String
        assert parse_type_spec("string") == {"type": "string"}
        # String with format
        assert parse_type_spec("string:email") == {"type": "string", "format": "email"}
        # Integer with range
        assert parse_type_spec("integer:1-100") == {"type": "integer", "minimum": 1, "maximum": 100}
        # Number with range
        assert parse_type_spec("number:0.0-10.0") == {"type": "number", "minimum": 0.0, "maximum": 10.0}
        # Boolean
        assert parse_type_spec("boolean") == {"type": "boolean"}
        # String with enum
        result = parse_type_spec("string:enum(a,b,c)")
        assert result == {"type": "string", "enum": ["a", "b", "c"]}

    def test_parse_type_spec_with_default(self):
        """Parse type spec with default value."""
        result = parse_type_spec("string=hello")
        assert result == {"type": "string", "default": "hello"}
        
        result = parse_type_spec("integer=42")
        assert result == {"type": "integer", "default": 42}
        
        result = parse_type_spec("boolean=true")
        assert result == {"type": "boolean", "default": True}

    def test_parse_type_spec_object(self):
        """Parse object type specification."""
        result = parse_type_spec("object{name:string,age:integer}")
        assert result["type"] == "object"
        assert "name" in result["properties"]
        assert "age" in result["properties"]
        assert result["properties"]["name"]["type"] == "string"
        assert result["properties"]["age"]["type"] == "integer"

    def test_parse_type_spec_object_required(self):
        """Parse object with required fields."""
        result = parse_type_spec("object{name:string!,age:integer}")
        assert result["type"] == "object"
        assert result["required"] == ["name"]
        assert "age" not in result["required"]

    def test_parse_type_spec_array(self):
        """Parse array type specification."""
        result = parse_type_spec("array<string>")
        assert result["type"] == "array"
        assert result["items"]["type"] == "string"
        
        # Nested array
        result = parse_type_spec("array<array<string>>")
        assert result["type"] == "array"
        assert result["items"]["type"] == "array"
        assert result["items"]["items"]["type"] == "string"

    def test_parse_type_spec_named_ref(self):
        """Parse reference to named schema (returns as-is for later resolution)."""
        result = parse_type_spec("User")
        assert result == {"type": "User"}
        
        result = parse_type_spec("UserList")
        assert result == {"type": "UserList"}

    def test_parse_string_endpoint(self):
        """Parse endpoint from string format."""
        route = parse_endpoint("GET /users")
        assert route.method == HttpMethod.GET
        assert route.path == "/users"
        
        route = parse_endpoint("POST /users {body:UserInput, resp:201=User}")
        assert route.method == HttpMethod.POST
        assert route.path == "/users"
        assert route.request_body is not None
        assert route.request_body.schema == {"type": "UserInput"}

    def test_parse_string_endpoint_with_path_params(self):
        """Parse endpoint with path parameters."""
        route = parse_endpoint("GET /users/{id}")
        assert route.path == "/users/{id}"
        path_params = [p for p in route.parameters if p.location == ParameterLocation.PATH]
        assert len(path_params) == 1
        assert path_params[0].name == "id"

    def test_parse_string_endpoint_with_query_params(self):
        """Parse endpoint with query parameters."""
        route = parse_endpoint("GET /users {param:limit=integer:1-100=20, param:offset=integer=0}")
        query_params = [p for p in route.parameters if p.location == ParameterLocation.QUERY]
        assert len(query_params) == 2
        limit = next(p for p in query_params if p.name == "limit")
        assert limit.schema["minimum"] == 1
        assert limit.schema["maximum"] == 100
        assert limit.default == 20

    def test_parse_dict_endpoint(self):
        """Parse endpoint from dict format."""
        endpoint = {
            "method": "POST",
            "path": "/users",
            "params": {"limit": "integer:1-100"},
            "body": "UserInput",
            "responses": {
                201: "User",
                400: "Error"
            }
        }
        route = parse_endpoint(endpoint)
        assert route.method == HttpMethod.POST
        assert route.path == "/users"
        assert route.request_body is not None
        assert route.request_body.schema == {"type": "UserInput"}
        status_codes = [r.status_code for r in route.responses]
        assert 201 in status_codes
        assert 400 in status_codes

    def test_parse_full_spec(self):
        """Parse complete ApiMock specification."""
        spec = {
            "info": {"title": "Test API", "version": "1.0.0"},
            "schemas": {
                "User": "object{id:integer,name:string,email:string:email}",
                "UserInput": "object{name:string!,email:string:email!}"
            },
            "endpoints": [
                "GET /users {param:limit=integer:1-100=20, resp:200=array<User>}",
                "POST /users {body:UserInput, resp:201=User}",
                "GET /users/{id} {resp:200=User, resp:404=Error}"
            ]
        }
        api = parse_apimock(spec)
        assert api.title == "Test API"
        assert api.version == "1.0.0"
        assert len(api.routes) == 3
        assert "User" in api.schemas
        assert "UserInput" in api.schemas

    def test_parse_file(self):
        """Parse ApiMock format file."""
        content = """
info:
  title: File Test API
  version: 2.0.0
schemas:
  Item: "object{id:integer,name:string}"
endpoints:
  - "GET /items {resp:200=array<Item>}"
  - "POST /items {body:Item, resp:201=Item}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mock", delete=False) as f:
            f.write(content)
            fname = f.name
        try:
            api = parse_apimock_file(fname)
            assert api.title == "File Test API"
            assert api.version == "2.0.0"
            assert len(api.routes) == 2
            assert "Item" in api.schemas
        finally:
            os.unlink(fname)

    def test_method_case_insensitive(self):
        """HTTP method parsing is case insensitive."""
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            route = parse_endpoint(f"{method} /test")
            assert route.method.value == method.upper()

    def test_response_schema_resolution(self):
        """Test that response schemas reference named schemas correctly."""
        spec = {
            "schemas": {
                "User": "object{id:integer,name:string}"
            },
            "endpoints": [
                {"method": "GET", "path": "/users", "responses": {200: "array<User>"}}
            ]
        }
        api = parse_apimock(spec)
        route = api.routes[0]
        resp = route.responses[0]
        # Schema should reference UserList which references User
        assert resp.schema["type"] == "array"
        assert resp.schema["items"]["type"] == "User"


class TestApiMockFormatIntegration:
    """Integration tests with mock generator."""

    def test_deterministic_generation(self):
        """Same seed produces same output."""
        spec = {
            "info": {"title": "Test", "version": "1.0.0"},
            "schemas": {
                "User": "object{id:integer:1-1000,name:string,email:string:email}"
            },
            "endpoints": [
                "GET /users {resp:200=array<User>}"
            ]
        }
        from apimock.mock.generator import create_generator
        
        api = parse_apimock(spec)
        gen1 = create_generator(api, seed=42)
        gen2 = create_generator(api, seed=42)
        
        route = api.routes[0]
        result1 = gen1.generate_response(route)
        result2 = gen2.generate_response(route)
        
        assert result1 == result2

    def test_different_seeds_different_output(self):
        """Different seeds produce different output."""
        spec = {
            "info": {"title": "Test", "version": "1.0.0"},
            "schemas": {
                "User": "object{id:integer:1-1000,name:string}"
            },
            "endpoints": [
                "GET /users {resp:200=array<User>}"
            ]
        }
        from apimock.mock.generator import create_generator
        
        api = parse_apimock(spec)
        gen1 = create_generator(api, seed=1)
        gen2 = create_generator(api, seed=2)
        
        route = api.routes[0]
        result1 = gen1.generate_response(route)
        result2 = gen2.generate_response(route)
        
        assert result1 != result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])