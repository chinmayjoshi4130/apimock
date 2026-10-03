# CLI Reference

## Synopsis

```bash
apimock [OPTIONS] SPEC_FILE
```

## Arguments

| Argument | Description |
|----------|-------------|
| `SPEC_FILE` | Path to OpenAPI specification (YAML or JSON) |

## Options

### Server Configuration

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--host` | `-H` | STRING | `127.0.0.1` | Host address to bind to |
| `--port` | `-p` | INTEGER | `8080` | Port number to bind to |

### Mock Data Generation

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--seed` | | INTEGER | random | Random seed for deterministic generation |
| `--delay` | | INTEGER | `0` | Artificial response delay in milliseconds |

### Output Control

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--verbose` | `-v` | FLAG | false | Enable verbose request logging |
| `--quiet` | `-q` | FLAG | false | Disable request logging |
| `--json` | | FLAG | false | Output machine-readable JSON |

### Utility

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--watch` | `-w` | FLAG | false | Watch spec file for changes (not implemented) |
| `--version` | | FLAG | false | Show version and exit |
| `--help` | | FLAG | false | Show help message and exit |

## Examples

### Basic Usage

```bash
# Start with defaults
apimock openapi.yaml

# Custom host and port
apimock openapi.yaml --host 0.0.0.0 --port 9000
apimock openapi.yaml -H 0.0.0.0 -p 9000
```

### Deterministic Generation

```bash
# Fixed seed for reproducible data
apimock openapi.yaml --seed 42

# Different seeds produce different data
apimock openapi.yaml --seed 123
apimock openapi.yaml --seed 456
```

### Latency Simulation

```bash
# Fixed 500ms delay
apimock openapi.yaml --delay 500

# Combined with seed
apimock openapi.yaml --seed 42 --delay 100
```

### Output Modes

```bash
# Verbose logging (shows all requests)
apimock openapi.yaml --verbose

# Quiet mode (no request logs)
apimock openapi.yaml --quiet

# JSON output for scripting
apimock openapi.yaml --json
# Output: {"host": "127.0.0.1", "port": 8080, "routes": 5, "title": "API", "version": "1.0.0"}
```

### CI/CD Integration

```bash
# Start in background, get port from JSON
PORT=$(apimock openapi.yaml --json --port 0 | jq -r .port)

# Run tests against mock
pytest tests/ --api-base-url=http://localhost:$PORT
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (invalid spec, port in use, etc.) |
| `130` | Interrupted (Ctrl+C) |

## Environment Variables

Currently no environment variables are supported. All configuration is via CLI flags.