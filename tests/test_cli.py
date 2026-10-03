"""Tests for CLI."""

import pytest
from click.testing import CliRunner
from apimock.cli import main


class TestCLI:
    """Tests for CLI commands."""

    def test_help(self):
        """Test --help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ApiMock" in result.output
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--seed" in result.output

    def test_version(self):
        """Test --version output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_missing_spec_file(self):
        """Test error when spec file not provided."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "SPEC_FILE" in result.output

    def test_nonexistent_spec_file(self):
        """Test error for nonexistent spec file."""
        runner = CliRunner()
        result = runner.invoke(main, ["nonexistent.yaml"])
        assert result.exit_code != 0
        assert "File not found" in result.output or "Error" in result.output

    def test_invalid_spec_file(self, tmp_path):
        """Test error for invalid spec file."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("invalid: yaml: [")
        runner = CliRunner()
        result = runner.invoke(main, [str(bad_file)])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_json_output(self, tmp_path):
        """Test --json output."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {"schema": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            },
        }
        import yaml
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.dump(spec))

        runner = CliRunner()
        result = runner.invoke(main, [str(spec_file), "--json"])
        assert result.exit_code == 0
        import json
        output = json.loads(result.output)
        assert output["host"] == "127.0.0.1"
        assert output["port"] == 8080
        assert output["routes"] == 1
        assert output["title"] == "Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])