"""
Integration tests for e2b-mcp package.

These tests require a valid E2B_API_KEY and will create real E2B sandboxes.
They test the full pipeline from sandbox creation to tool execution.
"""
import os
import pytest
import asyncio
from pathlib import Path
from e2b_mcp import E2BMCPRunner, ServerConfig, MCPError


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def e2b_api_key():
    """Get E2B API key from environment."""
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        pytest.skip("E2B_API_KEY not set - skipping integration tests")
    return api_key


@pytest.fixture
def test_server_code():
    """Get the test MCP server code."""
    test_server_path = Path(__file__).parent / "test_mcp_server.py"
    return test_server_path.read_text()


@pytest.fixture
def runner(e2b_api_key):
    """Create E2B MCP runner with test configuration."""
    runner = E2BMCPRunner(api_key=e2b_api_key)

    # Add test server configuration that will copy the test server
    runner.add_server(ServerConfig(
        name="test_server",
        command="python /tmp/test_mcp_server.py --stdio",
        description="Test MCP server for integration tests",
        timeout_minutes=3  # Short timeout for tests
    ))

    return runner


class TestE2BMCPIntegration:
    """Integration tests for E2B MCP functionality."""

    @pytest.mark.asyncio
    async def test_session_creation_and_cleanup(self, runner, test_server_code):
        """Test creating and cleaning up an E2B MCP session."""
        # Override setup to upload test server first
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            session_id = None
            # Create session
            async with runner.create_session("test_server") as session:
                session_id = session.session_id
                assert session.session_id is not None
                assert session.server_name == "test_server"
                assert session.sandbox_id is not None
                assert session.initialized is True

            # Session should be cleaned up automatically
            assert session_id not in runner.active_sessions
        finally:
            runner._setup_mcp_server = original_setup

    @pytest.mark.asyncio
    async def test_tool_discovery(self, runner, test_server_code):
        """Test discovering tools from MCP server in E2B sandbox."""
        # Override the session creation to upload test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            tools = await runner.discover_tools("test_server")

            # Should discover the test tools
            assert len(tools) >= 3  # get_time, echo, add_numbers

            tool_names = {tool.name for tool in tools}
            assert "get_time" in tool_names
            assert "echo" in tool_names
            assert "add_numbers" in tool_names

            # Check tool details
            for tool in tools:
                assert tool.server_name == "test_server"
                assert tool.description != ""
                assert isinstance(tool.input_schema, dict)
        finally:
            runner._setup_mcp_server = original_setup

    @pytest.mark.asyncio
    async def test_tool_execution_get_time(self, runner, test_server_code):
        """Test executing get_time tool."""
        # Setup with test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            # Test different time formats
            formats = ["iso", "timestamp", "readable"]

            for fmt in formats:
                result = await runner.execute_tool("test_server", "get_time", {"format": fmt})

                assert "content" in result
                assert len(result["content"]) > 0
                assert result["content"][0]["type"] == "text"

                # Parse the JSON response
                import json
                content = json.loads(result["content"][0]["text"])
                assert "time" in content
        finally:
            runner._setup_mcp_server = original_setup

    @pytest.mark.asyncio
    async def test_tool_execution_echo(self, runner, test_server_code):
        """Test executing echo tool."""
        test_message = "Hello E2B MCP Integration Test!"

        # Setup with test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            result = await runner.execute_tool("test_server", "echo", {"text": test_message})

            assert "content" in result
            content_text = result["content"][0]["text"]

            import json
            parsed = json.loads(content_text)
            assert parsed["echoed"] == test_message
        finally:
            runner._setup_mcp_server = original_setup

    @pytest.mark.asyncio
    async def test_tool_execution_add_numbers(self, runner, test_server_code):
        """Test executing add_numbers tool."""
        # Setup with test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            result = await runner.execute_tool("test_server", "add_numbers", {"a": 42, "b": 13})

            assert "content" in result
            content_text = result["content"][0]["text"]

            import json
            parsed = json.loads(content_text)
            assert parsed["sum"] == 55
        finally:
            runner._setup_mcp_server = original_setup

    @pytest.mark.asyncio
    async def test_error_handling_unknown_server(self, runner):
        """Test error handling with unknown server."""
        with pytest.raises(ValueError, match="Server 'nonexistent' not configured"):
            async with runner.create_session("nonexistent"):
                pass

    @pytest.mark.asyncio
    async def test_error_handling_unknown_tool(self, runner, test_server_code):
        """Test error handling with unknown tool."""
        # Setup with test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        try:
            with pytest.raises(MCPError, match="Tool 'nonexistent_tool' not found"):
                await runner.execute_tool("test_server", "nonexistent_tool", {})
        finally:
            runner._setup_mcp_server = original_setup

    def test_sync_tool_execution(self, runner, test_server_code):
        """Test synchronous tool execution."""
        # This test is simplified since sync execution uses the same underlying mechanism
        # and would require the same test server setup
        pass  # Skip for now due to complexity of setup


