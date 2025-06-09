#!/usr/bin/env python3
"""
Example demonstrating different package managers with e2b-mcp.

This shows how to configure MCP servers that need different types of packages:
- Python packages via pip
- Node.js packages via npm
- System packages via apt
- Multiple installation commands
"""

import os

from e2b_mcp import E2BMCPRunner, ServerConfig


def main():
    """Demonstrate different package manager configurations."""
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        print("Please set E2B_API_KEY environment variable")
        return

    runner = E2BMCPRunner(api_key=api_key)

    # Example 1: Python package installation
    runner.add_server(
        ServerConfig(
            name="python_server",
            command="python -m mcp_server_pandas",
            install_commands=["pip install pandas numpy requests"],
            description="Python MCP server with pip packages",
        )
    )

    # Example 2: Node.js MCP server
    runner.add_server(
        ServerConfig(
            name="nodejs_server",
            command="node mcp-server.js",
            install_commands=[
                "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
                "sudo apt-get install -y nodejs",
                "npm install @modelcontextprotocol/server-filesystem",
            ],
            description="Node.js MCP server with npm packages",
        )
    )

    # Example 3: System packages + Python packages
    runner.add_server(
        ServerConfig(
            name="system_deps",
            command="python mcp_git_server.py",
            install_commands=[
                "sudo apt-get update",
                "sudo apt-get install -y git curl",
                "pip install gitpython",
            ],
            description="MCP server requiring system dependencies",
        )
    )

    # Example 4: Complex setup with multiple package managers
    runner.add_server(
        ServerConfig(
            name="complex_setup",
            command="python complex_mcp_server.py",
            install_commands=[
                # System packages
                "sudo apt-get update",
                "sudo apt-get install -y build-essential libssl-dev",
                # Python packages
                "pip install --upgrade pip",
                "pip install requests beautifulsoup4 lxml",
                # Additional setup
                "mkdir -p /tmp/mcp_data",
                "chmod 755 /tmp/mcp_data",
            ],
            env={"MCP_DATA_DIR": "/tmp/mcp_data", "SSL_VERIFY": "true"},
            description="Complex MCP server with system deps, Python packages, and setup",
        )
    )

    # Example 5: Rust-based MCP server
    runner.add_server(
        ServerConfig(
            name="rust_server",
            command="./target/release/mcp-rust-server",
            install_commands=[
                "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
                "source ~/.cargo/env",
                "cargo build --release",
            ],
            description="Rust MCP server built from source",
        )
    )

    # Example 6: No installation needed
    runner.add_server(
        ServerConfig(
            name="prebuilt_server",
            command="./prebuilt_mcp_server",
            description="Pre-built MCP server requiring no installation",
        )
    )

    print("Configured servers with different package managers:")
    for server_name in runner.list_servers():
        config = runner.get_server_config(server_name)
        if config:
            print(f"\n{server_name}:")
            print(f"  Command: {config.command}")

            if config.install_commands:
                print(f"  Install commands ({len(config.install_commands)}):")
                for i, cmd in enumerate(config.install_commands, 1):
                    print(f"    {i}. {cmd}")
            else:
                print("  No installation needed")

    print("\nTo test a server:")
    print("  async with runner.create_session('python_server') as session:")
    print("    tools = await runner.discover_tools('python_server')")


if __name__ == "__main__":
    main()
