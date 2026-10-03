"""HTTP server for ApiMock."""

import asyncio
import time
from typing import Any
from aiohttp import web
from aiohttp.web import Request, Response, StreamResponse

from apimock.parser.models import NormalizedApi
from apimock.mock.generator import MockGenerator
from apimock.server.routes import Router, RouteMatch


class MockServer:
    """HTTP mock server for ApiMock."""

    def __init__(
        self,
        api: NormalizedApi,
        generator: MockGenerator,
        host: str = "127.0.0.1",
        port: int = 8080,
        delay: int = 0,
        verbose: bool = False,
        quiet: bool = False,
    ):
        self.api = api
        self.generator = generator
        self.host = host
        self.port = port
        self.delay = delay
        self.verbose = verbose
        self.quiet = quiet
        self.router = Router(api.routes)
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up aiohttp routes."""
        # Catch-all route for all methods
        self.app.router.add_route("*", "/{tail:.*}", self._handle_request)

    async def _handle_request(self, request: Request) -> StreamResponse:
        """Handle incoming HTTP request."""
        start_time = time.time()

        # Get path and query
        path = request.path
        query_string = request.query_string
        method = request.method

        # Match route
        match = self.router.match(method, path, query_string)

        if match is None:
            return self._not_found_response(path, method)

        # Simulate delay
        if self.delay > 0:
            await asyncio.sleep(self.delay / 1000.0)

        # Determine status code (prefer 2xx)
        status_code = 200
        selected_response = None
        for resp in match.route.responses:
            if 200 <= resp.status_code < 300:
                status_code = resp.status_code
                selected_response = resp
                break

        # Generate response
        if selected_response and selected_response.schema:
            response_data = self.generator.generate(selected_response.schema)
        elif selected_response and selected_response.example is not None:
            response_data = selected_response.example
        elif selected_response and selected_response.examples:
            first_example = next(iter(selected_response.examples.values()))
            if isinstance(first_example, dict) and "value" in first_example:
                response_data = first_example["value"]
            else:
                response_data = first_example
        else:
            response_data = self.generator.generate_response(match.route)

        # Build response - handle 204 No Content
        if status_code == 204:
            response = web.Response(status=204)
        else:
            response = web.json_response(response_data, status=status_code)

        # Log request
        if not self.quiet:
            elapsed = int((time.time() - start_time) * 1000)
            self._log_request(method, path, status_code, elapsed)

        return response

    def _not_found_response(self, path: str, method: str) -> Response:
        """Return 404 response for unmatched routes."""
        return web.json_response(
            {"error": "Not Found", "message": f"No route matches {method} {path}"},
            status=404,
        )

    def _log_request(self, method: str, path: str, status: int, elapsed: int) -> None:
        """Log incoming request."""
        method_str = f"{method:<7}"
        path_str = f"{path:<30}"
        print(f"{method_str} {path_str} {status:<4} {elapsed}ms")

    def print_startup_info(self) -> None:
        """Print server startup information."""
        if self.quiet:
            return

        print(f"\nApiMock v0.1.0\n")
        print(f"Spec:   {self.api.title} v{self.api.version}")
        print(f"Host:   {self.host}")
        print(f"Port:   {self.port}")
        print(f"\nRoutes:")

        for route in self.api.routes:
            method_str = f"{route.method.value:<7}"
            print(f"  {method_str} {route.path}")

        print(f"\nMock server ready at http://{self.host}:{self.port}\n")

    async def start(self) -> None:
        """Start the server."""
        self.print_startup_info()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()

    def run(self) -> None:
        """Run the server synchronously."""
        asyncio.run(self.start())


def create_server(
    api: NormalizedApi,
    generator: MockGenerator,
    host: str = "127.0.0.1",
    port: int = 8080,
    delay: int = 0,
    verbose: bool = False,
    quiet: bool = False,
) -> MockServer:
    """Factory function to create a MockServer."""
    return MockServer(api, generator, host, port, delay, verbose, quiet)