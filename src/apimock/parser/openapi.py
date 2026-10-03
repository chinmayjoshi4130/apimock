"""OpenAPI 3.x parser for ApiMock."""

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate, ValidationError

from apimock.parser.models import (
    NormalizedApi,
    Route,
    Parameter,
    RequestBody,
    Response,
    ParameterLocation,
    HttpMethod,
    Schema,
)


class OpenApiParseError(Exception):
    """Raised when OpenAPI specification cannot be parsed."""

    def __init__(self, message: str, location: str = "", path: str = "", method: str = ""):
        self.message = message
        self.location = location
        self.path = path
        self.method = method
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [f"Error: {self.message}"]
        if self.path:
            parts.append(f"Path: {self.path}")
        if self.method:
            parts.append(f"Method: {self.method}")
        if self.location:
            parts.append(f"Location: {self.location}")
        return "\n".join(parts)


OPENAPI_30_SCHEMA = {
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string", "pattern": "^3\\."},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
            },
        },
        "paths": {"type": "object"},
        "components": {"type": "object"},
        "servers": {"type": "array"},
    },
}


def load_openapi(file_path: str | Path) -> dict[str, Any]:
    """Load OpenAPI spec from YAML or JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise OpenApiParseError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise OpenApiParseError(f"Failed to read file: {e}")

    try:
        if path.suffix.lower() in (".yaml", ".yml"):
            return yaml.safe_load(content)
        elif path.suffix.lower() == ".json":
            return json.loads(content)
        else:
            # Try YAML first, then JSON
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return json.loads(content)
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise OpenApiParseError(f"Failed to parse file: {e}")


def validate_openapi(spec: dict[str, Any]) -> None:
    """Validate OpenAPI specification structure."""
    openapi_version = spec.get("openapi", "")
    if not openapi_version.startswith("3."):
        if openapi_version.startswith("2."):
            raise OpenApiParseError(
                f"Unsupported OpenAPI version: {openapi_version}. ApiMock currently supports OpenAPI 3.x."
            )
        raise OpenApiParseError(f"Invalid OpenAPI version: {openapi_version}. Expected 3.x.")

    try:
        validate(instance=spec, schema=OPENAPI_30_SCHEMA)
    except ValidationError as e:
        raise OpenApiParseError(f"Invalid OpenAPI specification: {e.message}")


def resolve_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a local JSON reference ($ref) within the OpenAPI document."""
    if not ref.startswith("#/"):
        raise OpenApiParseError(f"External references not yet supported: {ref}")

    parts = ref[2:].split("/")
    current = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise OpenApiParseError(f"Unable to resolve reference: {ref}")
    return current


def parse_schema(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Parse and resolve schema, handling $ref."""
    if "$ref" in schema:
        return resolve_ref(spec, schema["$ref"])
    return schema


def parse_parameters(
    spec: dict[str, Any], params: list[dict[str, Any]]
) -> list[Parameter]:
    """Parse OpenAPI parameters into internal Parameter model."""
    result = []
    for param in params:
        param_schema = parse_schema(spec, param.get("schema", {}))
        location = param.get("in", "query")
        try:
            loc = ParameterLocation(location)
        except ValueError:
            loc = ParameterLocation.QUERY

        result.append(
            Parameter(
                name=param.get("name", ""),
                location=loc,
                required=param.get("required", False),
                schema=param_schema,
                example=param.get("example"),
                examples=param.get("examples", {}),
                default=param.get("default"),
                enum=param_schema.get("enum", []),
            )
        )
    return result


def parse_request_body(
    spec: dict[str, Any], request_body: dict[str, Any]
) -> RequestBody | None:
    """Parse OpenAPI requestBody into internal RequestBody model."""
    content = request_body.get("content", {})
    if not content:
        return None

    # Prefer application/json, fallback to first content type
    content_type = "application/json"
    if content_type not in content:
        content_type = next(iter(content))

    media_type = content[content_type]
    schema = parse_schema(spec, media_type.get("schema", {}))

    return RequestBody(
        content_type=content_type,
        schema=schema,
        example=media_type.get("example"),
        examples=media_type.get("examples", {}),
        required=request_body.get("required", False),
    )


def parse_responses(
    spec: dict[str, Any], responses: dict[str, Any]
) -> list[Response]:
    """Parse OpenAPI responses into internal Response model."""
    result = []
    for status_code, response in responses.items():
        content = response.get("content", {})
        
        if content:
            content_type = "application/json"
            if content_type not in content:
                content_type = next(iter(content))

            media_type = content[content_type]
            schema = parse_schema(spec, media_type.get("schema", {}))
            example = media_type.get("example")
            examples = media_type.get("examples", {})
        else:
            # Response without content (e.g., 204 No Content)
            content_type = ""
            schema = {}
            example = None
            examples = {}

        result.append(
            Response(
                status_code=int(status_code),
                content_type=content_type,
                schema=schema,
                example=example,
                examples=examples,
            )
        )
    return sorted(result, key=lambda r: r.status_code)


def parse_path(spec: dict[str, Any], path: str, path_item: dict[str, Any]) -> list[Route]:
    """Parse a single path item into Route objects."""
    routes = []
    parameters = path_item.get("parameters", [])

    for method_str, operation in path_item.items():
        if method_str.upper() not in HttpMethod.__members__:
            continue

        method = HttpMethod(method_str.upper())
        op_params = parse_parameters(spec, operation.get("parameters", []) + parameters)
        request_body = parse_request_body(spec, operation.get("requestBody", {})) if "requestBody" in operation else None
        responses = parse_responses(spec, operation.get("responses", {}))

        routes.append(
            Route(
                path=path,
                method=method,
                parameters=op_params,
                request_body=request_body,
                responses=responses,
                summary=operation.get("summary", ""),
                description=operation.get("description", ""),
                operation_id=operation.get("operationId", ""),
            )
        )
    return routes


def parse_schemas(spec: dict[str, Any]) -> dict[str, Schema]:
    """Parse components/schemas into internal Schema model."""
    schemas = {}
    components = spec.get("components", {})
    for name, schema in components.get("schemas", {}).items():
        resolved = parse_schema(spec, schema)
        schemas[name] = Schema(name=name, schema=resolved)
    return schemas


def parse_openapi(spec: dict[str, Any]) -> NormalizedApi:
    """Parse OpenAPI specification into normalized internal model."""
    validate_openapi(spec)

    info = spec.get("info", {})
    paths = spec.get("paths", {})
    servers = spec.get("servers", [])

    base_path = ""
    if servers:
        server = servers[0]
        base_path = server.get("url", "").rstrip("/")

    routes = []
    for path, path_item in paths.items():
        routes.extend(parse_path(spec, path, path_item))

    schemas = parse_schemas(spec)

    return NormalizedApi(
        title=info.get("title", ""),
        version=info.get("version", ""),
        routes=routes,
        schemas=schemas,
        servers=servers,
        base_path=base_path,
    )


def parse_file(file_path: str | Path) -> NormalizedApi:
    """Parse OpenAPI file into normalized internal model."""
    spec = load_openapi(file_path)
    return parse_openapi(spec)