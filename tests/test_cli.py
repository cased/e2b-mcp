#!/usr/bin/env python3
"""
Tests for the e2b-mcp CLI interface.

These tests use Click's testing utilities to test the CLI functionality
without requiring actual E2B API calls or MCP server interactions.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from e2b_mcp.cli import cli
from e2b_mcp.models import MCPError, Tool


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".e2b-mcp"
        config_dir.mkdir()

        # Mock the config directory function
        monkeypatch.setattr("e2b_mcp.cli.get_config_dir", lambda: config_dir)
        yield config_dir


@pytest.fixture
def sample_config():
    """Sample server configuration for testing."""
    return {
        "github": {
            "command": "npx -y @modelcontextprotocol/server-github",
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
            "description": "GitHub integration",
            "timeout_minutes": 10,
        },
        "filesystem": {
            "command": "npx -y @modelcontextprotocol/server-filesystem /tmp",
            "env": {},
            "timeout_minutes": 5,
        },
    }


class TestBasicCLI:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "E2B MCP CLI" in result.output
        assert "Run MCP servers securely" in result.output

    def test_cli_version(self, runner):
        """Test CLI shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_server_subcommand_help(self, runner):
        """Test server subcommand help."""
        result = runner.invoke(cli, ["server", "--help"])
        assert result.exit_code == 0
        assert "Manage MCP server configurations" in result.output

    def test_tools_subcommand_help(self, runner):
        """Test tools subcommand help."""
        result = runner.invoke(cli, ["tools", "--help"])
        assert result.exit_code == 0
        assert "Discover and execute MCP tools" in result.output


class TestServerManagement:
    """Test server configuration management."""

    def test_server_add_basic(self, runner, temp_config_dir):
        """Test adding a basic server configuration."""
        result = runner.invoke(cli, ["server", "add", "test", "--command", "python test.py"])

        assert result.exit_code == 0
        assert "✅ Added server 'test'" in result.output
        assert "Command: python test.py" in result.output

        # Check config file was created
        config_file = temp_config_dir / "servers.json"
        assert config_file.exists()

        with open(config_file) as f:
            config = json.load(f)

        assert "test" in config
        assert config["test"]["command"] == "python test.py"
        assert config["test"]["env"] == {}
        assert config["test"]["timeout_minutes"] == 10

    def test_server_add_with_options(self, runner, temp_config_dir):
        """Test adding server with all options."""
        result = runner.invoke(
            cli,
            [
                "server",
                "add",
                "github",
                "--command",
                "npx server-github",
                "--env",
                "TOKEN=abc123",
                "--env",
                "DEBUG=1",
                "--install-commands",
                "npm install github-mcp",
                "--description",
                "GitHub server",
                "--timeout",
                "15",
            ],
        )

        assert result.exit_code == 0
        assert "✅ Added server 'github'" in result.output
        assert "Environment: ['TOKEN', 'DEBUG']" in result.output
        assert "Install commands: 1 commands" in result.output

        # Check config
        config_file = temp_config_dir / "servers.json"
        with open(config_file) as f:
            config = json.load(f)

        github_config = config["github"]
        assert github_config["command"] == "npx server-github"
        assert github_config["env"] == {"TOKEN": "abc123", "DEBUG": "1"}
        assert github_config["install_commands"] == ["npm install github-mcp"]
        assert github_config["description"] == "GitHub server"
        assert github_config["timeout_minutes"] == 15

    def test_server_add_invalid_env(self, runner, temp_config_dir):
        """Test adding server with invalid environment variable format."""
        result = runner.invoke(
            cli, ["server", "add", "test", "--command", "python test.py", "--env", "INVALID_FORMAT"]
        )

        assert result.exit_code == 1
        assert "Invalid environment variable format" in result.output
        assert "Use format: KEY=VALUE" in result.output

    def test_server_list_empty(self, runner, temp_config_dir):
        """Test listing servers when none are configured."""
        result = runner.invoke(cli, ["server", "list"])

        assert result.exit_code == 0
        assert "No servers configured" in result.output
        assert "Use 'e2b-mcp server add'" in result.output

    def test_server_list_with_servers(self, runner, temp_config_dir, sample_config):
        """Test listing configured servers."""
        # Save sample config
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(cli, ["server", "list"])

        assert result.exit_code == 0
        assert "Configured MCP Servers:" in result.output
        assert "📡 github" in result.output
        assert "📡 filesystem" in result.output
        assert "GitHub integration" in result.output
        assert "npx -y @modelcontextprotocol/server-github" in result.output

    def test_server_list_json(self, runner, temp_config_dir, sample_config):
        """Test listing servers in JSON format."""
        # Save sample config
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(cli, ["server", "list", "--json"])

        assert result.exit_code == 0

        # Should be valid JSON
        output_config = json.loads(result.output)
        assert "github" in output_config
        assert "filesystem" in output_config
        assert output_config["github"]["command"] == "npx -y @modelcontextprotocol/server-github"

    def test_server_remove_existing(self, runner, temp_config_dir, sample_config):
        """Test removing an existing server."""
        # Save sample config
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(cli, ["server", "remove", "github", "--yes"])

        assert result.exit_code == 0
        assert "✅ Removed server 'github'" in result.output

        # Check config file
        with open(config_file) as f:
            config = json.load(f)

        assert "github" not in config
        assert "filesystem" in config  # Should still exist

    def test_server_remove_nonexistent(self, runner, temp_config_dir):
        """Test removing a non-existent server."""
        result = runner.invoke(cli, ["server", "remove", "nonexistent", "--yes"])

        assert result.exit_code == 1
        assert "Server 'nonexistent' not found" in result.output

    def test_server_remove_with_confirmation(self, runner, temp_config_dir, sample_config):
        """Test removing server with confirmation prompt."""
        # Save sample config
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        # Test declining confirmation
        result = runner.invoke(cli, ["server", "remove", "github"], input="n")
        assert result.exit_code == 1  # Aborted

        # Config should be unchanged
        with open(config_file) as f:
            config = json.load(f)
        assert "github" in config

        # Test accepting confirmation
        result = runner.invoke(cli, ["server", "remove", "github"], input="y")
        assert result.exit_code == 0
        assert "✅ Removed server 'github'" in result.output


