#!/usr/bin/env python3
"""
Filesystem MCP Server Integration Example

This example demonstrates how to use e2b-mcp with the official filesystem MCP server
to safely interact with files and directories within E2B sandboxes.

The filesystem server provides secure file operations with configurable access controls.

Usage:
    python examples/filesystem_integration.py
"""
import asyncio
from e2b_mcp import E2BMCPRunner


async def main():
    """Demonstrate filesystem MCP server integration."""
    
    print("🗂️  Filesystem MCP Server Integration Example")
    print("=" * 50)
    
    # Initialize E2B MCP runner
    runner = E2BMCPRunner()
    
    # Configure filesystem MCP server
    # The filesystem server allows safe file operations within the sandbox
    # Using /tmp as the root since it always exists in E2B sandboxes
    filesystem_config = {
        "command": "npx -y @modelcontextprotocol/server-filesystem /tmp",
        "env": {}
    }
    
    runner.add_server_from_dict("filesystem", filesystem_config)
    
    try:
        print("\n🔧 Discovering filesystem tools...")
        tools = await runner.discover_tools("filesystem")
        print(f"✅ Found {len(tools)} filesystem tools:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")
        
        # Example 1: Create a directory structure
        print("\n📁 Example 1: Create directory structure")
        try:
            # First create the workspace directory
            workspace_result = await runner.execute_tool("filesystem", "create_directory", {
                "path": "/tmp/workspace"
            })
            print("📂 Created workspace directory")
            
            # Then create the projects subdirectory
            projects_result = await runner.execute_tool("filesystem", "create_directory", {
                "path": "/tmp/workspace/projects"
            })
            print("📂 Created projects directory")
            print(f"   Result: {projects_result}")
        except Exception as e:
            print(f"  ❌ Directory creation failed: {e}")
        
        # Example 2: Write files
        print("\n📝 Example 2: Write project files")
        try:
            # Create a Python file
            write_result = await runner.execute_tool("filesystem", "write_file", {
                "path": "/tmp/workspace/projects/hello.py",
                "content": """#!/usr/bin/env python3
print("Hello from MCP filesystem server!")
print("This file was created through e2b-mcp")

def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("MCP World"))
"""
            })
            print("🐍 Created hello.py")
            
            # Create a README file
            readme_result = await runner.execute_tool("filesystem", "write_file", {
                "path": "/tmp/workspace/projects/README.md",
                "content": """# MCP Filesystem Example

This directory was created using the MCP filesystem server through e2b-mcp.

## Files:
- `hello.py` - A simple Python script
- `README.md` - This file

## Created by:
- e2b-mcp library
- MCP filesystem server
- E2B sandbox environment
"""
            })
            print("📄 Created README.md")
            
        except Exception as e:
            print(f"  ❌ File writing failed: {e}")
        
        # Example 3: List directory contents
        print("\n📋 Example 3: List directory contents")
        try:
            list_result = await runner.execute_tool("filesystem", "list_directory", {
                "path": "/tmp/workspace/projects"
            })
            print("📁 Directory contents:")
            if "result" in list_result:
                files = list_result["result"].get("files", [])
                for file_info in files:
                    print(f"  • {file_info.get('name')} ({file_info.get('type', 'unknown')})")
            else:
                print(f"  Raw result: {list_result}")
        except Exception as e:
            print(f"  ❌ Directory listing failed: {e}")
        
        # Example 4: Read file contents
        print("\n📖 Example 4: Read file contents")
        try:
            read_result = await runner.execute_tool("filesystem", "read_file", {
                "path": "/tmp/workspace/projects/hello.py"
            })
            print("🐍 hello.py contents:")
            if "result" in read_result:
                content = read_result["result"].get("content", "")
                print("   " + "\n   ".join(content.split("\n")[:5]) + "\n   ...")
            else:
                print(f"  Raw result: {read_result}")
        except Exception as e:
            print(f"  ❌ File reading failed: {e}")
        
        # Example 5: Search for files
        print("\n🔍 Example 5: Search for Python files")
        try:
            search_result = await runner.execute_tool("filesystem", "search_files", {
                "path": "/tmp/workspace",
                "pattern": "*.py"
            })
            print("🔍 Python files found:")
            if "result" in search_result:
                files = search_result["result"].get("files", [])
                for file_path in files:
                    print(f"  • {file_path}")
            else:
                print(f"  Raw result: {search_result}")
        except Exception as e:
            print(f"  ❌ File search failed: {e}")
        
        print("\n🎉 Filesystem integration example completed successfully!")
        print("\n💡 Try modifying this example to:")
        print("  - Work with different file types")
        print("  - Create more complex directory structures")
        print("  - Move and copy files")
        print("  - Monitor file changes")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 