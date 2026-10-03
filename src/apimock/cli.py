"""CLI entry point for ApiMock."""

import sys
import json
import asyncio
import yaml
from pathlib import Path

import click

from apimock.parser.openapi import parse_file as parse_openapi, OpenApiParseError
from apimock.parser.postman import parse_postman_file, PostmanParseError
from apimock.parser.har import parse_har_file, HARParseError
from apimock.parser.apimock_format import parse_apimock_file, ApiMockFormatError, is_apimock_format
from apimock.mock.generator import create_generator
from apimock.server.app import create_server, MockServer
from apimock.config import create_config, Config


class AnyParseError(Exception):
    """Wrapper for any parsing error."""
    pass


def detect_format(file_path: str) -> str:
    """Detect specification format from file content."""
    path = Path(file_path)
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Try to parse as YAML to check for ApiMock format
        try:
            data = yaml.safe_load(content)
        except Exception:
            return "openapi"  # Assume YAML OpenAPI

    # Check for ApiMock native format
    if is_apimock_format(data):
        return "apimock"

    # Check for Postman Collection
    if "info" in data and "item" in data and isinstance(data.get("item"), list):
        return "postman"

    # Check for HAR
    if "log" in data and "entries" in data.get("log", {}):
        return "har"

    # Default to OpenAPI
    return "openapi"


def parse_spec_file(file_path: str) -> tuple:
    """Parse specification file, auto-detecting format."""
    fmt = detect_format(file_path)

    try:
        if fmt == "apimock":
            api = parse_apimock_file(file_path)
        elif fmt == "postman":
            api = parse_postman_file(file_path)
        elif fmt == "har":
            api = parse_har_file(file_path)
        else:
            api = parse_openapi(file_path)
        return api, fmt
    except (OpenApiParseError, PostmanParseError, HARParseError, ApiMockFormatError) as e:
        raise AnyParseError(str(e))


@click.command()
@click.argument("spec_file", type=click.Path(exists=True, readable=True))
@click.option("--host", "-H", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=8080, type=int, help="Port to bind to")
@click.option("--seed", type=int, help="Random seed for deterministic generation")
@click.option("--delay", type=int, default=0, help="Artificial delay in milliseconds")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output (no request logging)")
@click.option("--watch", "-w", is_flag=True, help="Watch spec file for changes (not yet implemented)")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON")
@click.option("--format", type=click.Choice(["auto", "openapi", "postman", "har", "apimock"]), default="auto",
              help="Specification format (default: auto-detect)")
@click.version_option(version="0.1.0", prog_name="ApiMock")
def main(
    spec_file: str,
    host: str,
    port: int,
    seed: int | None,
    delay: int,
    verbose: bool,
    quiet: bool,
    watch: bool,
    json_output: bool,
    format: str,
) -> None:
    """ApiMock - Local API mocking from OpenAPI, Postman Collection, HAR, or native format.

    Example:
        apimock openapi.yaml
        apimock collection.json --format postman
        apimock archive.har --format har
        apimock api.mock --format apimock
        apimock openapi.yaml --port 9000 --seed 42
    """
    config = create_config(
        spec_file=spec_file,
        host=host,
        port=port,
        seed=seed,
        delay=delay,
        verbose=verbose,
        quiet=quiet,
        watch=watch,
        json_output=json_output,
    )

    try:
        run_server(config, format)
    except AnyParseError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        if not config.quiet:
            click.echo("\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def run_server(config: Config, format: str = "auto") -> None:
    """Run the mock server with given configuration."""
    # Parse spec file
    if format == "auto":
        api, detected_fmt = parse_spec_file(config.spec_file)
        if not config.quiet and not config.json_output:
            click.echo(f"Detected format: {detected_fmt}")
    elif format == "apimock":
        api = parse_apimock_file(config.spec_file)
    elif format == "postman":
        api = parse_postman_file(config.spec_file)
    elif format == "har":
        api = parse_har_file(config.spec_file)
    else:
        api = parse_openapi(config.spec_file)

    # Create mock generator
    generator = create_generator(api, config.seed)

    # Create server
    server = create_server(
        api=api,
        generator=generator,
        host=config.host,
        port=config.port,
        delay=config.delay,
        verbose=config.verbose,
        quiet=config.quiet,
    )

    # Output JSON if requested
    if config.json_output:
        output = {
            "host": config.host,
            "port": config.port,
            "routes": len(api.routes),
            "title": api.title,
            "version": api.version,
        }
        click.echo(json.dumps(output))
        return

    # Run server
    server.run()


if __name__ == "__main__":
    main()