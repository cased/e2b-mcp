"""
Edge case tests for e2b-mcp.

This module tests various edge cases, error scenarios, and boundary conditions
that might not be covered in basic testing.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from e2b_mcp import E2BMCPRunner, ServerConfig, Tool, Session, MCPError


class TestEdgeCases:
    """Test various edge cases and boundary conditions."""

    def test_empty_configurations(self):
        """Test handling of empty or minimal configurations."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Empty bulk configuration
        runner.add_servers({})
        assert len(runner.list_servers()) == 0
        
        # Minimal server config
        minimal_config = ServerConfig(name="minimal", command="echo hello")
        runner.add_server(minimal_config)
        assert minimal_config.package == ""
        assert minimal_config.description == ""
        assert minimal_config.env == {}

    def test_unicode_and_special_strings(self):
        """Test handling of unicode and special string content."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Unicode in descriptions
        config = ServerConfig(
            name="unicode_test",
            command="python test.py",
            description="Test with unicode: 🚀 ñáéíóú 中文 🎉",
            env={"UNICODE_VAR": "🌟 Special value 🌟"}
        )
        runner.add_server(config)
        
        info = runner.get_server_info("unicode_test")
        assert "🚀" in info["description"]
        assert "UNICODE_VAR" in info["env_vars"]  # Check the key name is present

    def test_very_long_strings(self):
        """Test handling of very long strings."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Very long command
        long_command = "python " + "very_long_script_name_" * 50 + ".py"
        long_description = "This is a very long description. " * 100
        
        config = ServerConfig(
            name="long_test",
            command=long_command,
            description=long_description
        )
        runner.add_server(config)
        
        info = runner.get_server_info("long_test")
        assert len(info["command"]) > 1000
        assert len(info["description"]) > 1000

    def test_extreme_timeout_values(self):
        """Test handling of extreme timeout values."""
        # Very large timeout (should work)
        config = ServerConfig(
            name="long_timeout",
            command="python test.py",
            timeout_minutes=999999
        )
        assert config.timeout_minutes == 999999

    def test_complex_environment_variables(self):
        """Test complex environment variable scenarios."""
        complex_env = {
            "SIMPLE": "value",
            "WITH_SPACES": "value with spaces",
            "WITH_QUOTES": 'value with "quotes"',
            "WITH_EQUALS": "key=value=more",
            "WITH_NEWLINES": "line1\nline2",
            "EMPTY": "",
            "NUMERIC": "123",
            "BOOLEAN_LIKE": "true",
            "PATH_LIKE": "/path/to/something:/another/path",
            "URL_LIKE": "https://example.com:8080/path?query=value",
            "JSON_LIKE": '{"key": "value", "number": 42}',
        }
        
        config = ServerConfig(
            name="complex_env",
            command="python test.py",
            env=complex_env
        )
        
        # Should not raise errors
        assert len(config.env) == len(complex_env)
        for key, value in complex_env.items():
            assert config.env[key] == value

    def test_tool_with_complex_schemas(self):
        """Test tools with complex JSON schemas."""
        complex_schema = {
            "type": "object",
            "properties": {
                "nested_object": {
                    "type": "object",
                    "properties": {
                        "inner_string": {"type": "string"},
                        "inner_array": {
                            "type": "array",
                            "items": {"type": "integer"}
                        }
                    },
                    "required": ["inner_string"]
                },
                "array_of_objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    }
                },
                "optional_enum": {
                    "type": "string",
                    "enum": ["option1", "option2", "option3"]
                },
                "number_with_constraints": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["nested_object", "array_of_objects"]
        }
        
        tool = Tool(
            name="complex_tool",
            description="Tool with complex schema",
            input_schema=complex_schema
        )
        
        # Test parameter extraction
        required = tool.get_required_parameters()
        assert set(required) == {"nested_object", "array_of_objects"}
        
        optional = tool.get_optional_parameters()
        assert set(optional) == {"optional_enum", "number_with_constraints"}

    def test_tool_schema_edge_cases(self):
        """Test edge cases in tool schema handling."""
        # Tool with empty schema
        empty_tool = Tool(name="empty", description="Empty tool")
        assert empty_tool.get_required_parameters() == []
        assert empty_tool.get_optional_parameters() == []
        assert empty_tool.validate_parameters({}) == []
        
        # Tool with schema but no properties
        no_props_schema = {"type": "object"}
        no_props_tool = Tool(
            name="no_props",
            description="No properties",
            input_schema=no_props_schema
        )
        assert no_props_tool.get_required_parameters() == []
        assert no_props_tool.get_optional_parameters() == []
        
        # Tool with invalid required field type
        invalid_required_schema = {
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": "not_a_list"  # Should be a list
        }
        invalid_tool = Tool(
            name="invalid",
            description="Invalid required",
            input_schema=invalid_required_schema
        )
        # Should handle gracefully
        assert invalid_tool.get_required_parameters() == []

    def test_parameter_validation_edge_cases(self):
        """Test edge cases in parameter validation."""
        schema = {
            "type": "object",
            "properties": {
                "string_param": {"type": "string"},
                "number_param": {"type": "number"},
                "unknown_type": {"type": "unknown_type"}  # Unknown type
            },
            "required": ["string_param"]
        }
        
        tool = Tool(name="test", description="Test", input_schema=schema)
        
        # Unknown type should be skipped in validation
        params_with_unknown = {
            "string_param": "valid",
            "unknown_type": "anything"  # Should not cause validation error
        }
        errors = tool.validate_parameters(params_with_unknown)
        assert errors == []
        
        # Test with None values
        params_with_none = {
            "string_param": None,  # None where string expected
            "number_param": None   # None where number expected
        }
        errors = tool.validate_parameters(params_with_none)
        # Should detect type mismatches
        assert len(errors) >= 1

    def test_session_validation_edge_cases(self):
        """Test Session validation with edge cases."""
        config = ServerConfig(name="test", command="python test.py")
        
        # Test with empty strings
        with pytest.raises(ValueError):
            Session(
                session_id="",  # Empty session ID
                server_name="test",
                config=config,
                sandbox_id="sandbox123"
            )
        
        with pytest.raises(ValueError):
            Session(
                session_id="session123",
                server_name="",  # Empty server name
                config=config,
                sandbox_id="sandbox123"
            )

    def test_mcp_error_edge_cases(self):
        """Test MCPError with edge cases."""
        # Error with empty context
        error = MCPError("Test", server_name="", tool_name="")
        # Should not include empty context in message
        assert "server=" not in str(error)
        assert "tool=" not in str(error)
        
        # Error with None context
        error_none = MCPError("Test", server_name=None, tool_name=None)
        assert "server=" not in str(error_none)
        assert "tool=" not in str(error_none)
        
        # Error with very long message
        long_message = "Error: " + "x" * 10000
        long_error = MCPError(long_message)
        assert len(str(long_error)) > 10000


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and potential race conditions."""

    def test_concurrent_server_configuration(self):
        """Test adding servers concurrently."""
        runner = E2BMCPRunner(api_key="test_key")
        
        def add_server(i):
            config = ServerConfig(
                name=f"server_{i}",
                command=f"python server_{i}.py"
            )
            runner.add_server(config)
        
        # Add servers "concurrently" (simulated)
        for i in range(10):
            add_server(i)
        
        assert len(runner.list_servers()) == 10
        for i in range(10):
            assert f"server_{i}" in runner.list_servers()

    def test_duplicate_server_names(self):
        """Test handling of duplicate server names."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Add server
        config1 = ServerConfig(name="duplicate", command="python test1.py")
        runner.add_server(config1)
        
        # Add server with same name (should overwrite)
        config2 = ServerConfig(name="duplicate", command="python test2.py")
        runner.add_server(config2)
        
        # Should only have one server with that name
        servers = runner.list_servers()
        assert servers.count("duplicate") == 1
        
        # Should have the second configuration
        final_config = runner.get_server_config("duplicate")
        assert final_config.command == "python test2.py"


