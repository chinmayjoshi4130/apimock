# ApiMock

[![License](https://img.shields.io/github/license/chinmayjoshi4130/apimock)](LICENSE)

A developer-focused local API mocking tool that generates a working HTTP mock server directly from **OpenAPI**, **Postman Collection**, **HAR**, or **ApiMock native format** specifications.

**Author:** [Chinmay Joshi](https://github.com/chinmayjoshi4130)

---

## Installation

```bash
# Clone and install locally (not on PyPI)
git clone https://github.com/chinmayjoshi4130/apimock
cd apimock
pip install -e .

# Or install without editable mode
pip install .
```

---

## Quick Start

```bash
# From OpenAPI spec
apimock openapi.yaml

# From Postman Collection
apimock collection.json

# From HAR file (browser network capture)
apimock archive.har

# From ApiMock native format (simpler, concise)
apimock api.mock

# With options
apimock openapi.yaml --port 9000 --seed 42 --delay 100
```

---

## Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **OpenAPI 3.x** | `.yaml`, `.yml`, `.json` | Full OpenAPI 3.x support with `$ref` resolution |
| **Postman Collection** | `.json` | Postman v2.1 collections with examples |
| **HAR** | `.har` | HTTP Archive from browser dev tools |
| **ApiMock Native** | `.mock`, `.mock.yaml`, `.mock.json` | Concise custom format |

---

## Features

- 🚀 **Zero-config** - `apimock spec.yaml` just works
- 🎯 **Multi-format** - OpenAPI, Postman, HAR, native
- 🔄 **Deterministic** - `--seed` for reproducible mock data
- ⚡ **Fast** - Async aiohttp server, minimal overhead
- 📝 **Request logging** - See all requests with timing
- 🎭 **Realistic data** - Faker-powered generation with formats
- 🔗 **$ref resolution** - Local references fully supported
- 📦 **Schema reuse** - Named types in native format
- 🐳 **Docker ready** - `docker run -p 8080:8080 apimock spec.yaml`

---

## Usage Examples

### Basic Usage

```bash
# Default: 127.0.0.1:8080
apimock openapi.yaml

# Custom host/port
apimock openapi.yaml --host 0.0.0.0 --port 9000
apimock openapi.yaml -H 0.0.0.0 -p 9000

# Deterministic mock data (same seed = same data)
apimock openapi.yaml --seed 42

# Simulate network latency
apimock openapi.yaml --delay 500

# Output modes
apimock openapi.yaml --verbose    # Log all requests
apimock openapi.yaml --quiet      # Suppress request logs
apimock openapi.yaml --json       # Machine-readable startup info
```

### Format-Specific

```bash
# Auto-detect (default)
apimock api-spec.yaml

# Explicit format
apimock collection.json --format postman
apimock archive.har --format har
apimock api.mock --format apimock
```

### CI/CD Integration

```bash
# Start mock server in background, capture port
PORT=$(apimock openapi.yaml --port 0 --json | jq -r .port)

# Run tests against mock
pytest tests/ --api-base-url=http://localhost:$PORT
```

---

## ApiMock Native Format

A simpler, more concise alternative to OpenAPI:

```yaml
# api.mock
info:
  title: "User API"
  version: "1.0.0"

schemas:
  UserId: "integer:1-999999"
  Email: "string:email"
  UserRole: "string:enum(admin,user,guest)"
  User: "object{id:UserId,name:string,email:Email,role:UserRole}"
  UserInput: "object{name:string!,email:Email!}"

endpoints:
  - "GET /users {param:limit=integer:1-100=20, resp:200=array<User>}"
  - "POST /users {body:UserInput, resp:201=User}"
  - "GET /users/{id} {resp:200=User, resp:404=Error}"
```

Run: `apimock api.mock --seed 42`

[Full documentation →](docs/apimock-format.md)

---

## Mock Data Generation

ApiMock generates realistic data from schemas:

| Schema | Example Output |
|--------|----------------|
| `string:email` | `"user@example.com"` |
| `string:uuid` | `"550e8400-e29b-41d4-a716-446655440000"` |
| `integer:1-100` | `42` |
| `array<User>` | `[{"id": 1, "name": "Alice"}, ...]` |
| `object{name:string!,email:string:email}` | `{"name": "Bob", "email": "bob@example.com"}` |

**Priority:** `example` → `examples` → `default` → `enum` → generated

---

## Options Reference

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--host` | `-H` | `127.0.0.1` | Bind host address |
| `--port` | `-p` | `8080` | Bind port (0 = random) |
| `--seed` | | random | Random seed for deterministic data |
| `--delay` | | `0` | Artificial delay (ms) |
| `--verbose` | `-v` | false | Verbose request logging |
| `--quiet` | `-q` | false | Suppress request logs |
| `--json` | | false | Machine-readable JSON output |
| `--format` | | `auto` | Spec format: `auto`, `openapi`, `postman`, `har`, `apimock` |
| `--version` | | | Show version |
| `--help` | | | Show help |

---

## Documentation

- [Getting Started](docs/getting-started.md)
- [CLI Reference](docs/cli-reference.md)
- [OpenAPI Support](docs/openapi-support.md)
- [ApiMock Native Format](docs/apimock-format.md)
- [Postman Collection Support](docs/postman-support.md)
- [HAR Support](docs/har-support.md)
- [Mock Data Generation](docs/mock-data-generation.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Examples](docs/examples.md)
- [Contributing](docs/contributing.md)

---

## Examples

```bash
# Run example specs
apimock examples/crud-api.yaml --seed 42
apimock examples/ecommerce.yaml --seed 123 --port 9000
apimock examples/blog.yaml --seed 999 --delay 100
apimock examples/postman-collection.json
apimock examples/archive.har
apimock examples/api.mock
```

---

## Development

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest -v

# Format & lint
black src/ tests/
ruff check src/ tests/
mypy src/

# Build
pip install build && python -m build
```

---

## License

**MIT License** - see [LICENSE](LICENSE) for details.

```
MIT License

Copyright (c) 2024 Chinmay Joshi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Links

- **Repository:** https://github.com/chinmayjoshi4130/apimock
- **Issues:** https://github.com/chinmayjoshi4130/apimock/issues
- **Author:** [Chinmay Joshi](https://github.com/chinmayjoshi4130)

---

*Built with ❤️ for developers who need realistic APIs without the backend.*