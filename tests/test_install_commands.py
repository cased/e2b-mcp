"""
Tests for the install_commands functionality.

These tests verify that the ServerConfig properly handles installation
commands for different package managers.
"""

import pytest

from e2b_mcp.models import ServerConfig


class TestInstallCommands:
    """Test the install_commands functionality."""

    def test_no_installation_required(self):
        """Test when no installation is needed."""
        config = ServerConfig(
            name="test_server",
            command="./prebuilt_server",
        )

        assert config.install_commands == []
        assert config.requires_installation() is False

    def test_install_commands(self):
        """Test the install_commands field."""
        config = ServerConfig(
            name="test_server",
            command="node server.js",
            install_commands=[
                "apt-get update",
                "apt-get install -y nodejs npm",
                "npm install express",
            ],
        )

        assert len(config.install_commands) == 3
        assert config.requires_installation() is True

        assert config.install_commands == [
            "apt-get update",
            "apt-get install -y nodejs npm",
            "npm install express",
        ]

    def test_from_dict_with_install_commands(self):
        """Test creating ServerConfig from dict with install_commands."""
        data = {
            "command": "node server.js",
            "install_commands": [
                "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
                "sudo apt-get install -y nodejs",
                "npm install express",
            ],
            "description": "Node.js server with npm packages",
        }

        config = ServerConfig.from_dict("nodejs_server", data)

        assert config.name == "nodejs_server"
        assert config.command == "node server.js"
        assert len(config.install_commands) == 3
        assert config.description == "Node.js server with npm packages"

    def test_to_dict_includes_install_commands(self):
        """Test that to_dict includes install_commands."""
        config = ServerConfig(
            name="test_server",
            command="cargo run",
            install_commands=[
                "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
                "cargo build --release",
            ],
        )

        data = config.to_dict()

        assert "install_commands" in data
        assert data["install_commands"] == [
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            "cargo build --release",
        ]

    def test_install_commands_validation(self):
        """Test validation of install_commands."""
        # Should accept list of strings
        config = ServerConfig(
            name="test_server",
            command="test",
            install_commands=["pip install requests", "apt-get update"],
        )
        assert len(config.install_commands) == 2

        # Should reject non-list
        with pytest.raises(ValueError, match="install_commands must be a list"):
            ServerConfig(
                name="test_server",
                command="test",
                install_commands="not a list",  # type: ignore
            )

        # Should reject non-string elements
        with pytest.raises(ValueError, match="install_commands\\[0\\] must be a string"):
            ServerConfig(name="test_server", command="test", install_commands=[123])  # type: ignore

    def test_complex_real_world_example(self):
        """Test a complex real-world configuration."""
        config = ServerConfig(
            name="complex_mcp_server",
            command="python /app/mcp_server.py --stdio",
            install_commands=[
                # System dependencies
                "apt-get update",
                "apt-get install -y curl git build-essential",
                # Python packages
                "pip install --upgrade pip setuptools",
                "pip install requests lxml pandas beautifulsoup4",
                # Setup directories
                "mkdir -p /app/data /app/logs",
                "chmod 755 /app/data /app/logs",
            ],
            env={"MCP_DATA_DIR": "/app/data", "MCP_LOG_LEVEL": "INFO"},
            timeout_minutes=15,
        )

        expected_commands = [
            "apt-get update",
            "apt-get install -y curl git build-essential",
            "pip install --upgrade pip setuptools",
            "pip install requests lxml pandas beautifulsoup4",
            "mkdir -p /app/data /app/logs",
            "chmod 755 /app/data /app/logs",
        ]

        assert config.install_commands == expected_commands
        assert config.requires_installation() is True
        assert len(config.env) == 2
        assert config.timeout_minutes == 15

    def test_python_packages(self):
        """Test Python package installation."""
        config = ServerConfig(
            name="python_server",
            command="python server.py",
            install_commands=[
                "pip install --upgrade pip",
                "pip install fastapi uvicorn pandas numpy",
            ],
        )

        assert config.requires_installation() is True
        assert "pip install fastapi uvicorn pandas numpy" in config.install_commands

    def test_nodejs_packages(self):
        """Test Node.js package installation."""
        config = ServerConfig(
            name="nodejs_server",
            command="node mcp-server.js",
            install_commands=[
                "apt-get update",
                "apt-get install -y nodejs npm",
                "npm install express sqlite3",
            ],
        )

        assert config.requires_installation() is True
        assert "npm install express sqlite3" in config.install_commands

    def test_system_dependencies(self):
        """Test system dependency installation."""
        config = ServerConfig(
            name="system_server",
            command="python git_server.py",
            install_commands=[
                "apt-get update",
                "apt-get install -y git curl wget",
                "pip install gitpython",
            ],
        )

        assert config.requires_installation() is True
        assert "apt-get install -y git curl wget" in config.install_commands
