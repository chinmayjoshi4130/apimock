"""Postman Collection parser for ApiMock."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

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


class PostmanParseError(OpenApiParseError):
    """Raised when Postman Collection cannot be parsed."""
    pass


def load_postman(file_path: str | Path) -> dict[str, Any]:
    """Load Postman Collection from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise PostmanParseError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise PostmanParseError(f"Failed to parse JSON: {e}")


def is_postman_collection(data: dict[str, Any]) -> bool:
    """Check if data is a Postman Collection."""
    return (
        "info" in data
        and "item" in data
        and isinstance(data.get("item"), list)
    )


def parse_postman_url(url: str | dict) -> tuple[str, dict[str, list[str]]]:
    """Parse Postman URL object or string into path and query params."""
    if isinstance(url, str):
        parsed = urlparse(url)
        path = parsed.path or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)
        return path, query

    # URL object format
    raw = url.get("raw", "")
    if raw:
        parsed = urlparse(raw)
        path = parsed.path or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)
        return path, query

    # Path segments
    path_parts = url.get("path", [])
    if isinstance(path_parts, list):
        path = "/" + "/".join(str(p) for p in path_parts)
    else:
        path = str(path_parts)

    # Query params
    query = {}
    for param in url.get("query", []):
        if param.get("disabled"):
            continue
        key = param.get("key", "")
        value = param.get("value", "")
        if key:
            query.setdefault(key, []).append(value)

    return path, query


def parse_postman_method(method: str) -> HttpMethod:
    """Parse HTTP method string to HttpMethod enum."""
    try:
        return HttpMethod(method.upper())
    except ValueError:
        return HttpMethod.GET


def parse_postman_header(header: dict) -> Parameter:
    """Parse Postman header into Parameter."""
    return Parameter(
        name=header.get("key", ""),
        location=ParameterLocation.HEADER,
        required=False,
        schema={"type": "string"},
        example=header.get("value"),
    )


def parse_postman_body(body: dict | None) -> RequestBody | None:
    """Parse Postman request body."""
    if not body:
        return None

    mode = body.get("mode", "raw")
    content_type = "application/json"

    if mode == "raw":
        raw = body.get("raw", "")
        options = body.get("options", {})
        raw_lang = options.get("raw", {}).get("language", "json")
        if raw_lang == "json":
            content_type = "application/json"
        elif raw_lang == "xml":
            content_type = "application/xml"
        elif raw_lang == "text":
            content_type = "text/plain"
        else:
            content_type = "application/json"

        # Try to parse as JSON schema
        schema = {"type": "object"}
        try:
            if raw:
                parsed = json.loads(raw)
                schema = {"type": "object", "example": parsed}
        except json.JSONDecodeError:
            schema = {"type": "string", "example": raw}

        return RequestBody(
            content_type=content_type,
            schema=schema,
            example=raw if raw else None,
        )

    elif mode == "formdata":
        # Form data - treat as object with string properties
        properties = {}
        for item in body.get("formdata", []):
            if item.get("disabled"):
                continue
            key = item.get("key", "")
            if key:
                properties[key] = {"type": "string", "example": item.get("value", "")}
        return RequestBody(
            content_type="multipart/form-data",
            schema={"type": "object", "properties": properties},
        )

    elif mode == "urlencoded":
        properties = {}
        for item in body.get("urlencoded", []):
            if item.get("disabled"):
                continue
            key = item.get("key", "")
            if key:
                properties[key] = {"type": "string", "example": item.get("value", "")}
        return RequestBody(
            content_type="application/x-www-form-urlencoded",
            schema={"type": "object", "properties": properties},
        )

    return None


def extract_responses_from_examples(item: dict) -> list[Response]:
    """Extract responses from Postman examples."""
    responses = []

    # Check for response examples in the item
    for example in item.get("response", []):
        code = example.get("code", 200)
        headers = {}
        for h in example.get("header", []):
            headers[h.get("key", "")] = h.get("value", "")

        body = example.get("body", "")
        content_type = "application/json"
        for h in example.get("header", []):
            if h.get("key", "").lower() == "content-type":
                content_type = h.get("value", "application/json")
                break

        # Try to parse body as JSON
        schema = {"type": "object"}
        example_val = None
        if body:
            try:
                parsed = json.loads(body)
                schema = {"type": "object", "example": parsed}
                example_val = parsed
            except json.JSONDecodeError:
                schema = {"type": "string"}
                example_val = body

        responses.append(Response(
            status_code=code,
            content_type=content_type,
            schema=schema,
            example=example_val,
        ))

    # Default response if none found
    if not responses:
        responses.append(Response(
            status_code=200,
            content_type="application/json",
            schema={"type": "object"},
        ))

    return responses


