# ApiMock Native Format

ApiMock includes its own native format that's simpler and more concise than OpenAPI, designed for quick mock API creation.

## File Extension

Use `.mock` extension (YAML or JSON):
- `api.mock` (YAML)
- `api.mock.json` (JSON)

## Quick Example

```yaml
# api.mock
info:
  title: "User API"
  version: "1.0.0"

schemas:
  User: "object{id:integer,name:string,email:string:email}"
  UserInput: "object{name:string!,email:string:email!}"

endpoints:
  - "GET /users {param:limit=integer:1-100=20, resp:200=array<User>}"
  - "POST /users {body:UserInput, resp:201=User}"
  - "GET /users/{id} {resp:200=User, resp:404=Error}"
```

Run with:
```bash
apimock api.mock --seed 42
```

## Format Structure

```yaml
info:
  title: "API Title"        # Required
  version: "1.0.0"          # Required
  server: "http://localhost:8080"  # Optional

schemas:                    # Reusable type definitions
  TypeName: "type_spec"

endpoints:                  # API endpoints (or use 'routes')
  - endpoint_definition
```

## Type Specifications

### Primitive Types

| Spec | Schema |
|------|--------|
| `string` | `{"type": "string"}` |
| `string:email` | `{"type": "string", "format": "email"}` |
| `string:uuid` | `{"type": "string", "format": "uuid"}` |
| `string:date-time` | `{"type": "string", "format": "date-time"}` |
| `string:enum(a,b,c)` | `{"type": "string", "enum": ["a","b","c"]}` |
| `string=default` | `{"type": "string", "default": "default"}` |
| `integer` | `{"type": "integer"}` |
| `integer:1-100` | `{"type": "integer", "minimum": 1, "maximum": 100}` |
| `number` | `{"type": "number"}` |
| `number:0.0-1.0` | `{"type": "number", "minimum": 0, "maximum": 1}` |
| `boolean` | `{"type": "boolean"}` |
| `boolean=true` | `{"type": "boolean", "default": true}` |

### Array Types

| Spec | Schema |
|------|--------|
| `array<string>` | `{"type": "array", "items": {"type": "string"}}` |
| `array<string:email>` | `{"type": "array", "items": {"type": "string", "format": "email"}}` |
| `array<User>` | `{"type": "array", "items": {"type": "User"}}` |

### Object Types

```yaml
# Inline object
User: "object{id:integer,name:string,email:string:email}"

# With required fields (use !)
UserInput: "object{name:string!,email:string:email!}"

# Full object syntax (for complex cases)
User:
  type: object
  properties:
    id: "integer:1-999999"
    name: "string"
    email: "string:email"
    role: "string:enum(admin,user,guest)"
  required: ["id", "name", "email"]
```

### Named References

```yaml
schemas:
  User: "object{id:integer,name:string}"
  UserList: "array<User>"  # References User schema
```

## Endpoint Definitions

### String Format (Concise)

```
METHOD /path {inline_spec}
```

Inline spec components (comma-separated):
- `param:name=type_spec` - Query parameter
- `body:type_spec` - Request body
- `resp:code=type_spec` - Response (can have multiple)

```yaml
endpoints:
  - "GET /users {param:limit=integer:1-100=20, resp:200=array<User>}"
  - "POST /users {body:UserInput, resp:201=User, resp:400=Error}"
  - "GET /users/{id} {resp:200=User, resp:404=Error}"
  - "DELETE /users/{id} {resp:204=null}"
```

### Object Format (Explicit)

```yaml
endpoints:
  - method: GET
    path: "/users"
    params:
      limit: "integer:1-100=20"
      offset: "integer=0"
    responses:
      200: "array<User>"
  
  - method: POST
    path: "/users"
    body: "UserInput"
    responses:
      201: "User"
      400: "Error"
  
  - method: GET
    path: "/users/{id}"
    params:
      id: "integer:1-999999"
    responses:
      200: "User"
      404: "Error"
```

## Path Parameters

Automatically extracted from path:
- `/users/{id}` → path parameter `id`
- `/users/{userId}/posts/{postId}` → path parameters `userId`, `postId`

Override in params:
```yaml
params:
  id: "integer:1-999999"  # Custom type for path param
```

## Response Codes

Default response is `200` with `{"type": "object"}`. Specify custom:

```yaml
responses:
  201: "User"      # Created
  204: "null"      # No content
  400: "Error"     # Bad request
  404: "Error"     # Not found
  500: "Error"     # Server error
```

## Running

```bash
# Auto-detect format
apimock api.mock

# Explicit format
apimock api.mock --format apimock

# With options
apimock api.mock --port 9000 --seed 42 --delay 100
```

## Example: Complete CRUD API

```yaml
info:
  title: "Task Manager"
  version: "1.0.0"

schemas:
  TaskId: "integer:1-999999"
  TaskStatus: "string:enum(pending,in_progress,done)"
  Task:
    type: object
    properties:
      id: "TaskId"
      title: "string"
      description: "string"
      status: "TaskStatus"
      created_at: "string:date-time"
      due_date: "string:date"
    required: ["id", "title"]
  TaskInput:
    type: object
    properties:
      title: "string"
      description: "string"
      status: "TaskStatus=pending"
      due_date: "string:date"
    required: ["title"]

endpoints:
  - "GET /tasks {param:status=TaskStatus, param:limit=integer:1-100=20, resp:200=array<Task>}"
  - "POST /tasks {body:TaskInput, resp:201=Task}"
  - "GET /tasks/{id} {resp:200=Task, resp:404=Error}"
  - "PATCH /tasks/{id} {body:TaskInput, resp:200=Task, resp:404=Error}"
  - "DELETE /tasks/{id} {resp:204=null, resp:404=Error}"
```

## Comparison with OpenAPI

| Feature | OpenAPI | ApiMock Native |
|---------|---------|----------------|
| Verbosity | High | Low |
| Learning curve | Steep | Gentle |
| Schema reuse | `$ref` | Named types |
| Constraints | Full | Common ones |
| Enum | Full | `enum(a,b,c)` |
| Required fields | `required: []` | `!` suffix |
| Arrays | `items: {}` | `array<Type>` |
| Formats | Many | Common ones |
| Examples | `example:` | `=default` |

## When to Use

- **ApiMock Native**: Quick prototyping, simple APIs, team unfamiliar with OpenAPI
- **OpenAPI**: Production APIs, existing OpenAPI specs, complex validation needs
- **Postman/HAR**: Converting existing collections/captures