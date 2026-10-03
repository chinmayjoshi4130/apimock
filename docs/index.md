# ApiMock Documentation

## Table of Contents

- [Getting Started](getting-started.md)
- [CLI Reference](cli-reference.md)
- [OpenAPI Support](openapi-support.md)
- [ApiMock Native Format](apimock-format.md)
- [Postman Collection Support](postman-support.md)
- [HAR Support](har-support.md)
- [Mock Data Generation](mock-data-generation.md)
- [Configuration](configuration.md)
- [Examples](examples.md)
- [Architecture](architecture.md)
- [Contributing](contributing.md)

## Quick Links

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Common Options](#common-options)

## Installation

```bash
pip install apimock
```

Or from source:

```bash
git clone https://github.com/example/apimock
cd apimock
pip install -e .
```

## Basic Usage

```bash
# Start mock server from OpenAPI spec
apimock openapi.yaml

# From ApiMock native format
apimock api.mock

# From Postman Collection
apimock collection.json

# From HAR file
apimock archive.har

# With custom port and deterministic data
apimock openapi.yaml --port 9000 --seed 42
```

## Common Options

| Option | Description |
|--------|-------------|
| `-H, --host` | Bind host (default: 127.0.0.1) |
| `-p, --port` | Bind port (default: 8080) |
| `--seed` | Random seed for deterministic generation |
| `--delay` | Artificial latency in milliseconds |
| `-v, --verbose` | Verbose request logging |
| `-q, --quiet` | Suppress request logging |
| `--json` | Machine-readable JSON output |
| `--format` | Specification format (auto, openapi, postman, har, apimock) |