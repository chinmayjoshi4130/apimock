# Mock Data Generation

## Overview

ApiMock generates realistic mock data from OpenAPI schemas. The generation is deterministic when a seed is provided, making it ideal for testing, screenshots, and CI environments.

## Generation Priority

Values are selected in this order:

1. **`example`** - Explicit single example
2. **`examples`** - Multiple named examples (first one used)
3. **`default`** - Default value
4. **`enum`** - Random value from enum
5. **Generated** - Based on type, format, constraints

## Type Generators

### String

| Schema | Example Output |
|--------|----------------|
| `type: string` | `"aB3x9K"` |
| `minLength: 5, maxLength: 10` | `"abcde"` (5-10 chars) |
| `format: email` | `"user@example.com"` |
| `format: uuid` | `"550e8400-e29b-41d4-a716-446655440000"` |
| `format: date-time` | `"2024-01-15T10:30:00.000Z"` |
| `format: date` | `"2024-01-15"` |
| `format: uri` | `"https://example.com/path"` |
| `enum: ["a", "b", "c"]` | `"b"` (random) |
| `example: "fixed"` | `"fixed"` (always) |
| `default: "def"` | `"def"` |

### Integer

| Schema | Example Output |
|--------|----------------|
| `type: integer` | `42` (0-1000) |
| `minimum: 1, maximum: 100` | `57` (1-100) |
| `exclusiveMinimum: true, minimum: 0` | `1-1000` |
| `enum: [1, 2, 3]` | `2` (random) |

### Number

| Schema | Example Output |
|--------|----------------|
| `type: number` | `42.17` (0-1000) |
| `minimum: 0, maximum: 1` | `0.73` |
| `multipleOf: 0.01` | `0.42` (2 decimal places) |

### Boolean

| Schema | Example Output |
|--------|----------------|
| `type: boolean` | `true` or `false` (50/50) |
| `default: true` | `true` |
| `enum: [true]` | `true` |

### Array

| Schema | Example Output |
|--------|----------------|
| `type: array, items: {type: string}` | `["a", "b", "c"]` (1-10 items) |
| `minItems: 2, maxItems: 5` | 2-5 items |
| `uniqueItems: true` | No duplicates |

### Object

| Schema | Example Output |
|--------|----------------|
| `type: object, properties: {name: {type: string}}` | `{"name": "abc"}` |
| `required: ["id"]` | Always includes `id` |
| Optional properties | Included ~80% of the time |
| `additionalProperties: {type: string}` | Extra random properties |

## Format Support

### Built-in Formats

| Format | Generator |
|--------|-----------|
| `email` | Faker email |
| `uuid` | RFC 4122 UUID v4 |
| `date-time` | ISO 8601 UTC |
| `date` | YYYY-MM-DD |
| `time` | HH:MM:SS |
| `uri` / `url` | Valid URL |
| `ipv4` | IPv4 address |
| `ipv6` | IPv6 address |
| `hostname` | Valid hostname |
| `password` | Random password |
| `byte` | Base64 random bytes |

### Custom Pattern

Basic regex pattern support:

```yaml
pattern: "^[A-Z]{3}-\\d{4}$"
# Generates: "ABC-1234"
```

## Deterministic Generation

### Using Seeds

```bash
apimock openapi.yaml --seed 42
```

Same seed + same spec = identical output every time.

### How It Works

- Python's `random.Random(seed)` for standard types
- Faker's `seed_instance(seed)` for formatted strings
- Schema order preserved for consistent object property ordering

### Use Cases

- **Frontend development** - Consistent data for UI work
- **Screenshots** - Same data for visual regression tests
- **CI/CD** - Reproducible test runs
- **Bug reproduction** - Share seed to reproduce exact data

## Examples in Schema

### Single Example

```yaml
properties:
  name:
    type: string
    example: "John Doe"
```

### Multiple Examples

```yaml
properties:
  status:
    type: string
    enum: ["active", "inactive", "pending"]
    examples:
      active:
        value: "active"
        summary: "Active user"
      inactive:
        value: "inactive"
        summary: "Inactive user"
```

### Default Values

```yaml
properties:
  role:
    type: string
    enum: ["admin", "user"]
    default: "user"
```

## Response Selection

When multiple responses exist:

```
responses:
  "200": { ... }
  "404": { ... }
  "500": { ... }
```

ApiMock selects the **first 2xx response** by default (200, 201, 204, etc.).

Future versions will support:
- `--status 500` CLI flag
- `X-ApiMock-Status: 500` header

## Advanced: Customizing Generation

### Seed per Request (Future)

```bash
# Not yet implemented
curl -H "X-ApiMock-Seed: 123" http://localhost:8080/users
```

### Override Values (Future)

```yaml
# Not yet implemented
x-apimock:
  User:
    name: "Custom Name"
    email: "custom@example.com"
```

## Troubleshooting

### Empty Arrays

If arrays are empty, check `minItems`:

```yaml
# Default minItems is 1 (changed from 0)
type: array
items:
  $ref: "#/components/schemas/User"
minItems: 1  # Explicit for clarity
```

### Missing Optional Properties

Optional properties (~80% inclusion rate) may be missing. Use `required` for guaranteed presence.

### Very Long Strings

Default `maxLength` is 50. Specify constraints:

```yaml
type: string
maxLength: 200
```

### Determinism Issues

Ensure:
- Same seed used
- Same spec file
- Same ApiMock version
- No concurrent requests modifying generator state