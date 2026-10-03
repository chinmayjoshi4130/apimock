# Contributing

## Development Setup

```bash
# Clone repository
git clone https://github.com/example/apimock
cd apimock

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Or manually
pip install -e .
pip install pytest pytest-asyncio pytest-aiohttp faker
```

## Project Structure

```
apimock/
├── src/apimock/          # Main package
│   ├── cli.py            # CLI entry point
│   ├── config.py         # Configuration
│   ├── parser/           # OpenAPI parsing
│   ├── mock/             # Data generation
│   └── server/           # HTTP server
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/             # Example specs
├── pyproject.toml        # Project config
├── pytest.ini            # Pytest config
└── README.md             # Main docs
```

## Running Tests

```bash
# All tests
pytest

# Verbose
pytest -v

# Specific test file
pytest tests/test_parser.py -v

# With coverage
pytest --cov=apimock tests/

# Watch mode (requires pytest-watch)
ptw
```

## Code Style

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/
```

## Adding Features

### 1. New Schema Format

Edit `src/apimock/mock/generator.py`:

```python
def _generate_string(self, schema: dict[str, Any]) -> str:
    format_ = schema.get("format")
    if format_ == "my-format":
        return self.faker.my_provider()
    # ... existing formats
```

### 2. New Schema Type

```python
def _generate_by_type(self, schema: dict[str, Any]) -> Any:
    schema_type = get_schema_type(schema)
    if schema_type == "my-type":
        return self._generate_my_type(schema)
    # ... existing types
```

### 3. New CLI Option

Edit `src/apimock/cli.py`:

```python
@click.option("--my-option", help="Description")
def main(..., my_option: str):
    config = create_config(..., my_option=my_option)
```

Edit `src/apimock/config.py`:

```python
@dataclass
class Config:
    my_option: str = "default"
```

### 4. New OpenAPI Feature

Edit `src/apimock/parser/openapi.py`:

```python
def parse_new_feature(self, spec: dict, ...) -> NewModel:
    # Parse and return normalized model
```

## Testing Guidelines

### Unit Tests

- Test one function/class per test
- Use fixtures for common setup
- Mock external dependencies
- Test edge cases

```python
def test_generate_email_format(generator):
    result = generator.generate({"type": "string", "format": "email"})
    assert "@" in result
    assert "." in result.split("@")[1]
```

### Integration Tests

- Test full request/response cycle
- Use aiohttp test client
- Verify HTTP status codes, headers, body

```python
@pytest.mark.asyncio
async def test_get_users(aiohttp_client, server):
    client = await aiohttp_client(server.app)
    resp = await client.get("/users")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)
```

## Pull Request Process

1. **Fork** the repository
2. **Create branch** - `feature/description` or `fix/description`
3. **Make changes** - Follow code style
4. **Add tests** - Cover new functionality
5. **Run tests** - Ensure all pass
6. **Update docs** - If user-facing change
7. **Submit PR** - Clear description of changes

## Release Process

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

# Build
pip install build
python -m build

# Test package
pip install dist/apimock-*.whl
apimock --version

# Publish (maintainers only)
twine upload dist/*
```

## Reporting Issues

### Bug Reports

Include:
- ApiMock version (`apimock --version`)
- Python version
- OpenAPI spec (minimal reproduction)
- Command used
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Example OpenAPI spec if applicable

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers contribute
- No harassment or discrimination

## License

By contributing, you agree your contributions will be licensed under the MIT License.