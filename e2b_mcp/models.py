"""
Data models for E2B MCP.

Clean data structures without external dependencies.
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
import re
import asyncio


class MCPError(Exception):
    """Base exception for MCP operations."""
    
    def __init__(self, message: str, server_name: Optional[str] = None, tool_name: Optional[str] = None):
        """
        Initialize MCP error with context.
        
        Args:
            message: Error message
            server_name: Name of the MCP server where error occurred
            tool_name: Name of the tool where error occurred
        """
        self.server_name = server_name
        self.tool_name = tool_name
        
        context_parts = []
        if server_name:
            context_parts.append(f"server={server_name}")
        if tool_name:
            context_parts.append(f"tool={tool_name}")
        
        if context_parts:
            full_message = f"{message} ({', '.join(context_parts)})"
        else:
            full_message = message
            
        super().__init__(full_message)


@dataclass
class ServerConfig:
    """Configuration for an MCP server to run in E2B sandbox."""

    name: str
    command: str
    package: str = ""  # Python package to install (optional)
    description: str = ""
    timeout_minutes: int = 10
    env: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Server name must be a non-empty string")
        
        if not self.command or not isinstance(self.command, str):
            raise ValueError("Server command must be a non-empty string")
        
        if not isinstance(self.timeout_minutes, int) or self.timeout_minutes <= 0:
            raise ValueError("Timeout must be a positive integer")
        
        # Validate server name format (alphanumeric, underscore, hyphen only)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.name):
            raise ValueError(
                "Server name must contain only alphanumeric characters, underscores, and hyphens"
            )
        
        # Validate package name format if provided
        if self.package and not re.match(r'^[a-zA-Z0-9_.-]+$', self.package):
            raise ValueError(
                "Package name must contain only alphanumeric characters, dots, underscores, and hyphens"
            )

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ServerConfig":
        """Create ServerConfig from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Configuration data must be a dictionary")
        
        if "command" not in data:
            raise ValueError("Configuration must include 'command' field")
        
        return cls(
            name=name,
            command=data["command"],
            package=data.get("package", ""),
            description=data.get("description", ""),
            timeout_minutes=data.get("timeout_minutes", 10),
            env=data.get("env", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ServerConfig to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "package": self.package,
            "description": self.description,
            "timeout_minutes": self.timeout_minutes,
            "env": self.env,
        }

    def is_package_required(self) -> bool:
        """Check if this server requires package installation."""
        return bool(self.package.strip())

    def get_display_name(self) -> str:
        """Get a human-readable display name for the server."""
        return self.description if self.description else self.name


@dataclass
class Tool:
    """Represents an MCP tool discovered from a server."""

    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    server_name: str = ""

    def __post_init__(self):
        """Validate tool after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Tool name must be a non-empty string")
        
        if not isinstance(self.input_schema, dict):
            raise ValueError("Input schema must be a dictionary")

    @classmethod
    def from_mcp_tool(cls, tool_data: Dict[str, Any], server_name: str = "") -> "Tool":
        """Create Tool from MCP tool data."""        
        if tool_data is None or not isinstance(tool_data, dict):
            raise ValueError("Tool data must be a dictionary")
        
        if "name" not in tool_data:
            raise ValueError("Tool data must include 'name' field")
        
        return cls(
            name=tool_data["name"],
            description=tool_data.get("description", ""),
            input_schema=tool_data.get("inputSchema", {}),
            server_name=server_name,
        )

    def get_required_parameters(self) -> List[str]:
        """Get list of required parameter names."""
        if "properties" in self.input_schema:
            required = self.input_schema.get("required", [])
            return required if isinstance(required, list) else []
        return []

    def get_optional_parameters(self) -> List[str]:
        """Get list of optional parameter names."""
        if "properties" in self.input_schema:
            all_params = set(self.input_schema["properties"].keys())
            required_params = set(self.get_required_parameters())
            return list(all_params - required_params)
        return []

    def get_parameter_info(self, param_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific parameter."""
        if "properties" in self.input_schema:
            return self.input_schema["properties"].get(param_name)
        return None

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against the tool's input schema.
        
        Args:
            params: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required parameters
        required = self.get_required_parameters()
        for param in required:
            if param not in params:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types if schema provides them
        if "properties" in self.input_schema:
            for param_name, param_value in params.items():
                param_info = self.get_parameter_info(param_name)
                if param_info and "type" in param_info:
                    expected_type = param_info["type"]
                    if not self._validate_type(param_value, expected_type):
                        errors.append(f"Parameter '{param_name}' should be of type {expected_type}")
        
        return errors

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate that a value matches the expected JSON Schema type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, skip validation

    def get_full_name(self) -> str:
        """Get the full qualified name of the tool."""
        if self.server_name:
            return f"{self.server_name}.{self.name}"
        return self.name


@dataclass
class Session:
    """Represents an active MCP session in E2B sandbox."""

    session_id: str
    server_name: str
    config: ServerConfig
    sandbox_id: str
    initialized: bool = False
    tools: List[Tool] = field(default_factory=list)
    # PID of the running MCP server inside the sandbox (available once initialized)
    pid: int = 0
    # Map of JSON-RPC request id -> asyncio.Future used for awaiting responses
    pending_requests: Dict[str, "asyncio.Future[Any]"] = field(default_factory=dict, repr=False)
    cmd_handle: Any = field(default=None, repr=False)

    def __post_init__(self):
        """Validate session after initialization."""
        if not self.session_id or not isinstance(self.session_id, str):
            raise ValueError("Session ID must be a non-empty string")
        
        if not self.server_name or not isinstance(self.server_name, str):
            raise ValueError("Server name must be a non-empty string")
        
        if not self.sandbox_id or not isinstance(self.sandbox_id, str):
            raise ValueError("Sandbox ID must be a non-empty string")

    def is_ready(self) -> bool:
        """Check if the session is ready for tool execution."""
        return self.initialized

    def get_tool_count(self) -> int:
        """Get the number of discovered tools in this session."""
        return len(self.tools)

    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by name from this session."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def list_tool_names(self) -> List[str]:
        """Get a list of all tool names in this session."""
        return [tool.name for tool in self.tools]

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information as a dictionary."""
        return {
            "session_id": self.session_id,
            "server_name": self.server_name,
            "sandbox_id": self.sandbox_id,
            "initialized": self.initialized,
            "tool_count": self.get_tool_count(),
            "tools": self.list_tool_names(),
            "config": self.config.to_dict(),
        }