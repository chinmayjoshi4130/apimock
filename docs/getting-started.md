# Getting Started

## Prerequisites

- Python 3.10+
- An OpenAPI 3.x specification file (YAML or JSON)

## Installation

### From PyPI

```bash
pip install apimock
```

### From Source

```bash
git clone https://github.com/example/apimock
cd apimock
pip install -e .
```

## Your First Mock Server

### 1. Create an OpenAPI Specification

Create a file named `openapi.yaml`:

```yaml
openapi: 3.0.3
info:
  title: User API
  version: 1.0.0
servers:
  - url: http://localhost:8080
paths:
  /users:
    get:
      summary: List all users
      responses:
        "200":
          description: A list of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/User"
    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserInput"
      responses:
        "201":
          description: User created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
  /users/{id}:
    get:
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: A single user
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "404":
          description: User not found
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
    UserInput:
      type: object
      required:
        - name
      properties:
        name:
          type: string
        email:
          type: string
          format: email
```

### 2. Start the Mock Server

```bash
apimock openapi.yaml
```

Output:

```
ApiMock v0.1.0

Spec:   User API v1.0.0
Host:   127.0.0.1
Port:   8080

Routes:
  GET     /users
  POST    /users
  GET     /users/{id}

Mock server ready at http://127.0.0.1:8080
```

### 3. Test the API

```bash
# List users
curl http://127.0.0.1:8080/users

# Get a specific user
curl http://127.0.0.1:8080/users/42

# Create a user
curl -X POST http://127.0.0.1:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

## Deterministic Data

Use `--seed` for reproducible mock data:

```bash
apimock openapi.yaml --seed 42
```

Same seed + same spec = same mock data every time.

## Next Steps

- [CLI Reference](cli-reference.md) - All command-line options
- [OpenAPI Support](openapi-support.md) - Supported OpenAPI features
- [Mock Data Generation](mock-data-generation.md) - How mock data is generated
- [Examples](examples.md) - More example specifications