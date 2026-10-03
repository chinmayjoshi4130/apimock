"""Normalized internal API model for ApiMock."""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(str, Enum):
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class Parameter:
    name: str
    location: ParameterLocation
    required: bool = False
    schema: dict = field(default_factory=dict)
    example: Any = None
    examples: dict = field(default_factory=dict)
    default: Any = None
    enum: list = field(default_factory=list)


@dataclass
class RequestBody:
    content_type: str
    schema: dict = field(default_factory=dict)
    example: Any = None
    examples: dict = field(default_factory=dict)
    required: bool = False


@dataclass
class Response:
    status_code: int
    content_type: str
    schema: dict = field(default_factory=dict)
    example: Any = None
    examples: dict = field(default_factory=dict)


@dataclass
class Route:
    path: str
    method: HttpMethod
    parameters: list[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: list[Response] = field(default_factory=list)
    summary: str = ""
    description: str = ""
    operation_id: str = ""


@dataclass
class Schema:
    name: str
    schema: dict = field(default_factory=dict)


@dataclass
class NormalizedApi:
    title: str = ""
    version: str = ""
    routes: list[Route] = field(default_factory=list)
    schemas: dict[str, Schema] = field(default_factory=dict)
    servers: list[dict] = field(default_factory=list)
    base_path: str = ""