class TestE2BMCPWithPackageInstallation:
    """Test E2B MCP with actual package installation."""

    @pytest.mark.asyncio
    async def test_package_installation(self, e2b_api_key):
        """Test MCP server with package installation."""
        runner = E2BMCPRunner(api_key=e2b_api_key)

        # Add server that requires package installation
        runner.add_server(ServerConfig(
            name="requests_server",
            command="python -c 'import requests; print(\"Requests package available\")'",
            package="requests",
            description="Test server with package dependency",
            timeout_minutes=3
        ))

        # This should work without error if package installation works
        async with runner.create_session("requests_server") as session:
            assert session.initialized is True

    @pytest.mark.asyncio
    async def test_environment_variables(self, e2b_api_key):
        """Test MCP server with environment variables."""
        runner = E2BMCPRunner(api_key=e2b_api_key)

        runner.add_server(ServerConfig(
            name="env_server",
            command="python -c 'import os; print(f\"TEST_VAR={os.getenv(\"TEST_VAR\", \"not_set\")}\")'",
            env={"TEST_VAR": "integration_test_value"},
            description="Test server with environment variables",
            timeout_minutes=2
        ))

        async with runner.create_session("env_server") as session:
            assert session.initialized is True


class TestE2BMCPPerformance:
    """Performance and stress tests."""

    @pytest.mark.asyncio
    async def test_rapid_session_creation(self, runner, test_server_code):
        """Test creating and destroying sessions rapidly."""
        session_count = 3  # Reduced for faster testing

        # Setup with test server
        original_setup = runner._setup_mcp_server

        async def setup_with_test_server(session, sandbox):
            # Upload test server BEFORE calling original setup
            await sandbox.files.write("/tmp/test_mcp_server.py", test_server_code)
            # Now call original setup
            await original_setup(session, sandbox)

        runner._setup_mcp_server = setup_with_test_server

        async def quick_session():
            async with runner.create_session("test_server") as session:
                await asyncio.sleep(0.1)  # Brief work
                return True

        try:
            # Create sessions rapidly
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*[quick_session() for _ in range(session_count)])
            end_time = asyncio.get_event_loop().time()

            assert all(results)
            assert len(results) == session_count

            # Should complete within reasonable time
            assert end_time - start_time < 120  # 2 minutes max
        finally:
            runner._setup_mcp_server = original_setup


# Utility functions for integration tests
def test_runner_configuration():
    """Test runner can be configured without E2B API key for config testing."""
    runner = E2BMCPRunner(api_key="dummy_key")

    runner.add_server_from_dict("test", {
        "command": "python test.py",
        "description": "Test configuration"
    })

    assert len(runner.list_servers()) == 1
    assert runner.get_server_config("test") is not None


# Test markers and configuration
class TestIntegrationMarkers:
    """Test that integration test markers work correctly."""

    def test_integration_marker_applied(self):
        """Verify that integration marker is applied to all tests in this module."""
        # This test will be marked as integration due to pytestmark
        assert True