class TestErrorRecovery:
    """Test error recovery and cleanup scenarios."""

    def test_partial_bulk_configuration_failure(self):
        """Test bulk configuration with some invalid configs."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Mix of valid and invalid configs
        mixed_configs = {
            "valid1": {
                "command": "python valid1.py"
            },
            "invalid": {
                # Missing required "command" field
                "description": "Invalid config"
            },
            "valid2": {
                "command": "python valid2.py"
            }
        }
        
        # Should raise error due to invalid config
        with pytest.raises(ValueError):
            runner.add_servers(mixed_configs)
        
        # Check that no servers were added (atomic operation)
        assert len(runner.list_servers()) == 0

    @patch('e2b_mcp.runner.Sandbox')
    def test_sandbox_creation_failure_recovery(self, mock_sandbox_class):
        """Test recovery when sandbox creation fails."""
        runner = E2BMCPRunner(api_key="test_key")
        
        config = ServerConfig(name="test", command="python test.py")
        runner.add_server(config)
        
        # Mock sandbox creation to fail
        mock_sandbox_class.side_effect = Exception("Sandbox creation failed")
        
        async def test_session_failure():
            with pytest.raises(MCPError):
                async with runner.create_session("test"):
                    pass  # Should not reach here
            
            # Session should not be in active sessions
            assert runner.get_active_session_count() == 0
        
        # Run the async test
        asyncio.run(test_session_failure())

    def test_invalid_mcp_tool_data_recovery(self):
        """Test recovery from invalid MCP tool data."""
        # Invalid tool data scenarios
        invalid_tool_data_cases = [
            {},  # Missing name
            {"name": ""},  # Empty name
            {"name": "tool", "inputSchema": "not a dict"},  # Invalid schema
            None,  # None data
            "not a dict",  # Wrong type
        ]
        
        for invalid_data in invalid_tool_data_cases:
            with pytest.raises(ValueError):
                Tool.from_mcp_tool(invalid_data, "test_server")


class TestMemoryAndResourceLeaks:
    """Test for potential memory leaks and resource management."""

    def test_session_cleanup_tracking(self):
        """Test that sessions are properly tracked and cleaned up."""
        runner = E2BMCPRunner(api_key="test_key")
        
        config = ServerConfig(name="test", command="python test.py")
        runner.add_server(config)
        
        # Check initial state
        assert runner.get_active_session_count() == 0
        assert len(runner.active_sessions) == 0
        
        # Note: This test would need actual E2B integration to fully test
        # session cleanup, so we just test the tracking mechanisms

    def test_large_number_of_configurations(self):
        """Test handling of large numbers of server configurations."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Add many server configurations
        num_servers = 1000
        for i in range(num_servers):
            config = ServerConfig(
                name=f"server_{i:04d}",
                command=f"python server_{i}.py",
                description=f"Server number {i}"
            )
            runner.add_server(config)
        
        # Verify all were added
        assert len(runner.list_servers()) == num_servers
        
        # Test bulk operations still work
        info_list = [runner.get_server_info(f"server_{i:04d}") for i in range(0, 100)]
        assert all(info is not None for info in info_list)

    def test_tools_with_large_schemas(self):
        """Test tools with very large input schemas."""
        # Create a large schema
        large_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add many properties
        for i in range(1000):
            prop_name = f"property_{i:04d}"
            large_schema["properties"][prop_name] = {
                "type": "string",
                "description": f"Property number {i}"
            }
            if i % 2 == 0:  # Make every other property required
                large_schema["required"].append(prop_name)
        
        tool = Tool(
            name="large_tool",
            description="Tool with large schema",
            input_schema=large_schema
        )
        
        # Test parameter extraction still works
        required = tool.get_required_parameters()
        optional = tool.get_optional_parameters()
        
        assert len(required) == 500  # Half are required
        assert len(optional) == 500  # Half are optional
        assert len(required) + len(optional) == 1000


