#!/usr/bin/env python3
"""
Basic usage example for e2b-mcp.

This example shows how to:
1. Create an E2BMCPRunner
2. Configure MCP servers (individual and bulk)
3. Discover tools with validation
4. Execute tools safely in E2B sandboxes
5. Use parameter validation
6. Handle errors gracefully
"""
import asyncio
import os
from e2b_mcp import E2BMCPRunner, ServerConfig, MCPError


async def main():
    """Demonstrate basic e2b-mcp usage."""
    # Check for E2B API key
    if not os.getenv("E2B_API_KEY"):
        print("❌ Please set E2B_API_KEY environment variable")
        print("   Get your API key from https://e2b.dev")
        return

    print("🚀 E2B MCP Basic Usage Example")
    print("=" * 50)

    try:
        # 1. Create runner
        print("\n1️⃣ Creating E2B MCP Runner...")
        runner = E2BMCPRunner()
        print("✅ Runner created successfully")

        # 2. Add test server configuration
        print("\n2️⃣ Adding test MCP server...")
        test_config = ServerConfig(
            name="test",
            command="python /tmp/test_mcp_server.py",
            description="Simple test server with time, echo, and math tools",
            timeout_minutes=5
        )
        runner.add_server(test_config)
        print(f"✅ Added server: {test_config.name}")

        # 3. Bulk server configuration (new feature)
        print("\n3️⃣ Adding multiple servers at once...")
        bulk_configs = {
            "filesystem_example": {
                "command": "python -m mcp_server_filesystem --stdio",
                "package": "mcp-server-filesystem",
                "description": "File system operations",
                "timeout_minutes": 10
            },
            "git_example": {
                "command": "python -m mcp_server_git --stdio",
                "package": "mcp-server-git", 
                "description": "Git repository operations",
                "timeout_minutes": 8
            }
        }
        runner.add_servers(bulk_configs)
        print("✅ Added bulk server configurations")

        # 4. Server information (new feature)
        print("\n4️⃣ Server information:")
        for server_name in runner.list_servers():
            info = runner.get_server_info(server_name)
            print(f"   📋 {info['display_name']}")
            print(f"      Package required: {info['package_required']}")
            print(f"      Timeout: {info['timeout_minutes']} minutes")

        # 5. Discover tools from test server
        print("\n5️⃣ Discovering tools from test server...")
        tools = await runner.discover_tools("test")
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   🔧 {tool.name}: {tool.description}")
            print(f"      Required params: {tool.get_required_parameters()}")
            print(f"      Optional params: {tool.get_optional_parameters()}")

        # 6. Parameter validation (new feature)
        print("\n6️⃣ Testing parameter validation...")
        
        # Test valid parameters
        valid_params = {"format": "iso"}
        validation_errors = await runner.validate_tool_parameters("test", "get_time", valid_params)
        if not validation_errors:
            print("✅ Valid parameters passed validation")
        else:
            print(f"❌ Unexpected validation errors: {validation_errors}")

        # Test invalid parameters (missing required param)
        try:
            invalid_params = {}  # Missing required 'text' parameter
            validation_errors = await runner.validate_tool_parameters("test", "echo", invalid_params)
            if validation_errors:
                print(f"✅ Invalid parameters correctly caught: {validation_errors}")
            else:
                print("⚠️  Expected validation to fail but it passed")
        except MCPError as e:
            print(f"✅ Validation correctly failed: {e}")

        # 7. Execute tools with improved error handling
        print("\n7️⃣ Executing tools...")

        # Get current time
        print("\n🕒 Getting current time...")
        try:
            time_result = await runner.execute_tool("test", "get_time", {"format": "readable"})
            print(f"   Result: {time_result}")
        except MCPError as e:
            print(f"   ❌ Error: {e}")

        # Echo a message
        print("\n📢 Echoing a message...")
        try:
            echo_result = await runner.execute_tool("test", "echo", {"text": "Hello E2B MCP!"})
            print(f"   Result: {echo_result}")
        except MCPError as e:
            print(f"   ❌ Error: {e}")

        # Test with invalid parameters (should be caught by validation)
        print("\n🚫 Testing execution with invalid parameters...")
        try:
            # This should fail validation before execution
            await runner.execute_tool("test", "add_numbers", {"a": 42})  # Missing 'b' parameter
            print("   ⚠️  Expected this to fail but it succeeded")
        except MCPError as e:
            print(f"   ✅ Correctly caught parameter error: {e}")

        # Test with non-existent tool
        print("\n🚫 Testing execution with non-existent tool...")
        try:
            await runner.execute_tool("test", "nonexistent_tool", {})
            print("   ⚠️  Expected this to fail but it succeeded")
        except MCPError as e:
            print(f"   ✅ Correctly caught tool error: {e}")

        # 8. Session management info (new feature)
        print("\n8️⃣ Session management:")
        print(f"   Active sessions: {runner.get_active_session_count()}")
        sessions = runner.list_active_sessions()
        for session_info in sessions:
            print(f"   📊 Session {session_info['session_id'][:8]}...")
            print(f"      Server: {session_info['server_name']}")
            print(f"      Tools: {session_info['tool_count']}")

        print("\n🎉 All operations completed successfully!")

    except MCPError as e:
        print(f"\n❌ MCP Error: {e}")
        print(f"   Server: {getattr(e, 'server_name', 'unknown')}")
        print(f"   Tool: {getattr(e, 'tool_name', 'unknown')}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


def sync_example():
    """Demonstrate synchronous usage with improved error handling."""
    print("\n" + "=" * 50)
    print("🔄 Synchronous Usage Example")
    print("=" * 50)

    try:
        runner = E2BMCPRunner()

        # Add server
        runner.add_server_from_dict("sync_test", {
            "command": "python /tmp/test_mcp_server.py",
            "description": "Test server for sync example"
        })

        # Execute tool synchronously
        result = runner.execute_tool_sync("sync_test", "get_time", {"format": "iso"})
        print(f"✅ Sync execution result: {result}")

    except MCPError as e:
        print(f"❌ MCP Error in sync example: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in sync example: {e}")


def validation_example():
    """Demonstrate the new validation features."""
    print("\n" + "=" * 50)
    print("🔍 Parameter Validation Example") 
    print("=" * 50)

    try:
        # Test server config validation
        print("\n📋 Testing server configuration validation...")
        
        try:
            # This should work
            valid_config = ServerConfig(
                name="valid_server",
                command="python test.py",
                package="test-package",
                timeout_minutes=5
            )
            print("✅ Valid config created successfully")
        except ValueError as e:
            print(f"❌ Unexpected validation error: {e}")

        try:
            # This should fail - invalid server name
            invalid_config = ServerConfig(
                name="invalid server!",  # Spaces and special chars not allowed
                command="python test.py"
            )
            print("⚠️  Expected this to fail but it succeeded")
        except ValueError as e:
            print(f"✅ Invalid config correctly rejected: {e}")

        try:
            # This should fail - negative timeout
            invalid_config = ServerConfig(
                name="test",
                command="python test.py", 
                timeout_minutes=-5
            )
            print("⚠️  Expected this to fail but it succeeded")
        except ValueError as e:
            print(f"✅ Invalid timeout correctly rejected: {e}")

    except Exception as e:
        print(f"❌ Error in validation example: {e}")


if __name__ == "__main__":
    # Run async example
    asyncio.run(main())

    # Run sync example
    sync_example()

    # Run validation example
    validation_example()