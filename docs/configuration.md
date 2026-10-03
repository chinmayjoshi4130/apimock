# Configuration

## CLI Options

All configuration is done via command-line flags. See [CLI Reference](cli-reference.md) for full list.

## Server Configuration

### Host Binding

```bash
# Local only (default)
apimock openapi.yaml --host 127.0.0.1

# All interfaces (Docker, LAN access)
apimock openapi.yaml --host 0.0.0.0

# Specific interface
apimock openapi.yaml --host 192.168.1.100
```

### Port Selection

```bash
# Default port
apimock openapi.yaml --port 8080

# Custom port
apimock openapi.yaml --port 9000

# Random available port (use --json to get actual port)
apimock openapi.yaml --port 0 --json
```

## Mock Behavior

### Deterministic Data

```bash
# Fixed seed
apimock openapi.yaml --seed 42

# Random seed (default behavior)
apimock openapi.yaml
```

### Latency Simulation

```bash
# 100ms delay
apimock openapi.yaml --delay 100

# 1 second delay
apimock openapi.yaml --delay 1000
```

## Output Control

### Request Logging

```bash
# Default: log requests
apimock openapi.yaml

# Verbose: detailed timing
apimock openapi.yaml --verbose

# Quiet: no request logs
apimock openapi.yaml --quiet
```

### JSON Output

```bash
# Machine-readable startup info
apimock openapi.yaml --json
# {"host": "127.0.0.1", "port": 8080, "routes": 5, "title": "API", "version": "1.0.0"}
```

## Environment Variables

Currently not supported. All configuration via CLI.

## Configuration File (Future)

Planned for future version:

```yaml
# apimock.yaml (not yet implemented)
host: 0.0.0.0
port: 8080
seed: 42
delay: 0
verbose: false
```

## Profiles (Future)

```bash
# Not yet implemented
apimock openapi.yaml --profile development
apimock openapi.yaml --profile slow
apimock openapi.yaml --profile errors
```

## Docker Usage

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY openapi.yaml .
RUN pip install apimock
EXPOSE 8080
CMD ["apimock", "openapi.yaml", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t my-mock-api .
docker run -p 8080:8080 my-mock-api

# With seed
docker run -p 8080:8080 my-mock-api --seed 42
```

## Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apimock
spec:
  replicas: 1
  selector:
    matchLabels:
      app: apimock
  template:
    metadata:
      labels:
        app: apimock
    spec:
      containers:
      - name: apimock
        image: my-mock-api
        ports:
        - containerPort: 8080
        args: ["openapi.yaml", "--host", "0.0.0.0", "--seed", "42"]
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start mock API
        run: |
          apimock openapi.yaml --port 8080 --seed 42 &
          sleep 2
      - name: Run tests
        run: pytest tests/ --api-url=http://localhost:8080
```

### GitLab CI

```yaml
# .gitlab-ci.yml
test:
  script:
    - pip install apimock
    - apimock openapi.yaml --port 8080 --seed 42 &
    - sleep 2
    - pytest tests/
```

## Performance Tuning

### For High Traffic

```bash
# Increase worker processes (future feature)
apimock openapi.yaml --workers 4
```

### Memory Usage

- Minimal memory footprint
- No database or external dependencies
- Schemas cached in memory
- Generator state per request