class TestAsyncBehavior:
    """Test async-specific behavior and edge cases."""

    def test_sync_wrapper_error_conditions(self):
        """Test sync wrapper under various error conditions."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Test calling sync method when already in async context
        async def test_nested_call():
            # This should raise an error - either our custom error or asyncio's error
            with pytest.raises(RuntimeError, match="Cannot run the event loop"):
                runner.execute_tool_sync("server", "tool", {})
        
        # Run the test
        asyncio.run(test_nested_call())

    def test_event_loop_edge_cases(self):
        """Test edge cases with event loop handling."""
        runner = E2BMCPRunner(api_key="test_key")
        
        # Test when no event loop exists
        original_get_event_loop = asyncio.get_event_loop
        
        def mock_no_loop():
            raise RuntimeError("No event loop")
        
        with patch('asyncio.get_event_loop', side_effect=mock_no_loop):
            with patch('asyncio.new_event_loop') as mock_new_loop:
                with patch('asyncio.set_event_loop') as mock_set_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop
                    mock_loop.run_until_complete.return_value = {"result": "test"}
                    
                    # Should create new event loop
                    result = runner.execute_tool_sync("server", "tool", {})
                    
                    mock_new_loop.assert_called_once()
                    mock_set_loop.assert_called_once_with(mock_loop)
                    assert result == {"result": "test"} 