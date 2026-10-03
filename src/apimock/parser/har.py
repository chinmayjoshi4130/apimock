"""HAR (HTTP Archive) parser for ApiMock."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

from apimock.parser.models import (
    NormalizedApi,
    Route,
    Parameter,
    RequestBody,
    Response,
    ParameterLocation,
    HttpMethod,
)
from apimock.parser.openapi import OpenApiParseError


class HARParseError(OpenApiParseError):
    """Raised when HAR file cannot be parsed."""
    pass


def load_har(file_path: str | Path) -> dict[str, Any]:
    """Load HAR file from JSON."""
    path = Path(file_path)
    if not path.exists():
        raise HARParseError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise HARParseError(f"Failed to parse JSON: {e}")


def is_har(data: dict[str, Any]) -> bool:
    """Check if data is a HAR file."""
    return (
        "log" in data
        and "entries" in data.get("log", {})
        and isinstance(data["log"].get("entries"), list)
    )


def parse_har_url(url: str) -> tuple[str, dict[str, list[str]]]:
    """Parse URL into path and query parameters."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    query = parse_qs(parsed.query, keep_blank_values=True)
    return path, query


def normalize_path(path: str) -> str:
    """Normalize path by replacing numeric IDs with parameters."""
    import re
    # Replace UUIDs
    path = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "/{id}",
        path,
        flags=re.IGNORECASE
    )
    # Replace numeric IDs
    path = re.sub(r"/(\d+)(?=/|$)", "/{id}", path)
    # Replace email-like segments
    path = re.sub(r"/[^/]+@[^/]+\.[^/]+(?=/|$)", "/{email}", path)
    return path


def extract_har_headers(headers: list[dict]) -> dict[str, str]:
    """Extract headers from HAR format."""
    result = {}
    for h in headers:
        name = h.get("name", "")
        value = h.get("value", "")
        if name:
            result[name.lower()] = value
    return result


def parse_har_request_body(request: dict) -> RequestBody | None:
    """Parse HAR request body."""
    post_data = request.get("postData")
    if not post_data:
        return None

    mime_type = post_data.get("mimeType", "application/json")
    text = post_data.get("text", "")

    # Try to parse JSON
    schema = {"type": "object"}
    example = None
    if text:
        try:
            parsed = json.loads(text)
            schema = {"type": "object", "example": parsed}
            example = parsed
        except json.JSONDecodeError:
            schema = {"type": "string"}
            example = text

    return RequestBody(
        content_type=mime_type,
        schema=schema,
        example=example,
    )


def parse_har_response(response: dict) -> Response:
    """Parse HAR response."""
    status = response.get("status", 200)
    headers = extract_har_headers(response.get("headers", []))

    content_type = headers.get("content-type", "application/json")
    if ";" in content_type:
        content_type = content_type.split(";")[0].strip()

    content = response.get("content", {})
    text = content.get("text", "")
    encoding = content.get("encoding")

    # Handle base64 encoded content
    if encoding == "base64" and text:
        import base64
        try:
            text = base64.b64decode(text).decode("utf-8")
        except Exception:
            pass

    # Try to parse JSON
    schema = {"type": "object"}
    example = None
    if text:
        try:
            parsed = json.loads(text)
            schema = {"type": "object", "example": parsed}
            example = parsed
        except json.JSONDecodeError:
            schema = {"type": "string"}
            example = text

    return Response(
        status_code=status,
        content_type=content_type,
        schema=schema,
        example=example,
    )


def group_har_entries(entries: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Group HAR entries by normalized path and method."""
    grouped = defaultdict(list)

    for entry in entries:
        request = entry.get("request", {})
        method = request.get("method", "GET").upper()
        url = request.get("url", "")
        path, _ = parse_har_url(url)
        normalized_path = normalize_path(path)
        grouped[(method, normalized_path)].append(entry)

    return grouped


def merge_responses(responses: list[Response]) -> list[Response]:
    """Merge multiple responses for same route, keeping unique status codes."""
    seen = {}
    for resp in responses:
        if resp.status_code not in seen:
            seen[resp.status_code] = resp
        else:
            # Prefer response with example
            if resp.example is not None and seen[resp.status_code].example is None:
                seen[resp.status_code] = resp
    return sorted(seen.values(), key=lambda r: r.status_code)


def parse_har_entries(entries: list[dict]) -> list[Route]:
    """Parse HAR entries into routes."""
    grouped = group_har_entries(entries)
    routes = []

    for (method_str, path), entry_group in grouped.items():
        method = HttpMethod(method_str) if method_str in HttpMethod.__members__ else HttpMethod.GET

        # Use first entry for request details
        first_entry = entry_group[0]
        request = first_entry.get("request", {})

        # Parse query parameters from first entry
        url = request.get("url", "")
        _, query_params = parse_har_url(url)

        parameters = []
        for key, values in query_params.items():
            parameters.append(Parameter(
                name=key,
                location=ParameterLocation.QUERY,
                required=False,
                schema={"type": "string", "enum": list(set(values))},
                example=values[0] if values else None,
            ))

        # Extract path parameters from normalized path
        import re
        path_params = re.findall(r"\{([^}]+)\}", path)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                location=ParameterLocation.PATH,
                required=True,
                schema={"type": "string"},
            ))

        # Headers
        headers = extract_har_headers(request.get("headers", []))
        # Filter out common automatic headers (case-insensitive)
        filtered_headers = {
            "content-type", "content-length", "host",
            "accept", "user-agent", "accept-encoding",
            "accept-language", "connection", "cookie"
        }
        for name, value in headers.items():
            if name.lower() not in filtered_headers:
                parameters.append(Parameter(
                    name=name,
                    location=ParameterLocation.HEADER,
                    required=False,
                    schema={"type": "string"},
                    example=value,
                ))

        # Request body
        request_body = parse_har_request_body(request)

        # Responses - collect from all entries
        all_responses = []
        for entry in entry_group:
            response = entry.get("response", {})
            all_responses.append(parse_har_response(response))

        responses = merge_responses(all_responses)

        route = Route(
            path=path,
            method=method,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            summary=f"{method} {path}",
        )
        routes.append(route)

    return routes


def parse_har(har: dict[str, Any]) -> NormalizedApi:
    """Parse HAR into normalized API model."""
    log = har.get("log", {})
    version = log.get("version", "1.0")
    creator = log.get("creator", {})
    title = creator.get("name", "HAR API")
    creator_version = creator.get("version", "1.0")

    entries = log.get("entries", [])
    routes = parse_har_entries(entries)

    return NormalizedApi(
        title=f"{title} (from HAR)",
        version=creator_version,
        routes=routes,
        schemas={},
        servers=[{"url": ""}],
        base_path="",
    )


def parse_har_file(file_path: str | Path) -> NormalizedApi:
    """Parse HAR file into normalized API model."""
    har = load_har(file_path)

    if not is_har(har):
        raise HARParseError("Not a valid HAR format")

    return parse_har(har)