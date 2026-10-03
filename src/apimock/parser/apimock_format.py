"""ApiMock native format parser - a simpler alternative to OpenAPI."""

import json
import re
from pathlib import Path
from typing import Any

import yaml

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
from apimock.parser.openapi import OpenApiParseError


class ApiMockFormatError(OpenApiParseError):
    """Raised when ApiMock format file cannot be parsed."""
    pass


def load_apimock(file_path: str | Path) -> dict[str, Any]:
    """Load ApiMock format from YAML or JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise ApiMockFormatError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise ApiMockFormatError(f"Failed to read file: {e}")

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
        raise ApiMockFormatError(f"Failed to parse file: {e}")


def is_apimock_format(data: dict[str, Any]) -> bool:
    """Check if data is in ApiMock native format."""
    # Must have 'endpoints' or 'routes' key
    return "endpoints" in data or "routes" in data


def parse_type_spec(spec: str | dict) -> dict:
    """Parse a type specification string or dict into a schema dict.
    
    String format examples:
    - "string" -> {"type": "string"}
    - "string:email" -> {"type": "string", "format": "email"}
    - "integer:1-100" -> {"type": "integer", "minimum": 1, "maximum": 100}
    - "number:0.0-10.0" -> {"type": "number", "minimum": 0.0, "maximum": 10.0}
    - "boolean" -> {"type": "boolean"}
    - "array<string>" -> {"type": "array", "items": {"type": "string"}}
    - "array<string:email>" -> {"type": "array", "items": {"type": "string", "format": "email"}}
    - "object{name:string,age:integer}" -> {"type": "object", "properties": {...}}
    - "string=default_value" -> {"type": "string", "default": "default_value"}
    - "string:enum(a,b,c)" -> {"type": "string", "enum": ["a", "b", "c"]}
    """
    if isinstance(spec, dict):
        # Recursively parse nested properties and items
        result = dict(spec)
        if result.get("type") == "object" and "properties" in result:
            parsed_props = {}
            for prop_name, prop_spec in result["properties"].items():
                parsed_props[prop_name] = parse_type_spec(prop_spec)
            result["properties"] = parsed_props
        elif result.get("type") == "array" and "items" in result:
            result["items"] = parse_type_spec(result["items"])
        return result

    if not isinstance(spec, str):
        return {"type": "string"}

    # Parse default value: type=default
    default = None
    if "=" in spec and not spec.startswith("object{") and not spec.startswith("array<"):
        parts = spec.split("=", 1)
        spec = parts[0]
        default = parts[1]
        # Try to parse default as JSON
        try:
            default = json.loads(default)
        except json.JSONDecodeError:
            pass  # Keep as string

    # Parse enum: type:enum(a,b,c)
    enum = None
    enum_match = re.match(r"^(.+):enum\((.+)\)$", spec)
    if enum_match:
        spec = enum_match.group(1)
        enum = [e.strip() for e in enum_match.group(2).split(",")]

    # Parse object type: object{field:type,field:type}
    obj_match = re.match(r"^object\{(.+)\}$", spec)
    if obj_match:
        fields_str = obj_match.group(1)
        properties = {}
        required = []
        for field_spec in fields_str.split(","):
            field_spec = field_spec.strip()
            if not field_spec:
                continue
            # Check for required marker (!)
            is_required = field_spec.endswith("!")
            if is_required:
                field_spec = field_spec[:-1]
            # Parse field:type
            if ":" in field_spec:
                field_name, field_type = field_spec.split(":", 1)
                field_name = field_name.strip()
                field_type = field_type.strip()
            else:
                field_name = field_spec
                field_type = "string"
            properties[field_name] = parse_type_spec(field_type)
            if is_required:
                required.append(field_name)
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        if default is not None:
            schema["default"] = default
        if enum is not None:
            schema["enum"] = enum
        return schema

    # Parse array type: array<item_type>
    array_match = re.match(r"^array\<(.+)\>$", spec)
    if array_match:
        item_type = array_match.group(1)
        schema = {"type": "array", "items": parse_type_spec(item_type)}
        if default is not None:
            schema["default"] = default
        if enum is not None:
            schema["enum"] = enum
        return schema

    # Parse primitive types with optional format/constraints: type:format or type:min-max
    type_parts = spec.split(":", 1)
    base_type = type_parts[0].strip()

    schema = {"type": base_type}

    if len(type_parts) > 1:
        constraint = type_parts[1].strip()
        
        # Format: string:email, string:uuid, etc.
        if base_type == "string" and not re.match(r"^\d", constraint):
            schema["format"] = constraint
        # Range: integer:1-100, number:0.0-10.0
        elif "-" in constraint:
            try:
                min_val, max_val = constraint.split("-", 1)
                if base_type == "integer":
                    schema["minimum"] = int(min_val)
                    schema["maximum"] = int(max_val)
                elif base_type == "number":
                    schema["minimum"] = float(min_val)
                    schema["maximum"] = float(max_val)
            except ValueError:
                pass

    if default is not None:
        schema["default"] = default
    if enum is not None:
        schema["enum"] = enum

    return schema


def parse_endpoint(endpoint: dict | str) -> Route:
    """Parse a single endpoint definition.
    
    String format: "METHOD /path" or "METHOD /path { ... }"
    Dict format: {
        "method": "GET",
        "path": "/users",
        "params": {...},
        "body": {...},
        "responses": {...}
    }
    """
    if isinstance(endpoint, str):
        # Parse "METHOD /path" or "METHOD /path { ... }"
        match = re.match(r"^(\w+)\s+(\S+)(?:\s+\{(.+)\})?$", endpoint.strip())
        if not match:
            raise ApiMockFormatError(f"Invalid endpoint format: {endpoint}")
        method_str, path, inline = match.groups()
        method = HttpMethod(method_str.upper())
        
        params = {}
        body = None
        responses = {}
        
        if inline:
            # Parse inline spec: param:name=type, body:type, resp:code=type
            for part in inline.split(","):
                part = part.strip()
                if part.startswith("param:"):
                    _, rest = part.split(":", 1)
                    if "=" in rest:
                        name, type_spec = rest.split("=", 1)
                        params[name.strip()] = parse_type_spec(type_spec.strip())
                elif part.startswith("body:"):
                    _, type_spec = part.split(":", 1)
                    body = parse_type_spec(type_spec.strip())
                elif part.startswith("resp:"):
                    _, rest = part.split(":", 1)
                    if "=" in rest:
                        code, type_spec = rest.split("=", 1)
                        responses[int(code.strip())] = parse_type_spec(type_spec.strip())
        
        return build_route(method, path, params, body, responses)

    # Dict format
    method = HttpMethod(endpoint.get("method", "GET").upper())
    path = endpoint.get("path", "/")
    
    # Parse parameters
    params = {}
    for name, spec in endpoint.get("params", {}).items():
        params[name] = parse_type_spec(spec)
    
    # Parse body
    body = None
    if "body" in endpoint:
        body = parse_type_spec(endpoint["body"])
    
    # Parse responses
    responses = {}
    for code, spec in endpoint.get("responses", {}).items():
        responses[int(code)] = parse_type_spec(spec)
    
    return build_route(method, path, params, body, responses)


def build_route(method: HttpMethod, path: str, params: dict, body: dict | None, responses: dict) -> Route:
    """Build a Route object from parsed components."""
    # Extract path parameters from path
    path_params = re.findall(r"\{([^}]+)\}", path)
    
    parameters = []
    
    # Path parameters
    for param_name in path_params:
        param_spec = params.pop(param_name, {"type": "string"})
        parameters.append(Parameter(
            name=param_name,
            location=ParameterLocation.PATH,
            required=True,
            schema=param_spec,
        ))
    
    # Query parameters (remaining params)
    for name, spec in params.items():
        parameters.append(Parameter(
            name=name,
            location=ParameterLocation.QUERY,
            required=spec.get("required", False),
            schema=spec,
            example=spec.get("example"),
            default=spec.get("default"),
            enum=spec.get("enum", []),
        ))
    
    # Request body
    request_body = None
    if body:
        request_body = RequestBody(
            content_type="application/json",
            schema=body,
            example=body.get("example"),
            required=True,
        )
    
    # Responses
    response_list = []
    for code, spec in responses.items():
        response_list.append(Response(
            status_code=code,
            content_type="application/json",
            schema=spec,
            example=spec.get("example"),
        ))
    
    # Default 200 response if none specified
    if not response_list:
        response_list.append(Response(
            status_code=200,
            content_type="application/json",
            schema={"type": "object"},
        ))
    
    return Route(
        path=path,
        method=method,
        parameters=parameters,
        request_body=request_body,
        responses=response_list,
        summary=path,
    )


def parse_schema_def(schema_def: dict) -> dict[str, Schema]:
    """Parse schema definitions."""
    schemas = {}
    for name, spec in schema_def.items():
        schema = parse_type_spec(spec)
        schemas[name] = Schema(name=name, schema=schema)
    return schemas


def parse_apimock(data: dict[str, Any]) -> NormalizedApi:
    """Parse ApiMock format into normalized API model."""
    info = data.get("info", {})
    title = info.get("title", "ApiMock API")
    version = info.get("version", "1.0.0")
    
    # Parse schemas
    schemas = parse_schema_def(data.get("schemas", {}))
    
    # Parse endpoints/routes
    endpoints = data.get("endpoints") or data.get("routes", [])
    routes = []
    for endpoint in endpoints:
        routes.append(parse_endpoint(endpoint))
    
    return NormalizedApi(
        title=title,
        version=version,
        routes=routes,
        schemas=schemas,
        servers=[{"url": info.get("server", "http://localhost:8080")}],
        base_path="",
    )


def parse_apimock_file(file_path: str | Path) -> NormalizedApi:
    """Parse ApiMock format file into normalized API model."""
    data = load_apimock(file_path)
    
    if not is_apimock_format(data):
        raise ApiMockFormatError("Not a valid ApiMock format (missing 'endpoints' or 'routes')")
    
    return parse_apimock(data)