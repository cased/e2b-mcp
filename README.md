# E2B MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Run [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) servers securely in [E2B](https://e2b.dev) sandboxes.

E2B MCP provides a simple way to execute MCP servers in isolated cloud environments, enabling safe execution of untrusted tools and code. Instead of running MCP servers directly on your host system, they run inside secure E2B sandboxes with automatic resource management and cleanup.

## Features

- **Secure Execution**: Run MCP servers in isolated E2B sandboxes
- **Simple API**: Clean, intuitive interface for managing MCP servers
- **Tool Discovery**: Automatically discover tools from MCP servers
- **Async/Sync Support**: Both async and synchronous execution modes
- **Auto Cleanup**: Automatic sandbox and resource management
- **Package Management**: Automatic installation of MCP server dependencies

## Installation

```bash
pip install e2b-mcp
```

## Prerequisites

1. **E2B API Key**: Get your free API key from [e2b.dev](https://e2b.dev)
2. **Environment Variable**: Set `E2B_API_KEY` in your environment

```bash
export E2B_API_KEY="your_api_key_here"
```

## Quick Start

```python
import asyncio
from e2b_mcp import E2BMCPRunner, ServerConfig

async def main():
    # Create runner
    runner = E2BMCPRunner()

    # Add MCP server
    runner.add_server(ServerConfig(
        name="filesystem",
        command="python -m mcp_server_filesystem --stdio",
        package="mcp-server-filesystem",
        description="File system operations"
    ))

    # Discover tools by passing the server name
    tools = await runner.discover_tools("filesystem")
    print(f"Found {len(tools)} tools")

    # Execute a tool
    result = await runner.execute_tool(
        "filesystem",
        "read_file",
        {"path": "/tmp/example.txt"}
    )
    print(result)

# Run async code
asyncio.run(main())
```

## Configuration

### Server Configuration

```python
from e2b_mcp import ServerConfig

# Method 1: Using ServerConfig class
config = ServerConfig(
    name="my_server",
    command="python -m my_mcp_server --stdio",
    package="my-mcp-server-package",  # Optional
    description="My custom MCP server",
    timeout_minutes=10,
    env={"DEBUG": "1"}  # Optional environment variables
)
runner.add_server(config)

# Method 2: Using dictionary
runner.add_server_from_dict("my_server", {
    "command": "python -m my_mcp_server --stdio",
    "package": "my-mcp-server-package",
    "description": "My custom MCP server",
    "timeout_minutes": 10,
    "env": {"DEBUG": "1"}
})
```

### Configuration Parameters

- **name**: Unique identifier for the MCP server
- **command**: Command to start the MCP server
- **package**: Python package to install (optional)
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

E2B MCP works with any MCP server that supports the standard MCP protocol. Some popular servers include:

- **mcp-server-filesystem**: File system operations
- **mcp-server-git**: Git repository management
- **mcp-server-sqlite**: SQLite database operations
- **mcp-server-brave-search**: Web search capabilities
- **mcp-server-slack**: Slack integration

## Security

E2B MCP provides several layers of security:

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

# Format code
black .
ruff check .
```

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