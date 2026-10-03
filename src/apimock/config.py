"""Configuration for ApiMock."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for ApiMock server."""
    spec_file: str
    host: str = "127.0.0.1"
    port: int = 8080
    seed: Optional[int] = None
    delay: int = 0
    verbose: bool = False
    quiet: bool = False
    watch: bool = False
    json_output: bool = False

    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")


def create_config(
    spec_file: str,
    host: str = "127.0.0.1",
    port: int = 8080,
    seed: Optional[int] = None,
    delay: int = 0,
    verbose: bool = False,
    quiet: bool = False,
    watch: bool = False,
    json_output: bool = False,
) -> Config:
    """Factory function to create Config."""
    return Config(
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