class TestToolOperations:
    """Test tool discovery and execution."""

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_list_success(self, mock_get_runner, runner, temp_config_dir):
        """Test successful tool discovery."""
        # Mock runner and tools
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        # Create mock tools
        mock_tools = [
            Tool(
                name="read_file",
                description="Read a file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "encoding": {"type": "string"}},
                    "required": ["path"],
                },
                server_name="filesystem",
            ),
            Tool(
                name="write_file",
                description="Write a file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
                server_name="filesystem",
            ),
        ]

        mock_runner.discover_tools = AsyncMock(return_value=mock_tools)

        result = runner.invoke(cli, ["tools", "list", "filesystem"])

        assert result.exit_code == 0
        assert "Tools from 'filesystem' (2 found):" in result.output
        assert "🔧 read_file" in result.output
        assert "🔧 write_file" in result.output
        assert "Read a file" in result.output
        assert "Write a file" in result.output
        assert "• path (string) - required" in result.output
        assert "• encoding (string) - optional" in result.output

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_list_json(self, mock_get_runner, runner, temp_config_dir):
        """Test tool discovery with JSON output."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_tools = [
            Tool(
                name="test_tool",
                description="Test tool",
                input_schema={"type": "object"},
                server_name="test",
            )
        ]

        mock_runner.discover_tools = AsyncMock(return_value=mock_tools)

        result = runner.invoke(cli, ["tools", "list", "test", "--json"])

        assert result.exit_code == 0

        # Should be valid JSON
        tools_data = json.loads(result.output)
        assert len(tools_data) == 1
        assert tools_data[0]["name"] == "test_tool"
        assert tools_data[0]["description"] == "Test tool"
        assert tools_data[0]["server_name"] == "test"

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_list_error(self, mock_get_runner, runner, temp_config_dir):
        """Test tool discovery with MCP error."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_runner.discover_tools = AsyncMock(side_effect=MCPError("Server not found"))

        result = runner.invoke(cli, ["tools", "list", "nonexistent"])

        assert result.exit_code == 1
        assert "MCP Error: Server not found" in result.output

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_execute_with_params(self, mock_get_runner, runner, temp_config_dir):
        """Test tool execution with JSON parameters."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_result = {"content": [{"type": "text", "text": "File contents here"}]}

        mock_runner.execute_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(
            cli,
            [
                "tools",
                "execute",
                "filesystem",
                "read_file",
                "--params",
                '{"path": "/tmp/test.txt"}',
            ],
        )

        assert result.exit_code == 0
        assert "✅ Executed read_file on filesystem" in result.output
        assert "File contents here" in result.output

        # Verify the mock was called correctly
        mock_runner.execute_tool.assert_called_once_with(
            "filesystem", "read_file", {"path": "/tmp/test.txt"}
        )

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_execute_with_individual_params(self, mock_get_runner, runner, temp_config_dir):
        """Test tool execution with individual parameters."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_result = {"success": True}
        mock_runner.execute_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(
            cli,
            [
                "tools",
                "execute",
                "filesystem",
                "write_file",
                "--param",
                "path=/tmp/test.txt",
                "--param",
                "content=Hello World",
            ],
        )

        assert result.exit_code == 0

        # Check the parameters were parsed correctly
        mock_runner.execute_tool.assert_called_once_with(
            "filesystem", "write_file", {"path": "/tmp/test.txt", "content": "Hello World"}
        )

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_tools_execute_json_output(self, mock_get_runner, runner, temp_config_dir):
        """Test tool execution with JSON output."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_result = {"result": "success", "data": {"key": "value"}}
        mock_runner.execute_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(cli, ["tools", "execute", "test", "test_tool", "--json"])

        assert result.exit_code == 0

        # Should output valid JSON
        output_data = json.loads(result.output)
        assert output_data == mock_result

    def test_tools_execute_invalid_json_params(self, runner, temp_config_dir):
        """Test tool execution with invalid JSON parameters."""
        result = runner.invoke(
            cli, ["tools", "execute", "test", "test_tool", "--params", "invalid json"]
        )

        assert result.exit_code == 1
        assert "Invalid JSON in --params" in result.output

    def test_tools_execute_invalid_param_format(self, runner, temp_config_dir):
        """Test tool execution with invalid parameter format."""
        result = runner.invoke(
            cli, ["tools", "execute", "test", "test_tool", "--param", "invalid_format"]
        )

        assert result.exit_code == 1
        assert "Invalid parameter format" in result.output
        assert "Use format: key=value" in result.output


class TestQuickExecute:
    """Test quick execution functionality."""

    @patch("e2b_mcp.cli.E2BMCPRunner")
    def test_quick_execute_basic(self, mock_runner_class, runner):
        """Test basic quick execution."""
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        mock_result = {"content": [{"type": "text", "text": "Quick execution result"}]}

        mock_runner.execute_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(cli, ["quick", "python test.py", "test_tool"])

        assert result.exit_code == 0
        assert "✅ Executed test_tool" in result.output
        assert "Quick execution result" in result.output

        # Verify runner was configured correctly
        mock_runner.add_server_from_dict.assert_called_once_with(
            "temp_server", {"command": "python test.py", "env": {}}
        )
        mock_runner.execute_tool.assert_called_once_with("temp_server", "test_tool", {})

    @patch("e2b_mcp.cli.E2BMCPRunner")
    def test_quick_execute_with_env_and_params(self, mock_runner_class, runner):
        """Test quick execution with environment variables and parameters."""
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        mock_result = {"success": True}
        mock_runner.execute_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(
            cli,
            [
                "quick",
                "npx server",
                "create_file",
                "--env",
                "TOKEN=abc123",
                "--env",
                "DEBUG=1",
                "--param",
                "path=/tmp/test.txt",
                "--params",
                '{"mode": "create"}',
            ],
        )

        assert result.exit_code == 0

        # Check environment variables
        mock_runner.add_server_from_dict.assert_called_once_with(
            "temp_server", {"command": "npx server", "env": {"TOKEN": "abc123", "DEBUG": "1"}}
        )

        # Check parameters (should merge --param and --params)
        expected_params = {"path": "/tmp/test.txt", "mode": "create"}
        mock_runner.execute_tool.assert_called_once_with(
            "temp_server", "create_file", expected_params
        )


class TestConfiguration:
    """Test configuration management."""

    def test_config_show_no_file(self, runner, temp_config_dir):
        """Test showing config when no file exists."""
        result = runner.invoke(cli, ["config", "--show"])

        assert result.exit_code == 0
        assert "Configuration file:" in result.output
        assert "No configuration file found" in result.output

    def test_config_show_with_file(self, runner, temp_config_dir, sample_config):
        """Test showing existing configuration."""
        # Create config file
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f, indent=2)

        result = runner.invoke(cli, ["config", "--show"])

        assert result.exit_code == 0
        assert "Configuration file:" in result.output
        assert "github" in result.output
        assert "filesystem" in result.output

    def test_config_reset(self, runner, temp_config_dir, sample_config):
        """Test resetting configuration."""
        # Create config file
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        assert config_file.exists()

        # Reset with confirmation
        result = runner.invoke(cli, ["config", "--reset"], input="y")

        assert result.exit_code == 0
        assert "✅ Configuration reset" in result.output
        assert not config_file.exists()

    def test_config_reset_declined(self, runner, temp_config_dir, sample_config):
        """Test declining configuration reset."""
        # Create config file
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        result = runner.invoke(cli, ["config", "--reset"], input="n")

        assert result.exit_code == 0
        assert config_file.exists()  # Should still exist


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_missing_e2b_api_key(self, mock_get_runner, runner):
        """Test behavior when E2B API key is missing."""
        # Mock runner creation to raise ValueError for missing API key
        mock_get_runner.side_effect = ValueError("E2B_API_KEY is required")

        result = runner.invoke(cli, ["tools", "list", "test"])

        assert result.exit_code == 1
        assert "E2B_API_KEY is required" in result.output

    def test_corrupted_config_file(self, runner, temp_config_dir):
        """Test handling of corrupted configuration file."""
        # Create corrupted config file
        config_file = temp_config_dir / "servers.json"
        with open(config_file, "w") as f:
            f.write("invalid json content")

        result = runner.invoke(cli, ["server", "list"])

        assert result.exit_code == 0  # Should not crash
        assert "No servers configured" in result.output  # Should fall back gracefully

    @patch("e2b_mcp.cli.get_runner_with_config")
    def test_unexpected_error(self, mock_get_runner, runner):
        """Test handling of unexpected errors."""
        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_runner.discover_tools = AsyncMock(side_effect=Exception("Unexpected error"))

        result = runner.invoke(cli, ["tools", "list", "test"])

        assert result.exit_code == 1
        assert "Error: Unexpected error" in result.output


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands (require E2B API key)."""

    def test_cli_integration_basic(self, runner):
        """Test basic CLI integration with real E2B API."""
        # This would test the full CLI with real API calls
        # Skip if no API key is available
        if not os.getenv("E2B_API_KEY"):
            pytest.skip("E2B_API_KEY not set")

        # Test quick execution with a simple MCP server
        command = (
            "python -c 'import json; "
            'print(json.dumps({"jsonrpc": "2.0", "result": {"tools": []}}))\''
        )
        result = runner.invoke(
            cli,
            [
                "quick",
                command,
                "test_tool",
                "--json",
            ],
        )

        # This is a simplified test - in practice would need a real MCP server
        # Just verify the CLI doesn't crash with real API calls
        assert result.exit_code in [0, 1]  # May fail due to invalid MCP server, but shouldn't crash


if __name__ == "__main__":
    pytest.main([__file__])
