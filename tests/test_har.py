"""Tests for HAR parser."""

import pytest
import tempfile
import json
import os

from apimock.parser.har import (
    load_har,
    is_har,
    parse_har_file,
    parse_har,
    normalize_path,
    HARParseError,
)
from apimock.parser.models import HttpMethod, ParameterLocation


class TestHARParser:
    """Tests for HAR parsing."""

    def test_load_har(self):
        """Load a HAR file."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": []
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".har", delete=False) as f:
            json.dump(har, f)
            fname = f.name
        try:
            loaded = load_har(fname)
            assert loaded["log"]["creator"]["name"] == "Test"
        finally:
            os.unlink(fname)

    def test_load_har_missing_file(self):
        """Fail on missing file."""
        with pytest.raises(HARParseError) as exc:
            load_har("nonexistent.har")
        assert "File not found" in str(exc.value)

    def test_load_har_invalid_json(self):
        """Fail on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".har", delete=False) as f:
            f.write("invalid json")
            fname = f.name
        try:
            with pytest.raises(HARParseError) as exc:
                load_har(fname)
            assert "Failed to parse JSON" in str(exc.value)
        finally:
            os.unlink(fname)

    def test_is_har(self):
        """Detect HAR format."""
        valid = {
            "log": {
                "version": "1.2",
                "entries": []
            }
        }
        assert is_har(valid) is True

        invalid = {"openapi": "3.0.0", "info": {}, "paths": {}}
        assert is_har(invalid) is False

    def test_normalize_path(self):
        """Normalize paths by replacing IDs with parameters."""
        assert normalize_path("/api/users/42") == "/api/users/{id}"
        assert normalize_path("/api/users/123/posts/456") == "/api/users/{id}/posts/{id}"
        assert normalize_path("/api/users/550e8400-e29b-41d4-a716-446655440000") == "/api/users/{id}"
        assert normalize_path("/api/search") == "/api/search"
        assert normalize_path("/api/users/test@example.com") == "/api/users/{email}"

    def test_parse_simple_get(self):
        """Parse simple GET request."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/users",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "[{\"id\": 1}]"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        assert len(api.routes) == 1
        route = api.routes[0]
        assert route.method == HttpMethod.GET
        assert route.path == "/users"

    def test_parse_with_query_params(self):
        """Parse request with query parameters."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/search?q=test&limit=10",
                            "headers": [],
                            "queryString": [
                                {"name": "q", "value": "test"},
                                {"name": "limit", "value": "10"}
                            ]
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "[]"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        route = api.routes[0]
        params = {p.name: p for p in route.parameters}
        assert "q" in params
        assert params["q"].location == ParameterLocation.QUERY
        assert params["q"].example == "test"
        assert "limit" in params

    def test_normalize_path_parameters(self):
        """Normalize numeric IDs in paths."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/users/42",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{\"id\": 42}"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        route = api.routes[0]
        assert route.path == "/users/{id}"
        path_params = [p for p in route.parameters if p.location == ParameterLocation.PATH]
        assert len(path_params) == 1
        assert path_params[0].name == "id"

    def test_parse_post_with_body(self):
        """Parse POST request with JSON body."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "POST",
                            "url": "http://localhost:8080/users",
                            "headers": [
                                {"name": "Content-Type", "value": "application/json"}
                            ],
                            "queryString": [],
                            "postData": {
                                "mimeType": "application/json",
                                "text": "{\"name\": \"John\", \"email\": \"john@example.com\"}"
                            }
                        },
                        "response": {
                            "status": 201,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{\"id\": 1, \"name\": \"John\"}"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        route = api.routes[0]
        assert route.method == HttpMethod.POST
        assert route.request_body is not None
        assert route.request_body.content_type == "application/json"

    def test_merge_multiple_responses(self):
        """Merge multiple responses for same route."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/users/1",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{\"id\": 1, \"name\": \"First\"}"}
                        }
                    },
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/users/2",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{\"id\": 2, \"name\": \"Second\"}"}
                        }
                    },
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/users/999",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 404,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{\"error\": \"Not found\"}"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        assert len(api.routes) == 1
        route = api.routes[0]
        assert route.path == "/users/{id}"
        status_codes = [r.status_code for r in route.responses]
        assert 200 in status_codes
        assert 404 in status_codes

    def test_parse_headers(self):
        """Parse request headers."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/data",
                            "headers": [
                                {"name": "Authorization", "value": "Bearer token123"},
                                {"name": "Accept", "value": "application/json"},
                                {"name": "User-Agent", "value": "test-agent"}
                            ],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": "{}"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        route = api.routes[0]
        header_params = [p for p in route.parameters if p.location == ParameterLocation.HEADER]
        # Should include Authorization, but not Accept or User-Agent (filtered)
        # Headers are stored lowercase by extract_har_headers
        header_names = [p.name for p in header_params]
        assert "authorization" in header_names
        assert "accept" not in header_names
        assert "user-agent" not in header_names

    def test_parse_different_methods(self):
        """Parse various HTTP methods."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {"request": {"method": "GET", "url": "http://localhost:8080/a", "headers": [], "queryString": []}, "response": {"status": 200, "headers": [], "content": {}}},
                    {"request": {"method": "POST", "url": "http://localhost:8080/b", "headers": [], "queryString": []}, "response": {"status": 201, "headers": [], "content": {}}},
                    {"request": {"method": "PUT", "url": "http://localhost:8080/c", "headers": [], "queryString": []}, "response": {"status": 200, "headers": [], "content": {}}},
                    {"request": {"method": "PATCH", "url": "http://localhost:8080/d", "headers": [], "queryString": []}, "response": {"status": 200, "headers": [], "content": {}}},
                    {"request": {"method": "DELETE", "url": "http://localhost:8080/e", "headers": [], "queryString": []}, "response": {"status": 204, "headers": [], "content": {}}},
                ]
            }
        }
        api = parse_har(har)
        methods = {r.method for r in api.routes}
        assert HttpMethod.GET in methods
        assert HttpMethod.POST in methods
        assert HttpMethod.PUT in methods
        assert HttpMethod.PATCH in methods
        assert HttpMethod.DELETE in methods

    def test_base64_encoded_content(self):
        """Handle base64 encoded response content."""
        import base64
        encoded = base64.b64encode(b'{"id": 1}').decode("ascii")
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "http://localhost:8080/data",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {
                            "status": 200,
                            "headers": [{"name": "Content-Type", "value": "application/json"}],
                            "content": {"mimeType": "application/json", "text": encoded, "encoding": "base64"}
                        }
                    }
                ]
            }
        }
        api = parse_har(har)
        route = api.routes[0]
        # Should decode and parse
        assert route.responses[0].example is not None
        assert route.responses[0].example.get("id") == 1

    def test_parse_file(self):
        """Parse HAR file."""
        har = {
            "log": {
                "version": "1.2",
                "creator": {"name": "File Test", "version": "1.0"},
                "entries": [
                    {
                        "request": {"method": "GET", "url": "http://localhost:8080/test", "headers": [], "queryString": []},
                        "response": {"status": 200, "headers": [], "content": {}}
                    }
                ]
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".har", delete=False) as f:
            json.dump(har, f)
            fname = f.name
        try:
            api = parse_har_file(fname)
            assert "File Test" in api.title
            assert len(api.routes) == 1
        finally:
            os.unlink(fname)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])