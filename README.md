# e2b-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Run [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) servers securely in [E2B](https://e2b.dev) sandboxes.

e2b-mcp provides a simple way to execute MCP servers in isolated cloud environments, enabling safe execution of untrusted tools and code. Instead of running MCP servers directly on your host system, they run inside secure E2B sandboxes with automatic resource management and cleanup.

## Use Cases

We built e2b-mcp so [Cased](https://cased.com) can run MCP servers on behalf of users, and 
integrate with our DevOps agent. But e2b-mcp has many use cases:

### **AI Agent Platforms**
- **Safe Tool Execution**: Let AI agents use file operations, git commands, and web APIs without compromising your infrastructure
- **User-Specific Sandboxes**: Run MCP servers with each user's credentials and permissions in isolated environments  
- **Dynamic Tool Discovery**: Discover and provision new capabilities for agents on-demand

### **SaaS Applications**
- **Multi-Tenant Tool Execution**: Safely execute user-requested operations (file processing, data analysis) in dedicated sandboxes
- **API Gateway for MCP**: Expose MCP tools as REST endpoints with built-in security and isolation
- **Serverless MCP**: Scale MCP server instances based on demand without infrastructure management

### **Developer Tools & IDEs**
- **Code Execution Environments**: Provide secure code execution for online IDEs and coding platforms
- **Plugin Sandboxing**: Run untrusted MCP plugins safely without affecting the host environment  
- **CI/CD Integration**: Execute build/test tools in isolated environments with controlled access

### **Enterprise Solutions**
- **Compliance & Security**: Meet security requirements by isolating all tool execution
- **Customer Onboarding**: Let customers try tools and integrations safely before deployment
- **Managed AI Services**: Offer AI capabilities to customers without exposing backend systems

## Features

- **Secure Execution**: Run MCP servers in isolated E2B sandboxes
- **CLI & API**: Both command-line interface and Python API
- **Tool Discovery**: Automatically discover tools from MCP servers
- **Async/Sync Support**: Both async and synchronous execution modes
- **Auto Cleanup**: Automatic sandbox and resource management
- **Package Management**: Automatic installation of MCP server dependencies
- **Multi-Language**: Use from any language via CLI or build language-specific wrappers

## Installation

```bash
uv pip install e2b-mcp
```

## Prerequisites

1. **E2B API Key**: Get your free API key from [e2b.dev](https://e2b.dev)
2. **Environment Variable**: Set `E2B_API_KEY` in your environment

```bash
export E2B_API_KEY="your_api_key_here"
```

## Quick Start

### CLI Usage

```bash
# Add a GitHub MCP server
e2b-mcp server add github \
  --command "npx -y @modelcontextprotocol/server-github" \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=your_token

# Discover available tools
e2b-mcp tools list github

# Execute a tool
e2b-mcp tools execute github search_repositories \
  --params '{"query": "python", "per_page": 5}'

# Quick one-shot execution (no config save)
e2b-mcp quick "npx -y @modelcontextprotocol/server-filesystem /tmp" \
  list_directory --param path=/tmp

# Multi-package installation with install-commands
e2b-mcp server add complex_server \
  --command "python /app/server.py" \
  --install-commands "apt-get update" \
  --install-commands "apt-get install -y git curl" \
  --install-commands "pip install requests beautifulsoup4" \
  --env DATA_DIR=/app/data

# Node.js MCP server setup
e2b-mcp server add nodejs_fs \
  --command "node filesystem-server.js" \
  --install-commands "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -" \
  --install-commands "apt-get install -y nodejs" \
  --install-commands "npm install @modelcontextprotocol/server-filesystem"
```

### Python API

```python
import asyncio
from e2b_mcp import E2BMCPRunner, ServerConfig

async def main():
    # Create runner
    runner = E2BMCPRunner()

    # Add MCP server
    runner.add_server(ServerConfig(
        name="filesystem",
        command="npx -y @modelcontextprotocol/server-filesystem /tmp",
        description="File system operations"
    ))

    # Discover tools
    tools = await runner.discover_tools("filesystem")
    print(f"Found {len(tools)} tools")

    # Execute a tool
    result = await runner.execute_tool(
        "filesystem",
        "write_file",
        {"path": "/tmp/example.txt", "content": "Hello World!"}
    )
    print(result)

# Run async code
asyncio.run(main())
```

## 📖 CLI Documentation

### Server Management

```bash
# Add a new MCP server configuration
e2b-mcp server add <name> --command "<command>" [options]

# List all configured servers
e2b-mcp server list [--json]

# Remove a server configuration  
e2b-mcp server remove <name> [--yes]
```

**Add Server Options:**
- `--command`: Command to run the MCP server (required)
- `--env KEY=VALUE`: Environment variables (can be used multiple times)
- `--install-commands`: Installation commands to run (can be used multiple times)
- `--description`: Server description
- `--timeout`: Timeout in minutes (default: 10)

### Tool Operations

```bash
# List tools from a configured server
e2b-mcp tools list <server_name> [--json]

# Execute a tool
e2b-mcp tools execute <server_name> <tool_name> [options]
```

**Execute Tool Options:**
- `--params`: Tool parameters as JSON string
- `--param key=value`: Individual parameters (can be used multiple times)
- `--json`: Output raw JSON response

### Quick Execute

```bash
# Execute without saving server config
e2b-mcp quick "<command>" <tool_name> [options]
```

**Quick Execute Options:**
- `--params`: Tool parameters as JSON string
- `--param key=value`: Individual parameters  
- `--env KEY=VALUE`: Environment variables
- `--json`: Output raw JSON response

### Configuration

```bash
# Show current configuration
e2b-mcp config [--show]

# Edit configuration file
e2b-mcp config --edit

# Reset all configuration
e2b-mcp config --reset
```

### CLI Examples

```bash
# GitHub integration
export GITHUB_TOKEN="your_token"
e2b-mcp server add github \
  --command "npx -y @modelcontextprotocol/server-github" \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN

e2b-mcp tools execute github search_repositories \
  --params '{"query": "e2b", "per_page": 3}'

# Filesystem operations
e2b-mcp server add fs \
  --command "npx -y @modelcontextprotocol/server-filesystem /tmp"

e2b-mcp tools execute fs write_file \
  --param path=/tmp/test.txt \
  --param content="Hello CLI!"

e2b-mcp tools execute fs read_file \
  --param path=/tmp/test.txt

# Using quick execute for one-offs
e2b-mcp quick "npx -y @modelcontextprotocol/server-filesystem /tmp" \
  list_directory --param path=/tmp --json
```

Configuration is stored in `~/.e2b-mcp/servers.json` and can be shared across different environments.

## Configuration

### Server Configuration

```python
from e2b_mcp import ServerConfig

# Method 1: Using ServerConfig class
config = ServerConfig(
    name="my_server",
    command="python -m my_mcp_server --stdio",
    install_commands=[  # Installation commands for any package manager
        "apt-get update",
        "apt-get install -y nodejs npm",
        "npm install express",
        "pip install additional-package"
    ],
    description="My custom MCP server",
    timeout_minutes=10,
    env={"DEBUG": "1"}  # Optional environment variables
)
runner.add_server(config)

# Method 2: Using dictionary
runner.add_server_from_dict("my_server", {
    "command": "python -m my_mcp_server --stdio",
    "install_commands": [
        "pip install requests beautifulsoup4",
        "apt-get install -y curl"
    ],
    "description": "My custom MCP server",
    "timeout_minutes": 10,
    "env": {"DEBUG": "1"}
})

# Example: Node.js MCP server
runner.add_server_from_dict("nodejs_server", {
    "command": "node mcp-server.js",
    "install_commands": [
        "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
        "sudo apt-get install -y nodejs",
        "npm install @modelcontextprotocol/server-filesystem"
    ],
    "description": "Node.js MCP server"
})

# Example: Rust MCP server
runner.add_server_from_dict("rust_server", {
    "command": "./target/release/mcp-server",
    "install_commands": [
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "source ~/.cargo/env",
        "cargo build --release"
    ],
    "description": "Rust-based MCP server"
})
```

### Configuration Parameters

- **name**: Unique identifier for the MCP server
- **command**: Command to start the MCP server
- **install_commands**: Flexible installation commands (optional)
- **description**: Human-readable description
- **timeout_minutes**: Sandbox timeout (default: 10 minutes)
- **env**: Environment variables (optional)

## API Reference

### E2BMCPRunner

Main class for managing MCP servers in E2B sandboxes.

#### Methods

##### `__init__(api_key: Optional[str] = None)`
Initialize the runner with an E2B API key.

##### `add_server(config: ServerConfig) -> None`
Add an MCP server configuration.

##### `add_server_from_dict(name: str, config_data: Dict[str, Any]) -> None`
Add an MCP server configuration from a dictionary.

##### `list_servers() -> List[str]`
List all configured server names.

##### `async discover_tools(server_name: str) -> List[Tool]`
Discover tools from an MCP server.

##### `async execute_tool(server_name: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]`
Execute a tool on an MCP server.

##### `execute_tool_sync(server_name: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]`
Synchronous wrapper for `execute_tool`.

##### `async create_session(server_name: str) -> AsyncContextManager[Session]`
Create a managed MCP session (advanced usage).

## Examples

### Basic Tool Execution

```python
import asyncio
from e2b_mcp import E2BMCPRunner

async def main():
    runner = E2BMCPRunner()

    # Add a simple test server
    runner.add_server_from_dict("test", {
        "command": "python /tmp/test_mcp_server.py",
        "description": "Test server with basic tools"
    })

    # Execute tools
    time_result = await runner.execute_tool("test", "get_time", {"format": "iso"})
    echo_result = await runner.execute_tool("test", "echo", {"text": "Hello!"})

    print(f"Time: {time_result}")
    print(f"Echo: {echo_result}")

asyncio.run(main())
```

### Synchronous Usage

```python
from e2b_mcp import E2BMCPRunner

runner = E2BMCPRunner()
runner.add_server_from_dict("test", {
    "command": "python /tmp/test_mcp_server.py"
})

# Synchronous execution
result = runner.execute_tool_sync("test", "get_time", {"format": "readable"})
print(result)
```

### Session Management (Advanced)

```python
async def advanced_usage():
    runner = E2BMCPRunner()
    runner.add_server_from_dict("filesystem", {
        "command": "python -m mcp_server_filesystem --stdio",
        "package": "mcp-server-filesystem"
    })

    # Manage session lifecycle manually
    async with runner.create_session("filesystem") as session:
        print(f"Session ID: {session.session_id}")
        print(f"Sandbox ID: {session.sandbox_id}")

        # Session automatically cleaned up when exiting context
```

## Supported MCP Servers

e2b-mcp works with any MCP server that supports the standard MCP protocol. Some popular servers include:

- **mcp-server-filesystem**: File system operations
- **mcp-server-git**: Git repository management
- **mcp-server-sqlite**: SQLite database operations
- **mcp-server-brave-search**: Web search capabilities
- **mcp-server-slack**: Slack integration

## Security

e2b-mcp provides several layers of security:

1. **Sandbox Isolation**: All MCP servers run in isolated E2B sandboxes
2. **Network Isolation**: Sandboxes have controlled network access
3. **Resource Limits**: Automatic CPU, memory, and time limits
4. **Auto Cleanup**: Sandboxes are automatically destroyed after use
5. **No Host Access**: MCP servers cannot access your local file system

## Error Handling

```python
from e2b_mcp import E2BMCPRunner, MCPError

try:
    runner = E2BMCPRunner()
    result = await runner.execute_tool("nonexistent", "tool", {})
except MCPError as e:
    print(f"MCP operation failed: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/cased/e2b-mcp.git
cd e2b-mcp

# Install in development mode
pip install -e ".[dev]"

# Format and lint code using the provided script
./scripts/format

# Or run individual tools manually
black .
ruff check .
```

### Development Scripts

The project includes helpful development scripts in the `scripts/` directory:

#### Format Script (`./scripts/format`)
Automatically formats and lints the codebase:
- Runs `black` for code formatting
- Runs `ruff check --fix --unsafe-fixes` for linting and auto-fixes
- Runs `ruff format` for import sorting
- Runs `mypy` for type checking

```bash
./scripts/format
```

#### Release Script (`./scripts/release`)
Handles the complete professional release process with comprehensive pre-flight checks:
- **Version Validation**: Ensures provided version matches `pyproject.toml`
- **Pre-flight Checks**: Validates git state, branch, and required tools
- **Environment Validation**: Checks PyPI credentials and dependencies
- **Build & Publish**: Builds package and publishes to PyPI automatically
- **Git Tagging**: Creates and pushes git tags to GitHub
- **GitHub Releases**: Optionally creates GitHub releases with auto-generated notes

**Prerequisites for Release:**
```bash
# 1. Set PyPI credentials (required)
export TWINE_USERNAME=__token__
export TWINE_PASSWORD='your-pypi-api-token'

# 2. Install required tools
pip install build twine

# 3. Optional: Install GitHub CLI for release creation
brew install gh  # or equivalent for your system
```

**Release Process:**
```bash
# 1. Update version in pyproject.toml manually
# version = "0.2.0"

# 2. Commit the version change
git add pyproject.toml
git commit -m "Bump version to 0.2.0"

# 3. Run release script with the same version
./scripts/release 0.2.0
```

**What the Release Script Does:**
- ✅ Validates version matches `pyproject.toml`
- ✅ Checks for clean git state and proper branch
- ✅ Verifies PyPI credentials and required tools
- ✅ Builds package with `python -m build`
- ✅ Publishes to PyPI with `twine upload`
- ✅ Creates and pushes git tag (`v0.2.0`)
- ✅ Optionally creates GitHub release with auto-generated notes
- ✅ Handles virtual environment deactivation/reactivation for clean builds

**Security Features:**
- Multiple confirmation prompts before destructive actions
- Validates all prerequisites before starting
- Clean error handling with helpful messages
- Safe virtual environment handling

### Testing

The package includes both unit tests and integration tests:

#### Unit Tests
Run fast unit tests that don't require E2B API access:

```bash
# Run only unit tests (fast)
pytest tests/test_basic.py

# Run with verbose output
pytest tests/test_basic.py -v
```

#### Integration Tests
Run comprehensive integration tests that create real E2B sandboxes:

```bash
# Set E2B API key (required for integration tests)
export E2B_API_KEY="your_api_key"

# Run integration tests
pytest tests/test_integration.py -v

# Run all tests including integration
pytest -v
```

#### Test Commands

```bash
# Run only unit tests (no E2B API key needed)
pytest -m "not integration"

# Run only integration tests (E2B API key required)
pytest -m integration

# Run all tests
pytest

# Run with coverage
pytest --cov=e2b_mcp

# Run specific test
pytest tests/test_integration.py::TestE2BMCPIntegration::test_tool_discovery -v
```

#### Integration Test Categories

- **Basic Functionality**: Session creation, tool discovery, tool execution
- **Package Installation**: Testing MCP servers with pip dependencies
- **Environment Variables**: Testing custom environment configuration
- **Error Handling**: Testing failure scenarios and cleanup
- **Performance**: Concurrent sessions and rapid creation/destruction
- **Stress Testing**: Multiple simultaneous operations

**Note**: Integration tests create real E2B sandboxes and may take several minutes to complete. They require a valid E2B API key.

### Running Examples

```bash
# Set E2B API key
export E2B_API_KEY="your_api_key"

# Run basic example
python examples/basic_usage.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) - The protocol this library implements
- [E2B](https://e2b.dev) - Secure cloud sandboxes for AI
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server implementations

## Package Management

e2b-mcp supports flexible package installation across different ecosystems using `install_commands`:

### Installation Commands
```python

runner.add_server(ServerConfig(
    name="multi_lang_server",
    command="node server.js",
    install_commands=[
        # System packages
        "apt-get update",
        "apt-get install -y build-essential",
        # Node.js ecosystem
        "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -",
        "apt-get install -y nodejs",
        "npm install express @modelcontextprotocol/server-filesystem",
        # Python packages
        "pip install requests beautifulsoup4",
        # Custom setup
        "mkdir -p /app/data",
        "chmod 755 /app/data"
    ]
))
```

### Package Manager Examples

#### Node.js/npm
```python
runner.add_server_from_dict("nodejs_mcp", {
    "command": "node mcp-server.js",
    "install_commands": [
        "apt-get update",
        "apt-get install -y nodejs npm",
        "npm install express sqlite3"
    ]
})
```

#### Python with pip
```python
runner.add_server_from_dict("python_mcp", {
    "command": "python server.py",
    "install_commands": [
        "pip install --upgrade pip",
        "pip install fastapi uvicorn pandas numpy"
    ]
})
```

#### Rust with cargo
```python
runner.add_server_from_dict("rust_mcp", {
    "command": "./target/release/mcp-server",
    "install_commands": [
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "source ~/.cargo/env",
        "cargo build --release"
    ]
})
```

#### System Dependencies
```python
runner.add_server_from_dict("system_mcp", {
    "command": "python git_server.py",
    "install_commands": [
        "apt-get update",
        "apt-get install -y git curl wget",
        "pip install gitpython"
    ]
})
```

## Configuration