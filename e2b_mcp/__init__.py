"""
E2B MCP - Run MCP servers securely in E2B sandboxes.

This package provides a simple way to run MCP (Model Context Protocol) servers
in secure E2B sandboxes, enabling safe execution of untrusted tools and code.
"""

from .runner import E2BMCPRunner
from .models import ServerConfig, Tool, Session, MCPError
from .version import __version__

__all__ = [
    "E2BMCPRunner",
    "ServerConfig",
    "Tool",
    "Session",
    "MCPError",
    "__version__",
]