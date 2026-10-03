# ApiMock

A developer-focused local API mocking tool that generates a working HTTP mock server directly from an OpenAPI specification.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Basic usage
apimock openapi.yaml

# Custom host and port
apimock openapi.yaml --host 0.0.0.0 --port 9000
apimock openapi.yaml -H 0.0.0.0 -p 9000

# Deterministic mock data with seed
apimock openapi.yaml --seed 42

# Artificial delay (milliseconds)
apimock openapi.yaml --delay 500

# Quiet mode (no request logging)
apimock openapi.yaml --quiet

# Verbose mode
apimock openapi.yaml --verbose

# Machine-readable JSON output
apimock openapi.yaml --json
```

## Features

- **OpenAPI 3.x support** - Load YAML or JSON specifications
- **Automatic route discovery** - Discovers all paths, methods, parameters, and responses
- **Realistic mock data** - Generates data from schemas with support for:
  - Primitive types (string, integer, number, boolean)
  - Objects and arrays
  - Formats (email, uuid, date-time, uri, etc.)
  - Enums, defaults, examples
  - Min/max constraints
- **Deterministic generation** - Use `--seed` for reproducible mock data
- **$ref resolution** - Resolves local schema references
- **Configurable server** - Custom host, port, delay
- **Request logging** - See incoming requests with response times
- **Proper HTTP status codes** - 200, 201, 204, 404, etc.

## Example

Given an OpenAPI spec like:

```yaml
openapi: 3.0.3
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/User"
components:
  schemas:
    User:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
```

Run:
```bash
apimock openapi.yaml --seed 42
```

Request:
```bash
curl http://127.0.0.1:8080/users
```

Response:
```json
[
  {
    "id": 42,
    "name": "Alice",
    "email": "alice@example.com"
  },
  {
    "id": 43,
    "name": "Bob",
    "email": "bob@example.com"
  }
]
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--host` | `-H` | Host to bind to (default: 127.0.0.1) |
| `--port` | `-p` | Port to bind to (default: 8080) |
| `--seed` | | Random seed for deterministic generation |
| `--delay` | | Artificial delay in milliseconds |
| `--verbose` | `-v` | Verbose output |
| `--quiet` | `-q` | Quiet output (no request logging) |
| `--watch` | `-w` | Watch spec file for changes (not yet implemented) |
| `--json` | | Output machine-readable JSON |
| `--version` | | Show version |
| `--help` | | Show help |

## Architecture

```
src/apimock/
├── cli.py           # CLI entry point
├── config.py        # Configuration
├── parser/
│   ├── openapi.py   # OpenAPI parsing and validation
│   └── models.py    # Normalized internal API model
├── mock/
│   ├── generator.py # Mock data generation
│   └── schema.py    # Schema utilities
└── server/
    ├── app.py       # HTTP server (aiohttp)
    └── routes.py    # Request routing
```

## License

MIT