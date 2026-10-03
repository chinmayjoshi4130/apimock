# HAR (HTTP Archive) Support

ApiMock can generate mock servers from HAR files captured from browser dev tools or API clients.

## Usage

```bash
# Auto-detect (if file has HAR structure)
apimock archive.har

# Explicit format
apimock archive.har --format har
```

## Obtaining HAR Files

### Chrome DevTools
1. Open DevTools (F12)
2. Go to Network tab
3. Check "Preserve log"
4. Perform API requests
4. Right-click → "Save all as HAR with content"

### Firefox DevTools
1. Open DevTools (F12)
2. Go to Network tab
3. Perform API requests
4. Right-click → "Save All As HAR"

### curl
```bash
curl --output archive.har -w "@har-format.txt" http://api.example.com
```

### Postman
1. Open collection
2. Click "..." → Export
3. Choose "Collection v2.1" (not HAR)
4. Or use Postman's "Save Responses" feature

## Supported Features

| Feature | Supported |
|---------|-----------|
| Request Methods | ✅ GET, POST, PUT, PATCH, DELETE, etc. |
| Path Parameters | ✅ Auto-normalized (`/users/42` → `/users/{id}`) |
| Query Parameters | ✅ From URL and `queryString` |
| Headers | ✅ Request/Response (filters auto-headers) |
| Request Body | ✅ JSON, form, text (with base64 decode) |
| Response Body | ✅ JSON, text (with base64 decode) |
| Multiple Entries | ✅ Merged by path+method |
| Status Codes | ✅ Preserved from capture |
| Timings | ⚠️ Not used (use `--delay` instead) |

## Path Normalization

HAR captures contain real requests with concrete IDs. ApiMock normalizes:

| Original Path | Normalized |
|---------------|------------|
| `/api/users/42` | `/api/users/{id}` |
| `/api/users/550e8400-e29b-41d4-a716-446655440000` | `/api/users/{id}` |
| `/api/users/123/posts/456` | `/api/users/{id}/posts/{id}` |
| `/api/search?q=test` | `/api/search` (query params extracted) |

## Entry Merging

Multiple HAR entries for the same endpoint are merged:
- Unique status codes preserved (200, 404, 500, etc.)
- Request bodies from first entry
- Response examples from all entries
- Headers filtered (removes User-Agent, Accept, etc.)

## Example HAR Entry

```json
{
  "log": {
    "version": "1.2",
    "creator": {"name": "Chrome", "version": "120.0.0.0"},
    "entries": [
      {
        "request": {
          "method": "GET",
          "url": "http://localhost:8080/api/users/42",
          "headers": [{"name": "Authorization", "value": "Bearer token"}],
          "queryString": []
        },
        "response": {
          "status": 200,
          "headers": [{"name": "Content-Type", "value": "application/json"}],
          "content": {
            "mimeType": "application/json",
            "text": "{\"id\": 42, \"name\": \"Alice\"}"
          }
        }
      }
    ]
  }
}
```

## Base64 Encoded Content

HAR files may encode binary content as base64. ApiMock automatically decodes:
```json
"content": {
  "mimeType": "application/json",
  "text": "eyJpZCI6IDQyfQ==",
  "encoding": "base64"
}
```

## Limitations

- No WebSocket support
- No redirect handling
- Timing information not used for delay simulation
- Cookie handling basic
- No multipart form parsing (stored as raw)
- Single host assumption (uses first entry's host)

## Tips

1. **Clean captures**: Remove unnecessary requests (analytics, static assets)
2. **Include failures**: Capture 4xx/5xx responses for error simulation
3. **Use `--seed`**: For deterministic mock data from generated schemas
4. **Combine with `--delay`**: Simulate realistic latency