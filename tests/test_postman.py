"""Tests for Postman Collection parser."""

import pytest
import tempfile
import json
import os

from apimock.parser.postman import (
    load_postman,
    is_postman_collection,
    parse_postman_file,
    parse_postman,
    PostmanParseError,
)
from apimock.parser.models import HttpMethod, ParameterLocation


class TestPostmanParser:
    """Tests for Postman Collection parsing."""

    def test_load_postman(self):
        """Load a Postman Collection JSON file."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": []
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(collection, f)
            fname = f.name
        try:
            loaded = load_postman(fname)
            assert loaded["info"]["name"] == "Test API"
        finally:
            os.unlink(fname)

    def test_load_postman_missing_file(self):
        """Fail on missing file."""
        with pytest.raises(PostmanParseError) as exc:
            load_postman("nonexistent.json")
        assert "File not found" in str(exc.value)

    def test_load_postman_invalid_json(self):
        """Fail on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            fname = f.name
        try:
            with pytest.raises(PostmanParseError) as exc:
                load_postman(fname)
            assert "Failed to parse JSON" in str(exc.value)
        finally:
            os.unlink(fname)

    def test_is_postman_collection(self):
        """Detect Postman Collection format."""
        valid = {
            "info": {"name": "Test", "version": "1.0.0"},
            "item": []
        }
        assert is_postman_collection(valid) is True

        invalid = {"openapi": "3.0.0", "info": {}, "paths": {}}
        assert is_postman_collection(invalid) is False

    def test_parse_simple_request(self):
        """Parse a simple GET request."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": "http://localhost:8080/users"
                    }
                }
            ]
        }
        api = parse_postman(collection)
        assert api.title == "Test API"
        assert len(api.routes) == 1
        route = api.routes[0]
        assert route.method == HttpMethod.GET
        assert route.path == "/users"

    def test_parse_request_with_query_params(self):
        """Parse request with query parameters."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Search",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "http://localhost:8080/search?q=test&limit=10",
                            "path": ["search"],
                            "query": [
                                {"key": "q", "value": "test"},
                                {"key": "limit", "value": "10"}
                            ]
                        }
                    }
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        params = {p.name: p for p in route.parameters}
        assert "q" in params
        assert params["q"].location == ParameterLocation.QUERY
        assert params["q"].example == "test"
        assert "limit" in params

    def test_parse_path_parameters(self):
        """Parse path parameters from URL."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Get User",
                    "request": {
                        "method": "GET",
                        "url": "http://localhost:8080/users/42"
                    }
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        # Should extract path parameter
        assert "/users/" in route.path
        path_params = [p for p in route.parameters if p.location == ParameterLocation.PATH]
        assert len(path_params) >= 1

    def test_parse_post_with_body(self):
        """Parse POST request with JSON body."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Create User",
                    "request": {
                        "method": "POST",
                        "url": "http://localhost:8080/users",
                        "body": {
                            "mode": "raw",
                            "raw": "{\"name\": \"John\", \"email\": \"john@example.com\"}",
                            "options": {"raw": {"language": "json"}}
                        }
                    }
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        assert route.method == HttpMethod.POST
        assert route.request_body is not None
        assert route.request_body.content_type == "application/json"

    def test_parse_response_examples(self):
        """Parse response examples from Postman."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Get User",
                    "request": {
                        "method": "GET",
                        "url": "http://localhost:8080/users/1"
                    },
                    "response": [
                        {
                            "name": "Success",
                            "code": 200,
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": "{\"id\": 1, \"name\": \"John\"}"
                        },
                        {
                            "name": "Not Found",
                            "code": 404,
                            "body": "{\"error\": \"Not found\"}"
                        }
                    ]
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        status_codes = [r.status_code for r in route.responses]
        assert 200 in status_codes
        assert 404 in status_codes
        # Check example is parsed
        resp_200 = next(r for r in route.responses if r.status_code == 200)
        assert resp_200.example is not None
        assert resp_200.example["id"] == 1

    def test_parse_headers(self):
        """Parse request headers."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Get Data",
                    "request": {
                        "method": "GET",
                        "url": "http://localhost:8080/data",
                        "header": [
                            {"key": "Authorization", "value": "Bearer token123"},
                            {"key": "Accept", "value": "application/json"}
                        ]
                    }
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        header_params = [p for p in route.parameters if p.location == ParameterLocation.HEADER]
        assert len(header_params) == 2
        auth = next(p for p in header_params if p.name == "Authorization")
        assert auth.example == "Bearer token123"

    def test_parse_folders(self):
        """Parse nested folders."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Users",
                    "item": [
                        {
                            "name": "List Users",
                            "request": {
                                "method": "GET",
                                "url": "http://localhost:8080/users"
                            }
                        },
                        {
                            "name": "Get User",
                            "request": {
                                "method": "GET",
                                "url": "http://localhost:8080/users/1"
                            }
                        }
                    ]
                }
            ]
        }
        api = parse_postman(collection)
        assert len(api.routes) == 2
        paths = [r.path for r in api.routes]
        assert "/users" in paths
        assert any("/users/" in p for p in paths)

    def test_parse_formdata_body(self):
        """Parse form-data request body."""
        collection = {
            "info": {"name": "Test API", "version": "1.0.0"},
            "item": [
                {
                    "name": "Upload",
                    "request": {
                        "method": "POST",
                        "url": "http://localhost:8080/upload",
                        "body": {
                            "mode": "formdata",
                            "formdata": [
                                {"key": "file", "value": "test.txt", "type": "file"},
                                {"key": "name", "value": "myfile"}
                            ]
                        }
                    }
                }
            ]
        }
        api = parse_postman(collection)
        route = api.routes[0]
        assert route.request_body is not None
        assert route.request_body.content_type == "multipart/form-data"

    def test_parse_file(self):
        """Parse Postman Collection file."""
        collection = {
            "info": {"name": "File Test", "version": "1.0.0"},
            "item": [
                {
                    "name": "Test",
                    "request": {
                        "method": "GET",
                        "url": "http://localhost:8080/test"
                    }
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(collection, f)
            fname = f.name
        try:
            api = parse_postman_file(fname)
            assert api.title == "File Test"
            assert len(api.routes) == 1
        finally:
            os.unlink(fname)

    def test_method_case_insensitive(self):
        """HTTP method parsing is case insensitive."""
        collection = {
            "info": {"name": "Test", "version": "1.0.0"},
            "item": [
                {"name": "Test", "request": {"method": "get", "url": "http://localhost:8080/a"}},
                {"name": "Test", "request": {"method": "POST", "url": "http://localhost:8080/b"}},
                {"name": "Test", "request": {"method": "patch", "url": "http://localhost:8080/c"}},
            ]
        }
        api = parse_postman(collection)
        methods = [r.method for r in api.routes]
        assert HttpMethod.GET in methods
        assert HttpMethod.POST in methods
        assert HttpMethod.PATCH in methods


if __name__ == "__main__":
    pytest.main([__file__, "-v"])