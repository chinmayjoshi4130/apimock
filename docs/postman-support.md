# Postman Collection Support

ApiMock can generate mock servers directly from Postman Collection v2.1 format.

## Usage

```bash
# Auto-detect (if file has Postman structure)
apimock collection.json

# Explicit format
apimock collection.json --format postman
```

## Supported Features

| Feature | Supported |
|---------|-----------|
| HTTP Methods | ✅ GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| Path Parameters | ✅ `/users/42` → `/users/{id}` |
| Query Parameters | ✅ From URL or `query` array |
| Headers | ✅ Request headers as parameters |
| Request Body | ✅ raw (JSON), formdata, urlencoded |
| Response Examples | ✅ Multiple per endpoint |
| Folders | ✅ Used for organization |
| Variables | ⚠️ Not yet supported |

## Example Collection Structure

```json
{
  "info": {
    "name": "My API",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "url": "http://localhost:8080/users?limit=10"
      },
      "response": [
        {
          "name": "Success",
          "code": 200,
          "header": [{"key": "Content-Type", "value": "application/json"}],
          "body": "[{\"id\": 1, \"name\": \"Alice\"}]"
        }
      ]
    },
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "url": "http://localhost:8080/users",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"Bob\", \"email\": \"bob@example.com\"}",
          "options": {"raw": {"language": "json"}}
        }
      },
      "response": [
        {
          "code": 201,
          "body": "{\"id\": 2, \"name\": \"Bob\", \"email\": \"bob@example.com\"}"
        }
      ]
    }
  ]
}
```

## Body Formats

| Postman Mode | Content-Type |
|--------------|--------------|
| `raw` (json) | `application/json` |
| `raw` (xml) | `application/xml` |
| `raw` (text) | `text/plain` |
| `formdata` | `multipart/form-data` |
| `urlencoded` | `application/x-www-form-urlencoded` |

## Path Parameter Detection

ApiMock automatically converts:
- `/users/42` → `/users/{id}`
- `/users/550e8400-e29b-41d4-a716-446655440000` → `/users/{id}`
- `/api/v1/users/123` → `/api/v1/users/{id}`

## Response Selection

- Uses first response example for each status code
- Prefers 2xx status codes for default responses
- Falls back to first available response

## Limitations

- No support for pre-request/test scripts
- No environment variable substitution
- No authentication helpers
- Folder names not included in paths