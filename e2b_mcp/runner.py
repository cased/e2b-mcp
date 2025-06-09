"""
E2B MCP Runner - Core implementation for running MCP servers in E2B sandboxes.

This is the main interface for the package, providing a clean API for managing
MCP servers in secure E2B sandboxes.
"""

import asyncio
import json
import logging
import os
import shlex
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from e2b_code_interpreter import AsyncSandbox as Sandbox  # type: ignore[import-untyped]

from .models import MCPError, ServerConfig, Session, Tool

logger = logging.getLogger(__name__)


class E2BMCPRunner:
    """
    Run MCP servers securely in E2B sandboxes.

    This class provides a clean interface for:
    - Configuring MCP servers
    - Creating isolated sandbox sessions
    - Discovering tools from MCP servers
    - Executing tools safely in sandboxes
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize E2B MCP Runner.

        Args:
            api_key: E2B API key. If not provided, uses E2B_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        if not self.api_key:
            raise ValueError("E2B_API_KEY is required. Get your API key from https://e2b.dev")

        self.server_configs: dict[str, ServerConfig] = {}
        self.active_sessions: dict[str, tuple[Session, Sandbox]] = {}
        self._use_stdio = True

    def add_server(self, config: ServerConfig) -> None:
        """
        Add an MCP server configuration.

        Args:
            config: Server configuration
        """
        self.server_configs[config.name] = config
        logger.debug(f"Added MCP server config: {config.name}")

    def add_server_from_dict(self, name: str, config_data: dict[str, Any]) -> None:
        """
        Add an MCP server configuration from dictionary.

        Args:
            name: Server name
            config_data: Server configuration as dictionary
        """
        config = ServerConfig.from_dict(name, config_data)
        self.add_server(config)

    def add_servers(self, configs: dict[str, dict[str, Any]]) -> None:
        """
        Add multiple server configurations at once.

        Args:
            configs: Dictionary of server name to configuration data

        Raises:
            ValueError: If any configuration is invalid (no configs will be added)
        """
        # First, validate all configurations
        validated_configs = {}
        for name, config_data in configs.items():
            try:
                config = ServerConfig.from_dict(name, config_data)
                validated_configs[name] = config
            except Exception as e:
                # If any config is invalid, don't add any configs
                raise ValueError(f"Invalid configuration for server '{name}': {e}") from e

        for name, config in validated_configs.items():
            self.server_configs[name] = config
            logger.debug(f"Added MCP server config: {name}")

    def list_servers(self) -> list[str]:
        """List all configured server names."""
        return list(self.server_configs.keys())

    def get_server_config(self, name: str) -> ServerConfig | None:
        """Get server configuration by name."""
        return self.server_configs.get(name)

    def get_server_info(self, name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a server.

        Args:
            name: Server name

        Returns:
            Dictionary with server information or None if not found
        """
        config = self.get_server_config(name)
        if not config:
            return None

        return {
            "name": config.name,
            "command": config.command,
            "description": config.description,
            "timeout_minutes": config.timeout_minutes,
            "requires_installation": config.requires_installation(),
            "display_name": config.get_display_name(),
            "env_vars": list(config.env.keys()),
            "install_commands": config.install_commands,
        }

    def list_active_sessions(self) -> list[dict[str, Any]]:
        """
        Get information about all active sessions.

        Returns:
            List of session information dictionaries
        """
        session_info = []
        for session_id, (session, _sandbox) in self.active_sessions.items():
            session_info.append(
                {
                    "session_id": session_id,
                    "server_name": session.server_name,
                    "sandbox_id": session.sandbox_id,
                    "initialized": session.initialized,
                    "tool_count": session.get_tool_count(),
                }
            )
        return session_info

    def get_active_session_count(self) -> int:
        """Get the number of currently active sessions."""
        return len(self.active_sessions)

    @asynccontextmanager
    async def create_session(self, server_name: str) -> AsyncIterator[Session]:
        """
        Create a new MCP session in an E2B sandbox.

        Args:
            server_name: Name of the configured MCP server

        Yields:
            Session: Active session with running MCP server

        Raises:
            ValueError: If server is not configured
            MCPError: If session creation fails
        """
        if server_name not in self.server_configs:
            raise ValueError(f"Server '{server_name}' not configured")

        config = self.server_configs[server_name]
        session_id = str(uuid.uuid4())

        logger.info(f"Creating E2B MCP session for {server_name}")

        try:
            # Create E2B sandbox (async)
            sandbox = await Sandbox.create(api_key=self.api_key)
            logger.debug(f"Created sandbox {sandbox.sandbox_id}")

            # Set timeout
            await sandbox.set_timeout(config.timeout_minutes * 60)

            session = Session(
                session_id=session_id,
                server_name=server_name,
                config=config,
                sandbox_id=sandbox.sandbox_id,
            )

            # Setup MCP server in sandbox
            await self._setup_mcp_server(session, sandbox)

            # Store active session with sandbox reference
            self.active_sessions[session_id] = (session, sandbox)

            try:
                yield session
            finally:
                # Cleanup session
                await self._cleanup_session(session, sandbox)

        except Exception as e:
            logger.error(f"Failed to create MCP session for {server_name}: {e}")
            raise MCPError(f"Failed to create MCP session: {e}") from e

    async def discover_tools(self, server_name: str) -> list[Tool]:
        """
        Discover tools from an MCP server.

        Args:
            server_name: Name of the configured MCP server

        Returns:
            List of discovered tools

        Raises:
            MCPError: If tool discovery fails
        """
        logger.info(f"Discovering tools from MCP server: {server_name}")

        async with self.create_session(server_name) as session:
            try:
                # Send tools/list request
                response = await self._send_mcp_request(session, "tools/list")
                tools_data = response.get("tools", [])

                # Convert to Tool objects
                tools = [Tool.from_mcp_tool(tool_data, server_name) for tool_data in tools_data]

                logger.debug(f"Discovered {len(tools)} tools from {server_name}")
                return tools

            except Exception as e:
                logger.error(f"Failed to discover tools from {server_name}: {e}")
                raise MCPError(f"Failed to discover tools from {server_name}: {e}") from e

    async def execute_tool(
        self, server_name: str, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a tool on an MCP server.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            MCPError: If tool execution fails
        """
        logger.info(f"Executing tool {tool_name} on server {server_name}")

        # Validate that server is configured
        if server_name not in self.server_configs:
            raise MCPError(f"Server '{server_name}' not configured", server_name=server_name)

        async with self.create_session(server_name) as session:
            try:
                # First discover tools to get schema for validation
                tools = await self._discover_tools_for_session(session)

                # Find the specific tool
                tool = None
                for t in tools:
                    if t.name == tool_name:
                        tool = t
                        break

                if tool is None:
                    available_tools = [t.name for t in tools]
                    raise MCPError(
                        f"Tool '{tool_name}' not found. Available tools: {available_tools}",
                        server_name=server_name,
                        tool_name=tool_name,
                    )

                # Validate parameters against tool schema
                validation_errors = tool.validate_parameters(params)
                if validation_errors:
                    error_msg = f"Parameter validation failed: {', '.join(validation_errors)}"
                    raise MCPError(error_msg, server_name=server_name, tool_name=tool_name)

                # Send tools/call request
                response = await self._send_mcp_request(
                    session, "tools/call", {"name": tool_name, "arguments": params}
                )

                logger.info(f"Successfully executed tool {tool_name}")
                return response

            except MCPError:
                # Re-raise MCP errors as-is (they already have context)
                raise
            except Exception as e:
                logger.error(f"Failed to execute tool {tool_name}: {e}")
                raise MCPError(
                    f"Tool execution failed: {e}", server_name=server_name, tool_name=tool_name
                ) from e

    async def validate_tool_parameters(
        self, server_name: str, tool_name: str, params: dict[str, Any]
    ) -> list[str]:
        """
        Validate parameters for a tool without executing it.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            params: Tool parameters to validate

        Returns:
            List of validation error messages (empty if valid)

        Raises:
            MCPError: If server/tool not found
        """
        if server_name not in self.server_configs:
            raise MCPError(f"Server '{server_name}' not configured", server_name=server_name)

        # Discover tools to get the schema
        tools = await self.discover_tools(server_name)

        # Find the specific tool
        tool = None
        for t in tools:
            if t.name == tool_name:
                tool = t
                break

        if tool is None:
            available_tools = [t.name for t in tools]
            raise MCPError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}",
                server_name=server_name,
                tool_name=tool_name,
            )

        return tool.validate_parameters(params)

    async def _discover_tools_for_session(self, session: Session) -> list[Tool]:
        """
        Discover tools for an existing session without creating a new one.

        Args:
            session: Existing MCP session

        Returns:
            List of discovered tools
        """
        try:
            # Send tools/list request
            response = await self._send_mcp_request(session, "tools/list")
            tools_data = response.get("tools", [])

            # Convert to Tool objects
            tools = [Tool.from_mcp_tool(tool_data, session.server_name) for tool_data in tools_data]

            # Cache tools in session
            session.tools = tools

            logger.debug(f"Discovered {len(tools)} tools from {session.server_name}")
            return tools

        except Exception as e:
            raise MCPError(f"Failed to discover tools: {e}", server_name=session.server_name) from e

    def execute_tool_sync(
        self, server_name: str, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Synchronous wrapper for execute_tool.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, we can't use run_until_complete
                raise RuntimeError(
                    "Cannot use execute_tool_sync from within an async context. "
                    "Use execute_tool instead."
                )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute_tool(server_name, tool_name, params))

    async def _setup_mcp_server(self, session: Session, sandbox: Sandbox) -> None:
        """Setup MCP server in the sandbox."""
        config = session.config

        # Run installation commands if specified
        if config.install_commands:
            logger.debug(f"Running {len(config.install_commands)} installation commands")
            for i, command in enumerate(config.install_commands):
                logger.debug(f"Installing [{i + 1}/{len(config.install_commands)}]: {command}")

                # Security: properly escape the command
                escaped_command = shlex.quote(command)
                install_code = f"""
import subprocess
import sys
import os

# Run the installation command
result = subprocess.run({escaped_command}, shell=True, capture_output=True, text=True, check=False)

print(f"Command: {command}")
print(f"Exit code: {{result.returncode}}")
print(f"Stdout: {{result.stdout}}")
if result.stderr:
    print(f"Stderr: {{result.stderr}}")

if result.returncode != 0:
    raise Exception(f"Installation cmd failed with code {{result.returncode}}: {{result.stderr}}")
else:
    print("Installation command completed successfully")
"""
                result = await sandbox.run_code(install_code)
                if result.error:
                    raise MCPError(f"Failed to run install command '{command}': {result.error}")

                # Check if the command output indicates an error
                stdout = getattr(result, "stdout", "")
                if "Installation command failed" in stdout:
                    raise MCPError(f"Install command '{command}' failed")

                logger.debug(f"Successfully completed install command: {command}")

        # No file-based communication needed in stdio mode

        # Set environment variables if specified
        if config.env:
            env_commands = []
            for key, value in config.env.items():
                escaped_key = shlex.quote(key)
                escaped_value = shlex.quote(value)
                env_commands.append(f"export {escaped_key}={escaped_value}")

            env_code = "; ".join(env_commands)
            await sandbox.run_code(env_code)
            logger.debug(f"Set environment variables: {list(config.env.keys())}")

        # Extract file path from command
        cmd_parts = config.command.split()
        if len(cmd_parts) >= 2 and cmd_parts[0] == "python":
            file_path = cmd_parts[1]
        else:
            file_path = "/tmp/test_mcp_server.py"  # fallback

        # Note: In production, the MCP server file is assumed to already exist
        # or be provided via config. For tests, it's uploaded separately.
        logger.debug(f"Using MCP server file: {file_path}")

        # Use the command exactly as configured - different MCP servers handle stdio differently
        # Some use stdio by default, some need --stdio flag, some use other conventions
        command = config.command

        logger.debug(f"Starting MCP server with command: {command}")
        try:
            logger.debug(f"Executing command: {command}")

            # Buffer for partial stdout lines
            stdout_buffer = ""

            def _on_stdout(data: str) -> None:
                nonlocal stdout_buffer
                stdout_buffer += data
                while "\n" in stdout_buffer:
                    line, stdout_buffer = stdout_buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        response = json.loads(line)
                    except Exception:
                        continue

                    req_id = response.get("id")
                    if req_id and req_id in session.pending_requests:
                        fut = session.pending_requests.pop(req_id)
                        if not fut.done():
                            if "error" in response:
                                fut.set_exception(
                                    MCPError(f"MCP server error: {response['error']}")
                                )
                            else:
                                fut.set_result(response.get("result", {}))

            def _on_stderr(data: str) -> None:
                logger.error(f"MCP server stderr: {data}")

            process_handle = await sandbox.commands.run(
                command,
                background=True,
                on_stdout=_on_stdout,
                on_stderr=_on_stderr,
            )

            session.pid = process_handle.pid
            session.cmd_handle = process_handle
            logger.debug(f"Command started, PID={session.pid}")

            # Give the process a moment to start and check if it's running
            await asyncio.sleep(5)  # Give more time for server to fully initialize

            # Check if the process is still running
            try:
                ps_result = await sandbox.run_code(
                    """
import subprocess, os, time
print(f"Looking for PID {session.pid}")
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
lines = result.stdout.split('\\n')
our_process = [line for line in lines if str(session.pid) in line]
print(f"Our process ({session.pid}): {our_process}")
all_python = [line for line in lines if 'python' in line and 'test_mcp_server.py' in line]
print(f"All MCP processes: {all_python}")
"""
                )
                logger.debug(f"Process check result: {getattr(ps_result, 'stdout', '')}")
            except Exception as e:
                logger.debug(f"Failed to check processes: {e}")

            # Wait for server to become ready by checking for initialization
            await self._wait_for_server_ready(session, sandbox)

            session.initialized = True
            logger.debug(f"MCP server started successfully in session {session.session_id}")

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise MCPError(f"Failed to start MCP server: {e}") from e

    async def _wait_for_server_ready(
        self, session: Session, sandbox: Sandbox, timeout: int = 30
    ) -> None:
        """Wait briefly; stdio responses will prove readiness."""
        await asyncio.sleep(1)
        return

    async def _send_mcp_request(
        self, session: Session, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send MCP request via stdio when available, else fallback to files."""

        if not session.initialized:
            raise MCPError("MCP server not initialized")

        request_id = str(uuid.uuid4())
        request: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params:
            request["params"] = params

        if self._use_stdio and session.pid:
            # stdio path
            session_obj, sandbox = self.active_sessions[session.session_id]
            loop = asyncio.get_event_loop()
            fut: asyncio.Future[dict[str, Any]] = loop.create_future()
            session.pending_requests[request_id] = fut

            # Send over stdin
            await sandbox.commands.send_stdin(session.pid, json.dumps(request) + "\n")

            try:
                result: dict[str, Any] = await asyncio.wait_for(fut, timeout=30)
                return result
            except asyncio.TimeoutError:
                session.pending_requests.pop(request_id, None)
                raise MCPError(
                    f"Timeout waiting for MCP response to request {request_id}"
                ) from None

        raise MCPError("Session not configured for stdio communication")

    async def _wait_for_response(
        self, sandbox: Sandbox, response_file: str, request_id: str, timeout: int = 30
    ) -> dict[str, Any]:
        """Wait for MCP response using simple polling."""
        start_time = asyncio.get_event_loop().time()
        poll_count = 0

        logger.debug(f"Starting to wait for response {request_id}, timeout={timeout}s")

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            poll_count += 1

            # Simple approach: just read the entire response file each time
            read_code = f"""
import os
if os.path.exists('{response_file}'):
    with open('{response_file}', 'r') as f:
        file_content = f.read()
    print(f"FILE_SIZE:{{len(file_content)}}")
    if file_content.strip():
        print(f"FILE_CONTENT:{{file_content}}")
    else:
        print("FILE_CONTENT:")
else:
    print("FILE_SIZE:0")
    print("FILE_CONTENT:")
"""

            try:
                result = await sandbox.run_code(read_code)
                if result.error:
                    logger.debug(f"Poll {poll_count}: Error reading response file")
                    await asyncio.sleep(0.1)
                    continue

                # Extract content from logs
                file_content = ""
                for line in getattr(result, "stdout", "").splitlines():
                    if line.startswith("FILE_CONTENT:"):
                        file_content = line[13:]  # Remove "FILE_CONTENT:" prefix
                        break

                if file_content.strip():
                    logger.debug(
                        f"Poll {poll_count}: Got file content, checking for response {request_id}"
                    )

                    # Parse each line looking for our response
                    for response_line in file_content.strip().split("\n"):
                        if not response_line.strip():
                            continue
                        try:
                            response = json.loads(response_line.strip())
                            if response.get("id") == request_id:
                                logger.debug(f"Poll {poll_count}: Found matching response!")
                                if "error" in response:
                                    raise MCPError(f"MCP server error: {response['error']}")
                                result_data = response.get("result", {})
                                if isinstance(result_data, dict):
                                    return result_data
                                else:
                                    return {}
                        except json.JSONDecodeError as json_err:
                            logger.debug(f"Poll {poll_count}: JSON decode error: {json_err}")
                            continue
                else:
                    if poll_count % 10 == 0:  # Log every second
                        # Add detailed debugging every 10 polls
                        debug_result = await sandbox.run_code(
                            """
import os
import subprocess
print("=== DEBUG INFO ===")
print(f"Request file exists: {os.path.exists('/tmp/mcp/requests.jsonl')}")
print(f"Response file exists: {os.path.exists('/tmp/mcp/responses.jsonl')}")

if os.path.exists('/tmp/mcp/requests.jsonl'):
    with open('/tmp/mcp/requests.jsonl', 'r') as f:
        req_content = f.read()
    print(f"Request file lines: {len(req_content.splitlines())}")
    if req_content.strip():
        print(f"Last request line: {req_content.splitlines()[-1]}")

# Check response file size
if os.path.exists('/tmp/mcp/responses.jsonl'):
    with open('/tmp/mcp/responses.jsonl', 'r') as f:
        resp_content = f.read()
    print(f"Response file size: {len(resp_content)} chars")
    if resp_content.strip():
        print(f"Response content: {resp_content[:200]}...")
    else:
        print("Response file is EMPTY!")

# Check if MCP server process is still running
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
lines = result.stdout.split('\\n')
mcp_processes = [line for line in lines if 'test_mcp_server.py' in line]
print(f"MCP server processes: {len(mcp_processes)}")
for proc in mcp_processes:
    print(f"Process: {proc}")

# Check for any error logs or stderr from the MCP server
print("Checking for MCP server errors...")
try:
    # Check if the server process has any open file descriptors or error logs
    import glob
    log_files = glob.glob('/tmp/*.log') + glob.glob('/tmp/mcp/*.log')
    if log_files:
        print(f"Found log files: {log_files}")
        for log_file in log_files[:3]:  # Show first 3 log files
            with open(log_file, 'r') as f:
                content = f.read()[-500:]  # Last 500 chars
            print(f"{log_file}: {content}")
    else:
        print("No log files found in /tmp/")
except Exception as e:
    print(f"Error checking logs: {e}")

print("=== END DEBUG ===")
"""
                        )
                        if not debug_result.error:
                            debug_stdout = getattr(debug_result, "stdout", "")
                            logger.debug(f"Poll {poll_count}: Debug info: {debug_stdout}")
                        else:
                            logger.debug(f"Poll {poll_count}: Response file empty, still waiting")

            except Exception as err:
                logger.debug(f"Poll {poll_count}: Polling error: {err}")

            await asyncio.sleep(0.1)  # Poll every 100ms

        logger.error(
            f"Timeout after {poll_count} polls waiting for MCP response to request {request_id}"
        )
        raise MCPError(f"Timeout waiting for MCP response to request {request_id}")

    async def _cleanup_session(self, session: Session, sandbox: Sandbox) -> None:
        """Clean up session resources."""
        try:
            # Remove from active sessions first
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]

            # no file cleanup needed in stdio mode

            # Close sandbox
            await sandbox.kill()
            logger.debug(f"Cleaned up session {session.session_id}")

        except Exception as e:
            logger.warning(f"Error during session cleanup: {e}")
