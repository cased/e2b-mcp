"""
Tests for validation features in e2b-mcp.

This module tests all the new validation features including:
- Server configuration validation
- Tool parameter validation
- Error handling and context
- Input sanitization
"""
import pytest
from e2b_mcp import E2BMCPRunner, ServerConfig, Tool, MCPError


class TestServerConfigValidation:
    """Test server configuration validation."""

    def test_valid_server_config(self):
        """Test creating valid server configurations."""
        # Basic valid config
        config = ServerConfig(
            name="test_server",
            command="python test.py",
            description="Test server"
        )
        assert config.name == "test_server"
        assert config.command == "python test.py"
        assert config.timeout_minutes == 10  # default

        # Config with all fields
        config_full = ServerConfig(
            name="full_server",
            command="python -m server --stdio",
            package="test-package",
            description="Full test server",
            timeout_minutes=15,
            env={"DEBUG": "1", "API_KEY": "test"}
        )
        assert config_full.package == "test-package"
        assert config_full.timeout_minutes == 15
        assert config_full.env["DEBUG"] == "1"

    def test_invalid_server_names(self):
        """Test server name validation."""
        # Empty name
        with pytest.raises(ValueError, match="Server name must be a non-empty string"):
            ServerConfig(name="", command="python test.py")

        # None name
        with pytest.raises(ValueError, match="Server name must be a non-empty string"):
            ServerConfig(name=None, command="python test.py")

        # Invalid characters
        invalid_names = [
            "server with spaces",
            "server!",
            "server@home",
            "server#1",
            "server$",
            "server%",
            "server^",
            "server&",
            "server*",
            "server()",
            "server=",
            "server+",
            "server[",
            "server]",
            "server{",
            "server}",
            "server\\",
            "server|",
            "server;",
            "server:",
            "server'",
            "server\"",
            "server<",
            "server>",
            "server,",
            "server?",
            "server/",
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Server name must contain only alphanumeric"):
                ServerConfig(name=invalid_name, command="python test.py")

    def test_valid_server_names(self):
        """Test valid server name formats."""
        valid_names = [
            "server",
            "server1",
            "server_1",
            "server-1", 
            "test_server",
            "test-server",
            "MyServer",
            "my_server_123",
            "server-with-dashes",
            "server_with_underscores",
            "123server",
            "SERVER",
            "a",
            "a1",
            "a_1",
            "a-1",
        ]

        for valid_name in valid_names:
            config = ServerConfig(name=valid_name, command="python test.py")
            assert config.name == valid_name

    def test_invalid_commands(self):
        """Test command validation."""
        # Empty command
        with pytest.raises(ValueError, match="Server command must be a non-empty string"):
            ServerConfig(name="test", command="")

        # None command
        with pytest.raises(ValueError, match="Server command must be a non-empty string"):
            ServerConfig(name="test", command=None)

    def test_invalid_timeouts(self):
        """Test timeout validation."""
        # Zero timeout
        with pytest.raises(ValueError, match="Timeout must be a positive integer"):
            ServerConfig(name="test", command="python test.py", timeout_minutes=0)

        # Negative timeout
        with pytest.raises(ValueError, match="Timeout must be a positive integer"):
            ServerConfig(name="test", command="python test.py", timeout_minutes=-1)

        # Non-integer timeout
        with pytest.raises(ValueError, match="Timeout must be a positive integer"):
            ServerConfig(name="test", command="python test.py", timeout_minutes=5.5)

    def test_invalid_package_names(self):
        """Test package name validation."""
        invalid_packages = [
            "package with spaces",
            "package!",
            "package@",
            "package#",
            "package$",
            "package%",
            "package^",
            "package&",
            "package*",
            "package()",
            "package=",
            "package+",
            "package[",
            "package]",
            "package{",
            "package}",
            "package\\",
            "package|",
            "package;",
            "package:",
            "package'",
            "package\"",
            "package<",
            "package>",
            "package,",
            "package?",
            "package/",
        ]

        for invalid_package in invalid_packages:
            with pytest.raises(ValueError, match="Package name must contain only alphanumeric"):
                ServerConfig(
                    name="test", 
                    command="python test.py", 
                    package=invalid_package
                )

    def test_valid_package_names(self):
        """Test valid package name formats."""
        valid_packages = [
            "",  # Empty is allowed
            "package",
            "package1",
            "package_1",
            "package-1",
            "package.name",
            "my-package",
            "my_package",
            "my.package",
            "package.with.dots",
            "package-with-dashes",
            "package_with_underscores",
            "123package",
            "PACKAGE",
        ]

        for valid_package in valid_packages:
            config = ServerConfig(
                name="test", 
                command="python test.py", 
                package=valid_package
            )
            assert config.package == valid_package

    def test_from_dict_validation(self):
        """Test ServerConfig.from_dict validation."""
        # Valid dict
        data = {
            "command": "python test.py",
            "package": "test-package",
            "description": "Test",
            "timeout_minutes": 5,
            "env": {"TEST": "1"}
        }
        config = ServerConfig.from_dict("test", data)
        assert config.name == "test"
        assert config.command == "python test.py"

        # Missing command
        with pytest.raises(ValueError, match="Configuration must include 'command' field"):
            ServerConfig.from_dict("test", {"package": "test"})

        # Non-dict data
        with pytest.raises(ValueError, match="Configuration data must be a dictionary"):
            ServerConfig.from_dict("test", "not a dict")

        # None data
        with pytest.raises(ValueError, match="Configuration data must be a dictionary"):
            ServerConfig.from_dict("test", None)

    def test_utility_methods(self):
        """Test ServerConfig utility methods."""
        # Config without package
        config_no_pkg = ServerConfig(name="test", command="python test.py")
        assert not config_no_pkg.is_package_required()
        assert config_no_pkg.get_display_name() == "test"

        # Config with package
        config_with_pkg = ServerConfig(
            name="test", 
            command="python test.py", 
            package="my-package"
        )
        assert config_with_pkg.is_package_required()

        # Config with description
        config_with_desc = ServerConfig(
            name="test",
            command="python test.py",
            description="My awesome server"
        )
        assert config_with_desc.get_display_name() == "My awesome server"

        # Config with empty package should work fine
        config_empty_pkg = ServerConfig(
            name="test",
            command="python test.py",
            package=""  # Empty string instead of whitespace
        )
        assert not config_empty_pkg.is_package_required()


class TestToolValidation:
    """Test tool validation features."""

    def test_valid_tool_creation(self):
        """Test creating valid tools."""
        # Basic tool
        tool = Tool(name="test_tool", description="Test tool")
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        assert tool.input_schema == {}
        assert tool.server_name == ""

        # Tool with schema
        schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "integer", "description": "Second parameter"}
            },
            "required": ["param1"]
        }
        tool_with_schema = Tool(
            name="complex_tool",
            description="Complex tool",
            input_schema=schema,
            server_name="test_server"
        )
        assert tool_with_schema.input_schema == schema
        assert tool_with_schema.server_name == "test_server"

    def test_invalid_tool_creation(self):
        """Test tool validation errors."""
        # Empty name
        with pytest.raises(ValueError, match="Tool name must be a non-empty string"):
            Tool(name="", description="Test")

        # None name
        with pytest.raises(ValueError, match="Tool name must be a non-empty string"):
            Tool(name=None, description="Test")

        # Invalid schema type
        with pytest.raises(ValueError, match="Input schema must be a dictionary"):
            Tool(name="test", description="Test", input_schema="not a dict")

    def test_from_mcp_tool(self):
        """Test Tool.from_mcp_tool method."""
        # Valid MCP tool data
        mcp_data = {
            "name": "test_tool",
            "description": "Test tool from MCP",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                }
            }
        }
        tool = Tool.from_mcp_tool(mcp_data, "test_server")
        assert tool.name == "test_tool"
        assert tool.description == "Test tool from MCP"
        assert tool.server_name == "test_server"

        # Missing name
        with pytest.raises(ValueError, match="Tool data must include 'name' field"):
            Tool.from_mcp_tool({"description": "Test"}, "server")

        # Non-dict data
        with pytest.raises(ValueError, match="Tool data must be a dictionary"):
            Tool.from_mcp_tool("not a dict", "server")

    def test_parameter_extraction(self):
        """Test parameter extraction methods."""
        schema = {
            "type": "object",
            "properties": {
                "required_param": {"type": "string", "description": "Required parameter"},
                "optional_param": {"type": "integer", "description": "Optional parameter"},
                "another_required": {"type": "boolean", "description": "Another required"}
            },
            "required": ["required_param", "another_required"]
        }
        
        tool = Tool(name="test", description="Test", input_schema=schema)
        
        # Test required parameters
        required = tool.get_required_parameters()
        assert set(required) == {"required_param", "another_required"}
        
        # Test optional parameters
        optional = tool.get_optional_parameters()
        assert set(optional) == {"optional_param"}
        
        # Test parameter info
        param_info = tool.get_parameter_info("required_param")
        assert param_info["type"] == "string"
        assert param_info["description"] == "Required parameter"
        
        # Non-existent parameter
        assert tool.get_parameter_info("nonexistent") is None

    def test_parameter_validation(self):
        """Test parameter validation against schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name parameter"},
                "age": {"type": "integer", "description": "Age parameter"},
                "active": {"type": "boolean", "description": "Active parameter"},
                "tags": {"type": "array", "description": "Tags parameter"},
                "config": {"type": "object", "description": "Config parameter"}
            },
            "required": ["name", "age"]
        }
        
        tool = Tool(name="test", description="Test", input_schema=schema)
        
        # Valid parameters
        valid_params = {"name": "test", "age": 25, "active": True}
        errors = tool.validate_parameters(valid_params)
        assert errors == []
        
        # Missing required parameter
        missing_required = {"name": "test"}  # missing age
        errors = tool.validate_parameters(missing_required)
        assert len(errors) == 1
        assert "Missing required parameter: age" in errors
        
        # Wrong type
        wrong_type = {"name": "test", "age": "not an integer"}
        errors = tool.validate_parameters(wrong_type)
        assert len(errors) == 1
        assert "should be of type integer" in errors[0]
        
        # Multiple errors
        multiple_errors = {"age": "not an integer"}  # missing name, wrong type
        errors = tool.validate_parameters(multiple_errors)
        assert len(errors) == 2
        
        # Valid with all types
        all_types = {
            "name": "test",
            "age": 25,
            "active": True,
            "tags": ["tag1", "tag2"],
            "config": {"key": "value"}
        }
        errors = tool.validate_parameters(all_types)
        assert errors == []

    def test_tool_utility_methods(self):
        """Test tool utility methods."""
        tool = Tool(
            name="test_tool",
            description="Test tool",
            server_name="test_server"
        )
        
        # Full name
        assert tool.get_full_name() == "test_server.test_tool"
        
        # Tool without server
        tool_no_server = Tool(name="tool", description="Test")
        assert tool_no_server.get_full_name() == "tool"


class TestMCPErrorHandling:
    """Test improved error handling."""

    def test_mcp_error_with_context(self):
        """Test MCPError with server and tool context."""
        # Basic error
        error = MCPError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.server_name is None
        assert error.tool_name is None

        # Error with server context
        error_with_server = MCPError("Server error", server_name="test_server")
        assert "server=test_server" in str(error_with_server)
        assert error_with_server.server_name == "test_server"

        # Error with tool context
        error_with_tool = MCPError("Tool error", tool_name="test_tool")
        assert "tool=test_tool" in str(error_with_tool)
        assert error_with_tool.tool_name == "test_tool"

        # Error with both contexts
        error_with_both = MCPError(
            "Full error", 
            server_name="test_server", 
            tool_name="test_tool"
        )
        error_str = str(error_with_both)
        assert "server=test_server" in error_str
        assert "tool=test_tool" in error_str
        assert error_with_both.server_name == "test_server"
        assert error_with_both.tool_name == "test_tool"

    def test_error_inheritance(self):
        """Test that MCPError properly inherits from Exception."""
        error = MCPError("Test error")
        assert isinstance(error, Exception)
        
        # Can be caught as Exception
        try:
            raise MCPError("Test")
        except Exception as e:
            assert isinstance(e, MCPError)


class TestRunnerValidation:
    """Test validation features in E2BMCPRunner."""

    def test_runner_creation_validation(self):
        """Test runner creation with API key validation."""
        # Valid runner with explicit key
        runner = E2BMCPRunner(api_key="test_key")
        assert runner.api_key == "test_key"

        # No API key should raise error
        import os
        original_env = os.environ.get("E2B_API_KEY")
        if "E2B_API_KEY" in os.environ:
            del os.environ["E2B_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="E2B_API_KEY is required"):
                E2BMCPRunner()
        finally:
            if original_env:
                os.environ["E2B_API_KEY"] = original_env

    def test_bulk_server_configuration(self):
        """Test bulk server configuration."""
        runner = E2BMCPRunner(api_key="test_key")
        
        configs = {
            "server1": {
                "command": "python server1.py",
                "description": "First server"
            },
            "server2": {
                "command": "python server2.py",
                "package": "test-package",
                "timeout_minutes": 15
            }
        }
        
        runner.add_servers(configs)
        
        assert len(runner.list_servers()) == 2
        assert "server1" in runner.list_servers()
        assert "server2" in runner.list_servers()
        
        # Check individual configs
        config1 = runner.get_server_config("server1")
        assert config1.command == "python server1.py"
        assert config1.description == "First server"
        
        config2 = runner.get_server_config("server2")
        assert config2.package == "test-package"
        assert config2.timeout_minutes == 15

    def test_server_info_method(self):
        """Test get_server_info method."""
        runner = E2BMCPRunner(api_key="test_key")
        
        config = ServerConfig(
            name="test_server",
            command="python test.py",
            package="test-package",
            description="Test server",
            timeout_minutes=20,
            env={"DEBUG": "1", "API_KEY": "test"}
        )
        runner.add_server(config)
        
        info = runner.get_server_info("test_server")
        assert info is not None
        assert info["name"] == "test_server"
        assert info["command"] == "python test.py"
        assert info["package"] == "test-package"
        assert info["description"] == "Test server"
        assert info["timeout_minutes"] == 20
        assert info["package_required"] is True
        assert info["display_name"] == "Test server"
        assert set(info["env_vars"]) == {"DEBUG", "API_KEY"}
        
        # Non-existent server
        assert runner.get_server_info("nonexistent") is None

    def test_session_management_methods(self):
        """Test session management utility methods."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Initially no sessions
        assert runner.get_active_session_count() == 0
        assert runner.list_active_sessions() == [] 