#!/usr/bin/env python3
"""
GitHub MCP Server Integration Example

This example demonstrates how to use e2b-mcp with the official GitHub MCP server
to interact with GitHub repositories from within secure E2B sandboxes.

Prerequisites:
- Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable
- Set E2B_API_KEY environment variable

Usage:
    export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
    export E2B_API_KEY="your_e2b_key_here"
    python examples/github_integration.py
"""
import os
import asyncio
from e2b_mcp import E2BMCPRunner


async def main():
    """Demonstrate GitHub MCP server integration."""
    
    # Check for required environment variables
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("KIT_GITHUB_TOKEN")
    if not github_token:
        print("❌ Missing GitHub token!")
        print("Set GITHUB_PERSONAL_ACCESS_TOKEN or KIT_GITHUB_TOKEN environment variable")
        print("Create one at: https://github.com/settings/tokens")
        return
    
    print("🚀 GitHub MCP Server Integration Example")
    print("=" * 50)
    print(f"📡 Using token: {github_token[:12]}...")
    
    # Initialize E2B MCP runner
    runner = E2BMCPRunner()
    
    # Configure GitHub MCP server
    github_config = {
        "command": "npx -y @modelcontextprotocol/server-github",
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_token
        }
    }
    
    runner.add_server_from_dict("github", github_config)
    
    try:
        print("\n🔧 Discovering GitHub tools...")
        tools = await runner.discover_tools("github")
        print(f"✅ Found {len(tools)} GitHub tools")
        
        # Show some key tools
        key_tools = ["search_repositories", "search_code", "get_file_contents", 
                    "create_issue", "create_pull_request", "fork_repository"]
        print("\n📚 Key available tools:")
        for tool in tools:
            if tool.name in key_tools:
                print(f"  • {tool.name}: {tool.description}")
        
        # Example 1: Search repositories
        print("\n🔍 Example 1: Search for E2B repositories")
        try:
            search_result = await runner.execute_tool("github", "search_repositories", {
                "query": "e2b",
                "per_page": 3
            })
            print("📊 Search results:")
            if "result" in search_result:
                repos = search_result["result"].get("repositories", [])
                for repo in repos[:3]:
                    print(f"  • {repo.get('full_name')}: {repo.get('description', 'No description')}")
            else:
                print(f"  Raw result: {search_result}")
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
        
        # Example 2: Get repository information
        print("\n📦 Example 2: Get MCP servers repository details")
        try:
            repo_result = await runner.execute_tool("github", "get_file_contents", {
                "owner": "modelcontextprotocol",
                "repo": "servers",
                "path": "README.md"
            })
            print("📄 Repository README (first 200 chars):")
            if "result" in repo_result:
                content = repo_result["result"].get("content", "")
                print(f"  {content[:200]}...")
            else:
                print(f"  Raw result: {repo_result}")
        except Exception as e:
            print(f"  ❌ Get file failed: {e}")
        
        # Example 3: Search code
        print("\n🔎 Example 3: Search for MCP-related code")
        try:
            code_result = await runner.execute_tool("github", "search_code", {
                "q": "jsonrpc mcp in:file language:python",
                "per_page": 2
            })
            print("💻 Code search results:")
            if "result" in code_result:
                items = code_result["result"].get("items", [])
                for item in items[:2]:
                    print(f"  • {item.get('repository', {}).get('full_name')}: {item.get('path')}")
            else:
                print(f"  Raw result: {code_result}")
        except Exception as e:
            print(f"  ❌ Code search failed: {e}")
        
        print("\n🎉 GitHub integration example completed successfully!")
        print("\n💡 Try modifying this example to:")
        print("  - Search for different repositories")
        print("  - Read files from your own repositories")
        print("  - Create issues or pull requests")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 