"""Mock data generator for ApiMock."""

import random
import string
from typing import Any

from faker import Faker

from apimock.mock.schema import (
    resolve_refs,
    get_schema_type,
    get_example_value,
    get_default_value,
    get_enum_values,
    is_required_property,
)
from apimock.parser.models import NormalizedApi


class MockGenerator:
    """Generates deterministic mock data from OpenAPI schemas."""

    def __init__(self, api: NormalizedApi, seed: int | None = None):
        self.api = api
        self.seed = seed
        self.rng = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            self.faker.seed_instance(seed)

        # Pre-resolve all schemas
        self.resolved_schemas: dict[str, dict[str, Any]] = {}
        for name, schema in api.schemas.items():
            self.resolved_schemas[name] = resolve_refs(schema.schema, {n: s.schema for n, s in api.schemas.items()})

    def generate(self, schema: dict[str, Any] | str) -> Any:
        """Generate mock data from a schema."""
        # Handle string reference to named schema
        if isinstance(schema, str):
            schema = self._resolve_schema_ref(schema)
        
        # Resolve any refs in the schema
        resolved = resolve_refs(schema, {n: s.schema for n, s in self.api.schemas.items()})

        # Priority: example > examples > default > enum > generated
        example = get_example_value(resolved)
        if example is not None:
            return example

        default = get_default_value(resolved)
        if default is not None:
            return default

        enum_values = get_enum_values(resolved)
        if enum_values:
            return self.rng.choice(enum_values)

        return self._generate_by_type(resolved)

    def _resolve_schema_ref(self, ref: str) -> dict[str, Any]:
        """Resolve a schema reference by name."""
        if ref in self.api.schemas:
            return self.api.schemas[ref].schema
        # Try to parse as inline type spec
        from apimock.parser.apimock_format import parse_type_spec
        return parse_type_spec(ref)

    def _generate_by_type(self, schema: dict[str, Any]) -> Any:
        """Generate value based on schema type."""
        schema_type = get_schema_type(schema)

        if schema_type == "string":
            return self._generate_string(schema)
        elif schema_type == "integer":
            return self._generate_integer(schema)
        elif schema_type == "number":
            return self._generate_number(schema)
        elif schema_type == "boolean":
            return self.rng.choice([True, False])
        elif schema_type == "array":
            return self._generate_array(schema)
        elif schema_type == "object":
            return self._generate_object(schema)
        elif schema_type == "null":
            return None
        else:
            return self._generate_string(schema)

    def _generate_string(self, schema: dict[str, Any]) -> str:
        """Generate a string value."""
        format_ = schema.get("format")
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", 50)

        # Use faker for common formats
        if format_ == "email":
            return self.faker.email()
        elif format_ == "uuid":
            return self.faker.uuid4()
        elif format_ == "uri" or format_ == "url":
            return self.faker.url()
        elif format_ == "date-time":
            return self.faker.iso8601()
        elif format_ == "date":
            return self.faker.date()
        elif format_ == "time":
            return self.faker.time()
        elif format_ == "ipv4":
            return self.faker.ipv4()
        elif format_ == "ipv6":
            return self.faker.ipv6()
        elif format_ == "hostname":
            return self.faker.hostname()
        elif format_ == "password":
            return self.faker.password()
        elif format_ == "byte":
            return self.faker.binary(length=16).decode("latin-1")

        # Check for pattern
        pattern = schema.get("pattern")
        if pattern:
            return self._generate_from_pattern(pattern, min_length, max_length)

        # Generate random string
        length = self.rng.randint(min_length, max_length)
        return "".join(self.rng.choices(string.ascii_letters + string.digits, k=length))

    def _generate_from_pattern(self, pattern: str, min_len: int, max_len: int) -> str:
        """Generate string matching a simple regex pattern."""
        # Simplified pattern matching for common cases
        if pattern == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$":
            return self.faker.email()
        if pattern.startswith("^") and pattern.endswith("$"):
            # Try to extract character class
            inner = pattern[1:-1]
            if inner.startswith("[") and "]" in inner:
                char_class = inner[1:inner.index("]") + 1]
                return self._generate_from_char_class(char_class, min_len, max_len)
        return self._generate_string({**schema, "format": None} if (schema := {}) else {})

    def _generate_from_char_class(self, char_class: str, min_len: int, max_len: int) -> str:
        """Generate string from character class."""
        # Simplified: just use alphanumeric
        length = self.rng.randint(min_len, max_len)
        return "".join(self.rng.choices(string.ascii_letters + string.digits, k=length))

    def _generate_integer(self, schema: dict[str, Any]) -> int:
        """Generate an integer value."""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)
        exclusive_min = schema.get("exclusiveMinimum", False)
        exclusive_max = schema.get("exclusiveMaximum", False)

        if exclusive_min:
            minimum += 1
        if exclusive_max:
            maximum -= 1

        return self.rng.randint(minimum, maximum)

    def _generate_number(self, schema: dict[str, Any]) -> float:
        """Generate a number value."""
        minimum = schema.get("minimum", 0.0)
        maximum = schema.get("maximum", 1000.0)
        exclusive_min = schema.get("exclusiveMinimum", False)
        exclusive_max = schema.get("exclusiveMaximum", False)

        if exclusive_min:
            minimum += 0.001
        if exclusive_max:
            maximum -= 0.001

        return round(self.rng.uniform(minimum, maximum), 2)

    def _generate_array(self, schema: dict[str, Any]) -> list[Any]:
        """Generate an array value."""
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)  # Default to at least 1 item
        max_items = schema.get("maxItems", 10)
        unique_items = schema.get("uniqueItems", False)

        count = self.rng.randint(min_items, max_items)
        result = []

        if unique_items:
            seen = set()
            while len(result) < count:
                item = self.generate(items_schema)
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        else:
            result = [self.generate(items_schema) for _ in range(count)]

        return result

    def _generate_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate an object value."""
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_props = schema.get("additionalProperties", True)

        result = {}

        # Generate required properties first
        for prop_name in required:
            if prop_name in properties:
                result[prop_name] = self.generate(properties[prop_name])

        # Generate other properties (with some probability)
        for prop_name, prop_schema in properties.items():
            if prop_name not in result:
                # 80% chance to include optional properties
                if self.rng.random() < 0.8:
                    result[prop_name] = self.generate(prop_schema)

        # Handle additionalProperties
        if additional_props and isinstance(additional_props, dict):
            # Generate 0-2 extra properties
            for _ in range(self.rng.randint(0, 2)):
                extra_name = f"extra_{self.faker.word()}"
                result[extra_name] = self.generate(additional_props)

        return result

    def generate_response(self, route, status_code: int = 200) -> Any:
        """Generate a response for a specific route and status code."""
        # Find matching response
        response = None
        for r in route.responses:
            if r.status_code == status_code:
                response = r
                break

        # Fallback to first successful response
        if response is None:
            for r in route.responses:
                if 200 <= r.status_code < 300:
                    response = r
                    break

        # Fallback to any response
        if response is None and route.responses:
            response = route.responses[0]

        if response is None:
            return {"message": "No response defined"}

        # Use explicit example if available
        if response.example is not None:
            return response.example

        if response.examples:
            first_example = next(iter(response.examples.values()))
            if isinstance(first_example, dict) and "value" in first_example:
                return first_example["value"]
            return first_example

        # Generate from schema
        if response.schema:
            return self.generate(response.schema)

        return {"message": "OK"}


def create_generator(api: NormalizedApi, seed: int | None = None) -> MockGenerator:
    """Factory function to create a MockGenerator."""
    return MockGenerator(api, seed)