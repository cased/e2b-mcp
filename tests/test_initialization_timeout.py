"""
Tests for initialization timeout functionality in e2b-mcp.

Tests that the initialization_timeout parameter is properly used by the E2B runner
when setting up MCP servers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from e2b_mcp import E2BMCPRunner, ServerConfig


class TestInitializationTimeout:
    """Test initialization timeout functionality."""

    def test_server_config_includes_timeout_in_e2b_config(self):
        """Test that initialization_timeout is properly stored in ServerConfig."""
        # Default timeout
        config_default = ServerConfig(name="test", command="python test.py")
        assert config_default.initialization_timeout == 30

        # Custom timeout
        config_custom = ServerConfig(
            name="kit", command="python -m kit.mcp", initialization_timeout=45
        )
        assert config_custom.initialization_timeout == 45

    def test_runner_uses_initialization_timeout(self):
        """Test that E2BMCPRunner properly uses initialization_timeout."""
        runner = E2BMCPRunner(api_key="test_key")

        # Add server with custom initialization timeout
        config_data = {
            "command": "python -m kit.mcp",
            "description": "Kit MCP server",
            "initialization_timeout": 60,
        }

        runner.add_server_from_dict("kit", config_data)

        # Verify the server config was stored correctly
        stored_config = runner.get_server_config("kit")
        assert stored_config is not None
        assert stored_config.initialization_timeout == 60

        # Verify it's included in server info
        server_info = runner.get_server_info("kit")
        assert server_info is not None
        assert server_info["initialization_timeout"] == 60

    @patch("e2b_mcp.runner.Sandbox")
    async def test_setup_uses_initialization_timeout(self, mock_sandbox_class):
        """Test that _setup_mcp_server uses the initialization_timeout."""
        # Create mock sandbox instance
        mock_sandbox = AsyncMock()
        mock_sandbox.sandbox_id = "test_sandbox_id"
        mock_sandbox_class.create.return_value = mock_sandbox

        # Mock the command execution
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_sandbox.commands.run.return_value = mock_process

        runner = E2BMCPRunner(api_key="test_key")

        # Add server with custom initialization timeout
        config = ServerConfig(name="kit", command="python -m kit.mcp", initialization_timeout=45)
        runner.add_server(config)

        # Test that the timeout is used in session creation
        # Note: This is a simplified test since the actual E2B integration
        # would require a real E2B environment
        async with runner.create_session("kit") as session:
            # Verify session was created with correct config
            assert session.config.initialization_timeout == 45

    def test_kit_specific_configuration(self):
        """Test Kit-specific initialization timeout configuration."""
        # Simulate the Kit configuration from Comet
        kit_config_data = {
            "command": "python -m kit.mcp",
            "description": "Codebase analysis and code search toolkit",
            "install_commands": ["pip install cased-kit"],
            "initialization_timeout": 45,  # Kit needs extra time
        }

        config = ServerConfig.from_dict("Kit", kit_config_data)

        # Verify Kit gets the longer timeout
        assert config.initialization_timeout == 45
        assert config.install_commands == ["pip install cased-kit"]

    def test_different_servers_different_timeouts(self):
        """Test that different servers can have different initialization timeouts."""
        runner = E2BMCPRunner(api_key="test_key")

        # Add multiple servers with different timeouts
        servers = {
            "fast_server": {
                "command": "python fast.py",
                "description": "Fast server",
                # No initialization_timeout specified - should use default
            },
            "slow_server": {
                "command": "python slow.py",
                "description": "Slow server",
                "initialization_timeout": 60,
            },
            "kit": {
                "command": "python -m kit.mcp",
                "description": "Kit server",
                "initialization_timeout": 45,
            },
        }

        runner.add_servers(servers)

        # Verify each server has correct timeout
        fast_config = runner.get_server_config("fast_server")
        assert fast_config.initialization_timeout == 30  # Default

        slow_config = runner.get_server_config("slow_server")
        assert slow_config.initialization_timeout == 60

        kit_config = runner.get_server_config("kit")
        assert kit_config.initialization_timeout == 45

    def test_initialization_timeout_in_to_dict(self):
        """Test that initialization_timeout is included in to_dict output."""
        # Default timeout
        config_default = ServerConfig(name="test", command="python test.py")
        data_default = config_default.to_dict()
        assert data_default["initialization_timeout"] == 30

        # Custom timeout
        config_custom = ServerConfig(
            name="test", command="python test.py", initialization_timeout=90
        )
        data_custom = config_custom.to_dict()
        assert data_custom["initialization_timeout"] == 90

    def test_round_trip_serialization(self):
        """Test that initialization_timeout survives round-trip serialization."""
        original_data = {
            "command": "python -m kit.mcp",
            "description": "Kit server",
            "initialization_timeout": 45,
            "install_commands": ["pip install cased-kit"],
        }

        # Create config from dict
        config = ServerConfig.from_dict("kit", original_data)

        # Convert back to dict
        serialized_data = config.to_dict()

        # Verify initialization_timeout is preserved
        assert serialized_data["initialization_timeout"] == 45
        assert serialized_data["command"] == "python -m kit.mcp"
        assert serialized_data["install_commands"] == ["pip install cased-kit"]

        # Create new config from serialized data
        config2 = ServerConfig.from_dict("kit", serialized_data)
        assert config2.initialization_timeout == 45
        assert config2.command == "python -m kit.mcp"
