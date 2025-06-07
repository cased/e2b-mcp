# e2b-mcp Examples

This directory contains comprehensive examples demonstrating how to use e2b-mcp to integrate Model Context Protocol (MCP) servers with E2B sandboxes for secure AI agent operations.

## Overview

e2b-mcp enables AI agents to safely interact with external tools and services by running MCP servers inside secure E2B sandboxes. These examples show various integration patterns and use cases.

## Prerequisites

Before running these examples, ensure you have:

1. **E2B API Key**: Get yours at [e2b.dev](https://e2b.dev)
2. **Python Environment**: Python 3.8+ with e2b-mcp installed
3. **Optional Tokens**: For specific integrations (GitHub, etc.)

```bash
# Install e2b-mcp
pip install e2b-mcp

# Set required environment variables
export E2B_API_KEY="your_e2b_key_here"
export GITHUB_PERSONAL_ACCESS_TOKEN="your_github_token"  # For GitHub examples
```

## Examples

### 1. 🐙 GitHub Integration (`github_integration.py`)

**What it demonstrates:**
- Integrating with the official GitHub MCP server
- Repository searching and code analysis
- File content retrieval from GitHub repos
- Secure API token handling

**Features shown:**
- ✅ Repository search with filters
- ✅ File content reading
- ✅ Code search across GitHub
- ✅ Multi-step GitHub workflows

**Usage:**
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token"
python examples/github_integration.py
```

**Key learning:**
Shows how to integrate with external APIs that require authentication, demonstrating the power of combining E2B's security with MCP's protocol standardization.

---

### 2. 🗂️ Filesystem Operations (`filesystem_integration.py`)

**What it demonstrates:**
- Safe file and directory operations within E2B sandboxes
- Creating project structures programmatically
- File content management and search

**Features shown:**
- ✅ Directory creation and management
- ✅ File writing and reading
- ✅ File search with patterns
- ✅ Directory listing and navigation

**Usage:**
```bash
python examples/filesystem_integration.py
```

**Key learning:**
Demonstrates how MCP servers can provide safe file system access within the isolated E2B environment, perfect for code generation and project management tasks.

---

### 3. 🔗 Multi-Server Integration (`multi_server_example.py`)

**What it demonstrates:**
- Using multiple MCP servers simultaneously
- Data flow between different servers
- Complex automation workflows
- Cross-server coordination

**Servers integrated:**
- **GitHub**: Repository operations
- **Filesystem**: Local file management  
- **SQLite**: Data storage and analysis

**Features shown:**
- ✅ Multi-server tool discovery
- ✅ Cross-server data passing
- ✅ Workflow orchestration
- ✅ Comprehensive project analysis pipeline

**Usage:**
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token"  # Optional
python examples/multi_server_example.py
```

**Key learning:**
Shows the power of composing multiple MCP servers to create sophisticated automation workflows that combine external APIs, local operations, and data persistence.

---

### 4. 🛠️ Custom Server Creation (`custom_server_example.py`)

**What it demonstrates:**
- Building custom MCP servers from scratch
- Implementing the MCP protocol correctly
- Creating domain-specific tool suites
- Custom business logic integration

**Custom tools included:**
- **Calculator**: Math operations (add, multiply, power)
- **Text processor**: Text analysis and transformation
- **Workflow**: Multi-step operations

**Features shown:**
- ✅ Custom tool definition and JSON schema
- ✅ JSON-RPC protocol implementation
- ✅ Error handling and validation
- ✅ Complex multi-tool workflows

**Usage:**
```bash
python examples/custom_server_example.py
```

**Key learning:**
Demonstrates how to create your own MCP servers for specialized use cases, showing the full development cycle from server creation to integration.

## Running the Examples

### Quick Start

1. **Install dependencies:**
```bash
pip install e2b-mcp
```

2. **Set environment variables:**
```bash
export E2B_API_KEY="your_e2b_api_key"
export GITHUB_PERSONAL_ACCESS_TOKEN="your_github_token"  # Optional
```

3. **Run any example:**
```bash
python examples/github_integration.py
python examples/filesystem_integration.py
python examples/multi_server_example.py
python examples/custom_server_example.py
```

### Advanced Usage

Each example can be modified to explore different scenarios:

- **Modify server configurations** to use different MCP servers
- **Change tool parameters** to test different operations  
- **Combine examples** to create more complex workflows
- **Add error handling** for production use cases

## Example Output

### GitHub Integration
```
🚀 GitHub MCP Server Integration Example
==================================================
📡 Using token: github_pat_11...
✅ Found 26 GitHub tools

📚 Key available tools:
  • search_repositories: Search for GitHub repositories
  • get_file_contents: Get the contents of a file
  • create_issue: Create a new issue

🔍 Example 1: Search for E2B repositories
📊 Search results:
  • E2B-dev/E2B: Runtime for AI agents
  • e2b-dev/awesome-ai-agents: Curated list of AI agents
```

### Multi-Server Integration
```
🚀 Multi-Server MCP Integration Example
==================================================
✅ GitHub integration enabled
📡 Added filesystem server
📡 Added sqlite server
📡 Added github server

✅ filesystem: 8 tools
✅ sqlite: 6 tools  
✅ github: 26 tools

🎯 Example Workflow: Project Analysis System
✅ Created project directories
✅ Created analysis database table
✅ Found 2 repositories
📊 Analyzed: tensorflow/tensorflow (Python, 185043 stars)
```

## Integration Patterns

### 1. **External API Integration**
Examples show how to securely integrate with external APIs (GitHub) while maintaining isolation.

### 2. **Local Operations**
Demonstrate safe file system operations and data processing within sandboxes.

### 3. **Multi-Server Workflows**
Show how to orchestrate multiple servers to create comprehensive automation pipelines.

### 4. **Custom Server Development**
Illustrate the complete cycle of building, deploying, and using custom MCP servers.

## Security Benefits

All examples demonstrate e2b-mcp's security advantages:

- 🔒 **Isolation**: Each MCP server runs in its own secure E2B sandbox
- 🛡️ **Network Security**: External API calls are contained within sandboxes
- 📁 **File System Safety**: File operations are limited to sandbox boundaries
- 🔑 **Token Security**: API keys are only accessible within secure environments
- 🚫 **No Host Access**: Servers cannot access the host system

## Next Steps

After exploring these examples:

1. **Modify existing examples** to suit your use cases
2. **Combine multiple patterns** for complex workflows
3. **Create custom servers** for your specific domain
4. **Build production workflows** using the patterns shown
5. **Contribute new examples** to help the community

## Contributing

Found an issue or want to add an example? 

1. Fork the repository
2. Create your example following the existing patterns
3. Add comprehensive documentation
4. Submit a pull request

## Resources

- [e2b-mcp Documentation](https://github.com/your-org/e2b-mcp)
- [E2B Platform](https://e2b.dev)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)

---

**Happy building! 🚀**

These examples demonstrate the power of combining E2B's secure execution environment with MCP's standardized tool protocol to create safe, powerful AI agent capabilities. 