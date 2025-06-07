#!/usr/bin/env python3
"""
Test MCP server for e2b-mcp integration testing.

This server supports both stdio and file-based communication modes
and provides simple tools for testing the E2B MCP pipeline.
"""

import argparse
import json
import select
import sys
import time
from datetime import datetime
from pathlib import Path


class TestMCPServer:
    """Simple test MCP server with basic tools."""

    def __init__(self, file_mode=False):
        self.file_mode = file_mode
        self.request_file = Path("/tmp/mcp/requests.jsonl")
        self.response_file = Path("/tmp/mcp/responses.jsonl")

    def handle_request(self, request):
        """Handle MCP request and return response."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_time",
                            "description": "Get the current date and time",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "format": {
                                        "type": "string",
                                        "description": "Time format (iso, timestamp, or readable)",
                                        "default": "iso",
                                    }
                                },
                            },
                        },
                        {
                            "name": "echo",
                            "description": "Echo back the input text",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "description": "Text to echo back"}
                                },
                                "required": ["text"],
                            },
                        },
                        {
                            "name": "add_numbers",
                            "description": "Add two numbers together",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "a": {"type": "number", "description": "First number"},
                                    "b": {"type": "number", "description": "Second number"},
                                },
                                "required": ["a", "b"],
                            },
                        },
                    ]
                },
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "get_time":
                fmt = arguments.get("format", "iso")
                now = datetime.now()

                if fmt == "timestamp":
                    result = {"time": now.timestamp()}
                elif fmt == "readable":
                    result = {"time": now.strftime("%Y-%m-%d %H:%M:%S")}
                else:  # iso
                    result = {"time": now.isoformat()}

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
                }
            elif tool_name == "echo":
                text = arguments.get("text", "")
                result = {"echoed": text}
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
                }
            elif tool_name == "add_numbers":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = {"sum": a + b}
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }

    def run_stdio_mode(self):
        """Run server in stdio mode."""
        print("MCP Server starting in stdio mode...", file=sys.stderr)
        sys.stderr.flush()

        while True:
            try:
                # Check if stdin has data available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline()
                    if not line:  # EOF
                        print("Got EOF, but continuing to wait for more input...", file=sys.stderr)
                        sys.stderr.flush()
                        time.sleep(0.1)
                        continue

                    request = json.loads(line.strip())
                    response = self.handle_request(request)
                    print(json.dumps(response))
                    sys.stdout.flush()
                else:
                    # No input available, just sleep a bit
                    time.sleep(0.1)

            except (EOFError, KeyboardInterrupt):
                print("Got EOF/Keyboard interrupt, but continuing...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing request: {e}", file=sys.stderr)
                sys.stderr.flush()
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": f"Internal error: {e}"},
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

    def run_file_mode(self):
        """Run server in file mode."""
        processed_requests = set()

        while True:
            try:
                if self.request_file.exists():
                    with open(self.request_file) as f:
                        lines = f.readlines()

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        request = json.loads(line)
                        request_id = request.get("id")

                        # Skip if we've already processed this request
                        if request_id in processed_requests:
                            continue

                        processed_requests.add(request_id)

                        # Process request
                        response = self.handle_request(request)

                        # Write response
                        with open(self.response_file, "a") as f:
                            f.write(json.dumps(response) + "\n")

                time.sleep(0.1)  # Small delay to avoid busy waiting

            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                # Log error but continue running
                print(f"Error in file mode: {e}", file=sys.stderr)
                time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file-mode", action="store_true", help="Use file-based communication instead of stdio"
    )
    parser.add_argument("--stdio", action="store_true", help="Use stdio communication (default)")
    args = parser.parse_args()

    server = TestMCPServer(file_mode=args.file_mode)

    if args.file_mode:
        server.run_file_mode()
    else:
        server.run_stdio_mode()
