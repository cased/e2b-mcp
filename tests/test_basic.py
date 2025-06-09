"""
Basic tests for e2b-mcp package.
"""

import pytest

from e2b_mcp import E2BMCPRunner, MCPError, ServerConfig, Tool


class TestServerConfig:
    """Test ServerConfig functionality."""

    def test_create_server_config(self):
        """Test creating ServerConfig."""
        config = ServerConfig(
            name="test",
            command="python test.py",
            install_commands=["pip install test-package"],
            description="Test server",
            timeout_minutes=15,
        )

        assert config.name == "test"
        assert config.command == "python test.py"
        assert config.install_commands == ["pip install test-package"]
        assert config.description == "Test server"
        assert config.timeout_minutes == 15

    def test_from_dict(self):
        """Test creating ServerConfig from dictionary."""
        data = {
            "command": "python -m test_server",
            "install_commands": ["pip install test-server-package"],
            "description": "Test MCP server",
            "timeout_minutes": 20,
            "env": {"DEBUG": "1"},
        }

        config = ServerConfig.from_dict("test", data)

        assert config.name == "test"
        assert config.command == "python -m test_server"
        assert config.install_commands == ["pip install test-server-package"]
        assert config.description == "Test MCP server"
        assert config.timeout_minutes == 20
        assert config.env == {"DEBUG": "1"}

    def test_to_dict(self):
        """Test converting ServerConfig to dictionary."""
        config = ServerConfig(name="test", command="python test.py", description="Test server")

        data = config.to_dict()

        assert data["name"] == "test"
        assert data["command"] == "python test.py"
        assert data["description"] == "Test server"
        assert data["install_commands"] == []
        assert data["timeout_minutes"] == 10


class TestTool:
    """Test Tool functionality."""

    def test_create_tool(self):
        """Test creating Tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            server_name="test_server",
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.input_schema == {"type": "object"}
        assert tool.server_name == "test_server"

    def test_from_mcp_tool(self):
        """Test creating Tool from MCP tool data."""
        tool_data = {
            "name": "read_file",
            "description": "Read a file",
            "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}},
        }

        tool = Tool.from_mcp_tool(tool_data, "filesystem")

        assert tool.name == "read_file"
        assert tool.description == "Read a file"
        assert tool.server_name == "filesystem"
        assert "path" in tool.input_schema["properties"]


class TestE2BMCPRunner:
    """Test E2BMCPRunner functionality."""

    def test_init_without_api_key(self, monkeypatch):
        """Test initialization without API key."""
        monkeypatch.delenv("E2B_API_KEY", raising=False)

        with pytest.raises(ValueError, match="E2B_API_KEY is required"):
            E2BMCPRunner()

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        runner = E2BMCPRunner(api_key="test_key")
        assert runner.api_key == "test_key"

    def test_add_server(self):
        """Test adding server configuration."""
        runner = E2BMCPRunner(api_key="test")
        config = ServerConfig(name="test", command="python test.py")

        runner.add_server(config)

        assert "test" in runner.server_configs
        assert runner.server_configs["test"] == config

    def test_add_server_from_dict(self):
        """Test adding server from dictionary."""
        runner = E2BMCPRunner(api_key="test")

        runner.add_server_from_dict(
            "test", {"command": "python test.py", "description": "Test server"}
        )

        assert "test" in runner.server_configs
        config = runner.server_configs["test"]
        assert config.name == "test"
        assert config.command == "python test.py"
        assert config.description == "Test server"

    def test_list_servers(self):
        """Test listing servers."""
        runner = E2BMCPRunner(api_key="test")

        runner.add_server_from_dict("server1", {"command": "cmd1"})
        runner.add_server_from_dict("server2", {"command": "cmd2"})

        servers = runner.list_servers()
        assert set(servers) == {"server1", "server2"}

    def test_get_server_config(self):
        """Test getting server configuration."""
        runner = E2BMCPRunner(api_key="test")
        config = ServerConfig(name="test", command="python test.py")
        runner.add_server(config)

        retrieved = runner.get_server_config("test")
        assert retrieved == config

        missing = runner.get_server_config("nonexistent")
        assert missing is None


class TestMCPError:
    """Test MCPError exception."""

    def test_mcp_error(self):
        """Test MCPError creation."""
        error = MCPError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
