"""Schema utilities for mock data generation."""

from typing import Any
from copy import deepcopy


def resolve_refs(schema: dict[str, Any], all_schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Resolve all $ref references and named type references in a schema."""
    if not isinstance(schema, dict):
        return schema

    result = deepcopy(schema)

    # Handle $ref (OpenAPI style)
    if "$ref" in result:
        ref = result["$ref"]
        if ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            if schema_name in all_schemas:
                return resolve_refs(all_schemas[schema_name], all_schemas)
        return result

    # Handle named type references (ApiMock format): {"type": "UserName"}
    if "type" in result and isinstance(result["type"], str):
        type_name = result["type"]
        if type_name in all_schemas and type_name not in ("string", "integer", "number", "boolean", "array", "object", "null"):
            # This is a reference to a named schema
            return resolve_refs(all_schemas[type_name], all_schemas)

    for key, value in result.items():
        if isinstance(value, dict):
            result[key] = resolve_refs(value, all_schemas)
        elif isinstance(value, list):
            result[key] = [resolve_refs(item, all_schemas) for item in value]

    return result


def get_schema_type(schema: dict[str, Any]) -> str:
    """Get the type from a schema, defaulting to 'object'."""
    return schema.get("type", "object")


def get_example_value(schema: dict[str, Any]) -> Any:
    """Get explicit example value from schema."""
    if "example" in schema:
        return schema["example"]
    if "examples" in schema and schema["examples"]:
        first_example = next(iter(schema["examples"].values()))
        if isinstance(first_example, dict) and "value" in first_example:
            return first_example["value"]
        return first_example
    return None


def get_default_value(schema: dict[str, Any]) -> Any:
    """Get default value from schema."""
    return schema.get("default")


def get_enum_values(schema: dict[str, Any]) -> list[Any]:
    """Get enum values from schema."""
    return schema.get("enum", [])


def is_required_property(schema: dict[str, Any], prop_name: str) -> bool:
    """Check if a property is required."""
    required = schema.get("required", [])
    return prop_name in required