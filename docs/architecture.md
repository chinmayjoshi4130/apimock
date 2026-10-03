# Architecture

## Overview

```
┌─────────────┐
│  OpenAPI    │
│  Spec File  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Parser    │  (parser/openapi.py)
│  - Load     │
│  - Validate │
│  - Resolve  │
│  - Normalize│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Normalized Model   │  (parser/models.py)
│  - Routes           │
│  - Parameters       │
│  - Request/Response │
│  - Schemas          │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌─────────┐ ┌──────────┐
│ Router  │ │Generator │  (server/routes.py) (mock/generator.py)
│ - Match │ │ - Types  │
│ - Params│ │ - Formats│
└────┬────┘ │ - Constraints
     │      │ - Seed    │
     │      └────┬──────┘
     │           │
     ▼           ▼
┌─────────────────────┐
│    HTTP Server      │  (server/app.py)
│  - aiohttp          │
│  - Request handling │
│  - Response building│
│  - Logging          │
└─────────────────────┘
```

## Module Structure

### `apimock/parser/`

**`models.py`** - Normalized internal data model
- `HttpMethod` - Enum of supported methods
- `ParameterLocation` - Enum of parameter locations
- `Parameter` - Path, query, header, cookie params
- `RequestBody` - Request body with schema
- `Response` - Response with status, schema, examples
- `Route` - Complete route definition
- `Schema` - Named schema reference
- `NormalizedApi` - Complete parsed API

**`openapi.py`** - OpenAPI 3.x parser
- `load_openapi()` - Load YAML/JSON file
- `validate_openapi()` - Validate spec structure
- `resolve_ref()` - Resolve local `$ref`
- `parse_schema()` - Parse schema with ref resolution
- `parse_parameters()` - Parse parameters
- `parse_request_body()` - Parse requestBody
- `parse_responses()` - Parse responses
- `parse_path()` - Parse single path
- `parse_schemas()` - Parse all component schemas
- `parse_openapi()` - Main entry point

### `apimock/mock/`

**`schema.py`** - Schema utilities
- `resolve_refs()` - Recursive ref resolution
- `get_schema_type()` - Extract type with default
- `get_example_value()` - Get explicit example
- `get_default_value()` - Get default
- `get_enum_values()` - Get enum array
- `is_required_property()` - Check required

**`generator.py`** - Mock data generator
- `MockGenerator` class with:
  - `generate()` - Main entry point
  - `_generate_by_type()` - Dispatch by type
  - `_generate_string()` - String with formats
  - `_generate_integer()` - Integer with constraints
  - `_generate_number()` - Float with constraints
  - `_generate_array()` - Array with items
  - `_generate_object()` - Object with properties
  - `generate_response()` - Route-specific generation
- Deterministic via `random.Random(seed)` + `Faker.seed_instance(seed)`

### `apimock/server/`

**`routes.py`** - HTTP routing
- `Router` class with:
  - `_compile_routes()` - Convert paths to regex
  - `_compile_path_pattern()` - OpenAPI path → regex
  - `match()` - Match method + path + query
  - `_parse_query()` - Parse query string
  - `get_all_routes()` - List all routes
- `RouteMatch` - Match result with params

**`app.py`** - HTTP server
- `MockServer` class with:
  - `print_startup_info()` - Pretty startup output
  - `_handle_request()` - Main request handler
  - `_not_found_response()` - 404 handler
  - `_log_request()` - Request logging
  - `start()` - Async server start
  - `run()` - Sync entry point
- Uses aiohttp for async HTTP

### `apimock/config.py`

- `Config` dataclass - All CLI options
- `create_config()` - Factory function

### `apimock/cli.py`

- Click-based CLI
- `main()` - Entry point
- `run_server()` - Orchestrate parse → generate → serve

## Data Flow

```
Request: GET /users/42
                │
                ▼
         ┌─────────────┐
         │   Router    │
         │  match()    │
         └──────┬──────┘
                │ RouteMatch
                ▼
         ┌─────────────┐
         │  Generator  │
         │ generate()  │
         └──────┬──────┘
                │ Mock Data
                ▼
         ┌─────────────┐
         │   Server    │
         │  Response   │
         └─────────────┘
```

## Key Design Decisions

### 1. Normalized Internal Model
- Decouples parser from server/generator
- Enables testing each component independently
- Single source of truth for routes/schemas

### 2. Deterministic Generation
- Seed passed to both `random.Random` and `Faker`
- Same seed = same output across runs
- Critical for testing and reproducibility

### 3. Priority-Based Value Selection
```
example → examples → default → enum → generated
```
- Gives schema authors control
- Falls back to sensible generated values

### 4. Local `$ref` Resolution Only
- Resolves `#/components/schemas/Name` at parse time
- Pre-resolves all schemas for generator
- External/remote refs not supported (v1)

### 5. 2xx Response Preference
- Always picks first 2xx status code
- Matches typical "success" expectation
- Future: explicit status selection

### 6. aiohttp for Async Server
- High performance async I/O
- Native WebSocket support (future)
- Easy middleware integration

## Extension Points

### Adding New Formats
```python
# In generator.py _generate_string()
elif format_ == "custom-format":
    return self.faker.custom_method()
```

### Adding New Types
```python
# In generator.py _generate_by_type()
elif schema_type == "custom-type":
    return self._generate_custom(schema)
```

### Custom Response Selection
```python
# In app.py _handle_request()
# Check headers for X-ApiMock-Status
status_header = request.headers.get("X-ApiMock-Status")
if status_header:
    status_code = int(status_header)
```

## Testing Strategy

- **Unit tests** - Each module tested in isolation
- **Parser tests** - Spec loading, validation, normalization
- **Generator tests** - Type generation, constraints, determinism
- **Router tests** - Path matching, param extraction
- **Integration tests** - Full request/response cycle
- **CLI tests** - Command parsing, output formats

## Performance Considerations

- Schemas pre-resolved at startup
- Route patterns compiled once
- Generator stateless (except RNG)
- No I/O in request path
- Minimal allocations per request

## Future Architecture

### Planned Extensions

1. **Stateful Mode** - In-memory data store
2. **Proxy Mode** - Forward unmatched to real API
3. **Middleware Pipeline** - Custom request/response processing
4. **WebSocket Support** - Real-time mock APIs
5. **Plugin System** - Custom generators, validators
6. **External Refs** - File/HTTP `$ref` resolution