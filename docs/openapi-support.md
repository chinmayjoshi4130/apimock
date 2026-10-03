# OpenAPI Support

## Supported Versions

- **OpenAPI 3.0.x** ✅
- **OpenAPI 3.1.x** ✅ (partial)
- **Swagger 2.0** ❌ (explicitly unsupported)

## Supported Features

### Specification Format

| Format | Supported |
|--------|-----------|
| YAML | ✅ |
| JSON | ✅ |

### Core Components

| Feature | Supported | Notes |
|---------|-----------|-------|
| `info` | ✅ | Title, version, description |
| `servers` | ✅ | Base URL extraction |
| `paths` | ✅ | All HTTP methods |
| `components/schemas` | ✅ | Full schema support |
| `components/responses` | ⚠️ | Not yet implemented |
| `components/parameters` | ⚠️ | Not yet implemented |
| `components/examples` | ⚠️ | Not yet implemented |
| `security` | ❌ | Not implemented |
| `tags` | ⚠️ | Parsed but not used |
| `externalDocs` | ❌ | Not implemented |

### Paths & Operations

| Feature | Supported | Notes |
|---------|-----------|-------|
| Path parameters (`/users/{id}`) | ✅ | Extracted and validated |
| Query parameters | ✅ | With defaults, enums |
| Header parameters | ⚠️ | Parsed but not validated |
| Cookie parameters | ⚠️ | Parsed but not validated |
| Request body | ✅ | JSON content type |
| Multiple responses | ✅ | Prefers 2xx status codes |
| Response content types | ✅ | Defaults to application/json |
| Callbacks | ❌ | Not implemented |
| Deprecated operations | ⚠️ | Parsed but not used |

### Schema Support

| Feature | Supported | Notes |
|---------|-----------|-------|
| `type` (string, integer, number, boolean, array, object, null) | ✅ | |
| `format` | ✅ | email, uuid, date-time, date, time, uri, url, ipv4, ipv6, hostname, password, byte |
| `properties` | ✅ | |
| `required` | ✅ | |
| `items` (arrays) | ✅ | |
| `enum` | ✅ | |
| `default` | ✅ | |
| `example` | ✅ | Highest priority |
| `examples` | ✅ | Second priority |
| `minimum` / `maximum` | ✅ | Numbers |
| `exclusiveMinimum` / `exclusiveMaximum` | ✅ | Numbers |
| `minLength` / `maxLength` | ✅ | Strings |
| `pattern` | ⚠️ | Basic support |
| `minItems` / `maxItems` | ✅ | Arrays |
| `uniqueItems` | ✅ | Arrays |
| `additionalProperties` | ✅ | Objects |
| `$ref` (local) | ✅ | `#/components/schemas/Name` |
| `$ref` (external file) | ❌ | Not implemented |
| `$ref` (remote) | ❌ | Not implemented |

### Combinators (Not Yet Supported)

| Feature | Status |
|---------|--------|
| `allOf` | ❌ |
| `oneOf` | ❌ |
| `anyOf` | ❌ |
| `not` | ❌ |
| `discriminator` | ❌ |
| `nullable` | ❌ (use `type: [string, "null"]` in 3.1) |

### Format Details

#### String Formats

| Format | Example Output |
|--------|----------------|
| `email` | `user@example.com` |
| `uuid` | `550e8400-e29b-41d4-a716-446655440000` |
| `date-time` | `2024-01-15T10:30:00.000Z` |
| `date` | `2024-01-15` |
| `time` | `10:30:00` |
| `uri` / `url` | `https://example.com/path` |
| `ipv4` | `192.168.1.1` |
| `ipv6` | `2001:db8::1` |
| `hostname` | `example.com` |
| `password` | `x7K9mP2q` |
| `byte` | Base64 encoded binary |

## Limitations

1. **No external `$ref` resolution** - All references must be local (`#/components/schemas/...`)
2. **No schema composition** - `allOf`, `oneOf`, `anyOf` not supported
3. **No authentication** - Security schemes ignored
4. **Single response selection** - Always picks first 2xx response
5. **No request validation** - Request bodies not validated against schema
6. **No stateful behavior** - Each request independent (see future features)

## Validation

ApiMock validates:
- OpenAPI version is 3.x
- Required fields: `openapi`, `info`, `paths`
- `info` has `title` and `version`
- `paths` is an object
- Basic schema structure

## Error Messages

Errors include:
- Problem description
- Location in spec (path, method)
- Possible solution when obvious

Example:
```
Error: Unsupported OpenAPI version: 2.0. ApiMock currently supports OpenAPI 3.x.
```

## Migration from Swagger 2.0

Convert using tools like:
- `swagger2openapi` (npm)
- Online converters
- Manual conversion

Key changes:
- `swagger: "2.0"` → `openapi: "3.0.3"`
- `definitions` → `components.schemas`
- `parameters` → `components.parameters`
- `responses` → `components.responses`
- `securityDefinitions` → `components.securitySchemes`
- `produces`/`consumes` → `content` in request/response