def parse_postman_item(item: dict, base_path: str = "") -> list[Route]:
    """Parse a single Postman item (request or folder)."""
    routes = []

    # Check if it's a request (has request field)
    if "request" in item:
        request = item["request"]
        method = parse_postman_method(request.get("method", "GET"))
        path, query_params = parse_postman_url(request.get("url", ""))

        # Combine with base path
        if base_path and not path.startswith(base_path):
            if path == "/":
                path = base_path
            else:
                path = base_path.rstrip("/") + path

        # Parameters from URL query
        parameters = []
        for key, values in query_params.items():
            parameters.append(Parameter(
                name=key,
                location=ParameterLocation.QUERY,
                required=False,
                schema={"type": "string", "enum": values},
                example=values[0] if values else None,
            ))

        # Parameters from URL path variables (Postman uses :param or {param})
        import re
        path_params = re.findall(r"[:{]([^}]+)[}]?", path)
        for param_name in path_params:
            # Convert {param} to {param} for our router
            path = path.replace(f":{param_name}", f"{{{param_name}}}")
            path = path.replace(f"{{{param_name}}}", f"{{{param_name}}}")
            parameters.append(Parameter(
                name=param_name,
                location=ParameterLocation.PATH,
                required=True,
                schema={"type": "string"},
            ))

        # Also detect numeric IDs in path segments (e.g., /users/42 -> /users/{id})
        # This handles cases where Postman collections have concrete IDs
        def replace_numeric_ids(p):
            # Replace UUIDs
            p = re.sub(
                r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                "/{id}",
                p,
                flags=re.IGNORECASE
            )
            # Replace numeric IDs (but not version numbers like v1, v2)
            p = re.sub(r"/(\d+)(?=/|$)", "/{id}", p)
            return p

        new_path = replace_numeric_ids(path)
        if new_path != path:
            # Add path parameter for the replaced ID
            parameters.append(Parameter(
                name="id",
                location=ParameterLocation.PATH,
                required=True,
                schema={"type": "string"},
            ))
            path = new_path

        # Headers
        for header in request.get("header", []):
            if not header.get("disabled"):
                parameters.append(parse_postman_header(header))

        # Body
        request_body = parse_postman_body(request.get("body"))

        # Responses from examples
        responses = extract_responses_from_examples(item)

        route = Route(
            path=path,
            method=method,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            summary=item.get("name", ""),
            description=item.get("description", "") if isinstance(item.get("description"), str) else "",
        )
        routes.append(route)

    # Check if it's a folder (has item array)
    elif "item" in item and isinstance(item["item"], list):
        # Folders in Postman are for organization, not part of the API path
        # Pass through base_path unchanged
        for sub_item in item["item"]:
            routes.extend(parse_postman_item(sub_item, base_path))

    return routes


def parse_postman(collection: dict[str, Any]) -> NormalizedApi:
    """Parse Postman Collection into normalized API model."""
    info = collection.get("info", {})
    title = info.get("name", "Postman API")
    version = info.get("version", "1.0.0") if isinstance(info.get("version"), str) else "1.0.0"
    description = info.get("description", "") if isinstance(info.get("description"), str) else ""

    routes = []
    for item in collection.get("item", []):
        routes.extend(parse_postman_item(item))

    return NormalizedApi(
        title=title,
        version=version,
        routes=routes,
        schemas={},
        servers=[{"url": ""}],
        base_path="",
    )


def parse_postman_file(file_path: str | Path) -> NormalizedApi:
    """Parse Postman Collection file into normalized API model."""
    collection = load_postman(file_path)

    if not is_postman_collection(collection):
        raise PostmanParseError("Not a valid Postman Collection format")

    return parse_postman(collection)