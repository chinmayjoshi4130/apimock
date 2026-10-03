"""Tests for mock data generator."""

import pytest
from apimock.parser.openapi import parse_file
from apimock.mock.generator import create_generator, MockGenerator


class TestMockGenerator:
    """Tests for mock data generation."""

    @pytest.fixture
    def api(self):
        return parse_file("openapi.yaml")

    @pytest.fixture
    def generator(self, api):
        return create_generator(api, seed=42)

    def test_generate_string(self, generator):
        """Generate string values."""
        schema = {"type": "string"}
        result = generator.generate(schema)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_string_with_format(self, generator):
        """Generate formatted strings."""
        # Email
        result = generator.generate({"type": "string", "format": "email"})
        assert "@" in result
        assert "." in result

        # UUID
        result = generator.generate({"type": "string", "format": "uuid"})
        assert len(result) == 36
        assert result.count("-") == 4

        # Date-time
        result = generator.generate({"type": "string", "format": "date-time"})
        assert "T" in result

    def test_generate_string_with_constraints(self, generator):
        """Generate strings with length constraints."""
        schema = {"type": "string", "minLength": 5, "maxLength": 10}
        result = generator.generate(schema)
        assert 5 <= len(result) <= 10

    def test_generate_integer(self, generator):
        """Generate integer values."""
        schema = {"type": "integer", "minimum": 1, "maximum": 100}
        result = generator.generate(schema)
        assert isinstance(result, int)
        assert 1 <= result <= 100

    def test_generate_number(self, generator):
        """Generate number values."""
        schema = {"type": "number", "minimum": 0.0, "maximum": 10.0}
        result = generator.generate(schema)
        assert isinstance(result, float)
        assert 0.0 <= result <= 10.0

    def test_generate_boolean(self, generator):
        """Generate boolean values."""
        schema = {"type": "boolean"}
        result = generator.generate(schema)
        assert isinstance(result, bool)

    def test_generate_array(self, generator):
        """Generate array values."""
        schema = {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5}
        result = generator.generate(schema)
        assert isinstance(result, list)
        assert 1 <= len(result) <= 5
        assert all(isinstance(item, str) for item in result)

    def test_generate_array_unique(self, generator):
        """Generate unique array items."""
        schema = {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 1000},
            "minItems": 5,
            "maxItems": 5,
            "uniqueItems": True,
        }
        result = generator.generate(schema)
        assert len(result) == 5
        assert len(set(result)) == 5

    def test_generate_object(self, generator):
        """Generate object values."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        result = generator.generate(schema)
        assert isinstance(result, dict)
        assert "name" in result
        assert isinstance(result["name"], str)
        # age is optional, may or may not be present

    def test_generate_object_required(self, generator):
        """Generate object with required fields."""
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
            "required": ["id", "name"],
        }
        result = generator.generate(schema)
        assert "id" in result
        assert "name" in result
        assert isinstance(result["id"], int)
        assert isinstance(result["name"], str)

    def test_example_priority(self, generator):
        """Explicit example takes priority."""
        schema = {"type": "string", "example": "explicit-example"}
        result = generator.generate(schema)
        assert result == "explicit-example"

    def test_examples_priority(self, generator):
        """Examples take priority over generated."""
        schema = {"type": "string", "examples": {"ex1": {"value": "from-examples"}}}
        result = generator.generate(schema)
        assert result == "from-examples"

    def test_default_priority(self, generator):
        """Default takes priority over generated."""
        schema = {"type": "string", "default": "default-value"}
        result = generator.generate(schema)
        assert result == "default-value"

    def test_enum_priority(self, generator):
        """Enum takes priority over generated."""
        schema = {"type": "string", "enum": ["a", "b", "c"]}
        result = generator.generate(schema)
        assert result in ["a", "b", "c"]

    def test_deterministic_generation(self, api):
        """Same seed produces same output."""
        gen1 = create_generator(api, seed=123)
        gen2 = create_generator(api, seed=123)

        route = next(r for r in api.routes if r.path == "/users" and r.method.value == "GET")
        result1 = gen1.generate_response(route)
        result2 = gen2.generate_response(route)
        assert result1 == result2

    def test_different_seeds_different_output(self, api):
        """Different seeds produce different output."""
        gen1 = create_generator(api, seed=1)
        gen2 = create_generator(api, seed=2)

        route = next(r for r in api.routes if r.path == "/users" and r.method.value == "GET")
        result1 = gen1.generate_response(route)
        result2 = gen2.generate_response(route)
        assert result1 != result2

    def test_generate_response_from_schema(self, generator, api):
        """Generate response from route's response schema."""
        route = next(r for r in api.routes if r.path == "/users/{id}" and r.method.value == "GET")
        result = generator.generate_response(route, status_code=200)
        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result

    def test_generate_response_prefers_2xx(self, generator, api):
        """Prefer 2xx status code for response generation."""
        route = next(r for r in api.routes if r.path == "/users/{id}" and r.method.value == "GET")
        result = generator.generate_response(route)
        assert isinstance(result, dict)
        assert "id" in result

    def test_generate_response_fallback(self, generator, api):
        """Fallback to any response if no 2xx."""
        route = next(r for r in api.routes if r.path == "/users/{id}" and r.method.value == "DELETE")
        result = generator.generate_response(route)
        assert result == {"message": "OK"}

    def test_format_variations(self, generator):
        """Test various format types."""
        formats = {
            "uri": lambda x: x.startswith("http"),
            "url": lambda x: x.startswith("http"),
            "date": lambda x: len(x) == 10 and x.count("-") == 2,
            "time": lambda x: ":" in x,
            "ipv4": lambda x: len(x.split(".")) == 4,
            "ipv6": lambda x: ":" in x,
            "hostname": lambda x: "." in x,
        }
        for fmt, validator in formats.items():
            result = generator.generate({"type": "string", "format": fmt})
            assert validator(result), f"Format {fmt} failed: {result}"


class TestMockGeneratorEdgeCases:
    """Edge case tests for mock generator."""

    @pytest.fixture
    def api(self):
        return parse_file("openapi.yaml")

    def test_empty_schema(self, api):
        """Handle empty schema."""
        gen = create_generator(api, seed=42)
        result = gen.generate({})
        assert isinstance(result, dict)  # Defaults to object

    def test_null_type(self, api):
        """Handle null type."""
        gen = create_generator(api, seed=42)
        result = gen.generate({"type": "null"})
        assert result is None

    def test_unknown_type(self, api):
        """Handle unknown type gracefully."""
        gen = create_generator(api, seed=42)
        result = gen.generate({"type": "unknown"})
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])