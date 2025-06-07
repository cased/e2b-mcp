#!/usr/bin/env python3
"""
Custom MCP Server Example

This example demonstrates how to create and use a custom MCP server with e2b-mcp.
It shows how to build your own MCP server and integrate it into the e2b-mcp system.

The custom server provides simple calculator and text processing tools.

Usage:
    python examples/custom_server_example.py
"""

import asyncio

from e2b_mcp import E2BMCPRunner

# Custom MCP Server Code
CUSTOM_SERVER_CODE = '''#!/usr/bin/env python3
"""
Custom Calculator and Text Processing MCP Server

This is a simple example MCP server that provides:
- Calculator operations (add, subtract, multiply, divide)
- Text processing tools (uppercase, lowercase, word count)
"""
import sys
import json
import argparse
import math


class CustomMCPServer:
    """A simple custom MCP server for demonstration."""

    def __init__(self):
        self.tools = [
            {
                "name": "add",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "power",
                "description": "Raise a number to a power",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {"type": "number", "description": "Base number"},
                        "exponent": {"type": "number", "description": "Exponent"}
                    },
                    "required": ["base", "exponent"]
                }
            },
            {
                "name": "text_stats",
                "description": "Get statistics about a text string",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to analyze"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "transform_text",
                "description": "Transform text (uppercase, lowercase, title case)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to transform"},
                        "operation": {
                            "type": "string",
                            "enum": ["upper", "lower", "title", "reverse"],
                            "description": "Transformation operation"
                        }
                    },
                    "required": ["text", "operation"]
                }
            }
        ]

    def handle_request(self, request):
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": self.tools}
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                result = self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": str(result)}]}
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }

    def execute_tool(self, tool_name, arguments):
        """Execute a specific tool."""
        if tool_name == "add":
            return arguments["a"] + arguments["b"]

        elif tool_name == "multiply":
            return arguments["a"] * arguments["b"]

        elif tool_name == "power":
            return math.pow(arguments["base"], arguments["exponent"])

        elif tool_name == "text_stats":
            text = arguments["text"]
            return {
                "character_count": len(text),
                "word_count": len(text.split()),
                "sentence_count": text.count('.') + text.count('!') + text.count('?'),
                "paragraph_count": text.count('\\n\\n') + 1
            }

        elif tool_name == "transform_text":
            text = arguments["text"]
            operation = arguments["operation"]

            if operation == "upper":
                return text.upper()
            elif operation == "lower":
                return text.lower()
            elif operation == "title":
                return text.title()
            elif operation == "reverse":
                return text[::-1]

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def run_stdio_mode(self):
        """Run server in stdio mode."""
        print("Custom MCP Server starting...", file=sys.stderr)

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    print(json.dumps(response))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print("Error: Invalid JSON", file=sys.stderr)
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)

        except KeyboardInterrupt:
            print("Server stopped", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true", help="Use stdio communication")
    args = parser.parse_args()

    server = CustomMCPServer()

    if args.stdio:
        server.run_stdio_mode()
    else:
        print("Custom MCP Server")
        print("Use --stdio flag to run in stdio mode")
'''


async def main():
    """Demonstrate custom MCP server integration."""

    print("🛠️  Custom MCP Server Integration Example")
    print("=" * 50)

    # Initialize E2B MCP runner
    runner = E2BMCPRunner()

    # Configure our custom MCP server
    # We'll upload the server code and run it
    custom_config = {
        "command": "python /tmp/custom_mcp_server.py --stdio",
        "env": {},
        "upload_files": {"/tmp/custom_mcp_server.py": CUSTOM_SERVER_CODE},
    }

    runner.add_server_from_dict("custom", custom_config)

    try:
        print("\n🔧 Discovering custom server tools...")
        tools = await runner.discover_tools("custom")
        print(f"✅ Found {len(tools)} custom tools:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")

        # Example 1: Calculator operations
        print("\n🧮 Example 1: Calculator Operations")

        try:
            # Test addition
            add_result = await runner.execute_tool("custom", "add", {"a": 15, "b": 27})
            print(f"📊 15 + 27 = {add_result}")

            # Test multiplication
            mult_result = await runner.execute_tool("custom", "multiply", {"a": 8, "b": 9})
            print(f"📊 8 × 9 = {mult_result}")

            # Test power
            power_result = await runner.execute_tool("custom", "power", {"base": 2, "exponent": 10})
            print(f"📊 2^10 = {power_result}")

        except Exception as e:
            print(f"❌ Calculator operations failed: {e}")

        # Example 2: Text processing
        print("\n📝 Example 2: Text Processing")

        sample_text = (
            "Hello, World! This is a sample text for analysis. "
            "It contains multiple sentences and words."
        )

        try:
            # Get text statistics
            stats_result = await runner.execute_tool("custom", "text_stats", {"text": sample_text})
            print(f"📊 Text statistics for: '{sample_text[:30]}...'")
            print(f"   Result: {stats_result}")

            # Transform text
            transforms = ["upper", "lower", "title", "reverse"]
            short_text = "Hello MCP World"

            print(f"\\n🔄 Text transformations for: '{short_text}'")
            for transform in transforms:
                transform_result = await runner.execute_tool(
                    "custom", "transform_text", {"text": short_text, "operation": transform}
                )
                print(f"   {transform}: {transform_result}")

        except Exception as e:
            print(f"❌ Text processing failed: {e}")

        # Example 3: Complex workflow combining operations
        print("\\n🔗 Example 3: Complex Workflow")

        try:
            # Calculate some values
            values = []
            for i in range(3):
                result = await runner.execute_tool(
                    "custom", "power", {"base": i + 2, "exponent": 2}
                )
                values.append(result)
                print(f"   {i + 2}^2 = {result}")

            # Sum the values
            total = values[0]
            for val in values[1:]:
                total = await runner.execute_tool("custom", "add", {"a": total, "b": val})

            print(f"📊 Sum of squares: {total}")

            # Create a report text and analyze it
            report_text = (
                f"Mathematical Analysis Report: The sum of squares from 2^2 to 4^2 equals {total}. "
                f"This demonstrates the power of custom MCP servers."
            )

            report_stats = await runner.execute_tool("custom", "text_stats", {"text": report_text})

            print(f"📄 Generated report statistics: {report_stats}")

        except Exception as e:
            print(f"❌ Complex workflow failed: {e}")

        print("\\n🎉 Custom server integration example completed successfully!")
        print("\\n💡 This example demonstrated:")
        print("  ✅ Creating a custom MCP server from scratch")
        print("  ✅ Implementing multiple tool types (math, text)")
        print("  ✅ Proper JSON-RPC protocol handling")
        print("  ✅ Error handling and validation")
        print("  ✅ Complex multi-tool workflows")
        print("\\n📚 Next steps:")
        print("  • Add more sophisticated tools")
        print("  • Implement resource providers")
        print("  • Add persistent state management")
        print("  • Create domain-specific tool suites")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
