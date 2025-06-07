#!/usr/bin/env python3
"""
CLI interface for e2b-mcp library.

Provides command-line access to all e2b-mcp functionality.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import click

from .runner import E2BMCPRunner
from .models import MCPError


def get_config_dir() -> Path:
    """Get the configuration directory for e2b-mcp."""
    config_dir = Path.home() / ".e2b-mcp"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_servers_config_file() -> Path:
    """Get the servers configuration file path."""
    return get_config_dir() / "servers.json"


def load_servers_config() -> Dict[str, Any]:
    """Load servers configuration from file."""
    config_file = get_servers_config_file()
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        click.echo(f"Error loading config: {e}", err=True)
        return {}


def save_servers_config(config: Dict[str, Any]) -> None:
    """Save servers configuration to file."""
    config_file = get_servers_config_file()
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        click.echo(f"Error saving config: {e}", err=True)
        sys.exit(1)


def get_runner_with_config() -> E2BMCPRunner:
    """Create an E2BMCPRunner with loaded server configurations."""
    runner = E2BMCPRunner()
    
    config = load_servers_config()
    if config:
        try:
            runner.add_servers(config)
        except Exception as e:
            click.echo(f"Error loading server configs: {e}", err=True)
            sys.exit(1)
    
    return runner


@click.group()
@click.version_option()
def cli():
    """
    E2B MCP CLI - Run MCP servers securely in E2B sandboxes.
    
    This CLI provides access to all e2b-mcp functionality from the command line.
    """
    pass


@cli.group()
def server():
    """Manage MCP server configurations."""
    pass


@server.command("add")
@click.argument("name")
@click.option("--command", required=True, help="Command to run the MCP server")
@click.option("--env", multiple=True, help="Environment variables (format: KEY=VALUE)")
@click.option("--package", help="Python package to install")
@click.option("--description", help="Server description")
@click.option("--timeout", default=10, help="Timeout in minutes (default: 10)")
def server_add(name: str, command: str, env: tuple, package: Optional[str], 
               description: Optional[str], timeout: int):
    """Add a new MCP server configuration."""
    
    # Parse environment variables
    env_dict = {}
    for env_var in env:
        if "=" not in env_var:
            click.echo(f"Invalid environment variable format: {env_var}", err=True)
            click.echo("Use format: KEY=VALUE", err=True)
            sys.exit(1)
        key, value = env_var.split("=", 1)
        env_dict[key] = value
    
    # Create server config
    server_config = {
        "command": command,
        "env": env_dict,
        "timeout_minutes": timeout
    }
    
    if package:
        server_config["package"] = package
    if description:
        server_config["description"] = description
    
    # Load existing config and add new server
    config = load_servers_config()
    config[name] = server_config
    save_servers_config(config)
    
    click.echo(f"✅ Added server '{name}'")
    click.echo(f"   Command: {command}")
    if env_dict:
        click.echo(f"   Environment: {list(env_dict.keys())}")


@server.command("list")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def server_list(output_json: bool):
    """List all configured MCP servers."""
    config = load_servers_config()
    
    if not config:
        click.echo("No servers configured.")
        click.echo("Use 'e2b-mcp server add' to add a server.")
        return
    
    if output_json:
        click.echo(json.dumps(config, indent=2))
        return
    
    click.echo("Configured MCP Servers:")
    click.echo("=" * 40)
    
    for name, server_config in config.items():
        click.echo(f"\n📡 {name}")
        click.echo(f"   Command: {server_config['command']}")
        if server_config.get('description'):
            click.echo(f"   Description: {server_config['description']}")
        if server_config.get('package'):
            click.echo(f"   Package: {server_config['package']}")
        if server_config.get('env'):
            click.echo(f"   Environment: {list(server_config['env'].keys())}")
        click.echo(f"   Timeout: {server_config.get('timeout_minutes', 10)} minutes")


@server.command("remove")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def server_remove(name: str, yes: bool):
    """Remove an MCP server configuration."""
    config = load_servers_config()
    
    if name not in config:
        click.echo(f"Server '{name}' not found.", err=True)
        sys.exit(1)
    
    if not yes:
        click.confirm(f"Remove server '{name}'?", abort=True)
    
    del config[name]
    save_servers_config(config)
    
    click.echo(f"✅ Removed server '{name}'")


@cli.group()
def tools():
    """Discover and execute MCP tools."""
    pass


@tools.command("list")
@click.argument("server_name")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def tools_list(server_name: str, output_json: bool):
    """List tools available from an MCP server."""
    
    async def run():
        try:
            runner = get_runner_with_config()
            discovered_tools = await runner.discover_tools(server_name)
            
            if output_json:
                tools_data = []
                for tool in discovered_tools:
                    tools_data.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "server_name": tool.server_name
                    })
                click.echo(json.dumps(tools_data, indent=2))
                return
            
            if not discovered_tools:
                click.echo(f"No tools found for server '{server_name}'")
                return
            
            click.echo(f"Tools from '{server_name}' ({len(discovered_tools)} found):")
            click.echo("=" * 50)
            
            for tool in discovered_tools:
                click.echo(f"\n🔧 {tool.name}")
                click.echo(f"   {tool.description}")
                
                required_params = tool.get_required_parameters()
                optional_params = tool.get_optional_parameters()
                
                if required_params or optional_params:
                    click.echo("   Parameters:")
                    for param in required_params:
                        param_info = tool.get_parameter_info(param)
                        param_type = param_info.get('type', 'any') if param_info else 'any'
                        click.echo(f"     • {param} ({param_type}) - required")
                    for param in optional_params:
                        param_info = tool.get_parameter_info(param)
                        param_type = param_info.get('type', 'any') if param_info else 'any'
                        click.echo(f"     • {param} ({param_type}) - optional")
        
        except MCPError as e:
            click.echo(f"MCP Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@tools.command("execute")
@click.argument("server_name")
@click.argument("tool_name")
@click.option("--params", help="Tool parameters as JSON string")
@click.option("--param", multiple=True, help="Individual parameters (format: key=value)")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON response")
def tools_execute(server_name: str, tool_name: str, params: Optional[str], 
                  param: tuple, output_json: bool):
    """Execute a tool on an MCP server."""
    
    # Parse parameters
    tool_params = {}
    
    if params:
        try:
            tool_params = json.loads(params)
        except json.JSONDecodeError as e:
            click.echo(f"Invalid JSON in --params: {e}", err=True)
            sys.exit(1)
    
    # Add individual parameters
    for p in param:
        if "=" not in p:
            click.echo(f"Invalid parameter format: {p}", err=True)
            click.echo("Use format: key=value", err=True)
            sys.exit(1)
        key, value = p.split("=", 1)
        
        # Try to parse as JSON, fallback to string
        try:
            tool_params[key] = json.loads(value)
        except json.JSONDecodeError:
            tool_params[key] = value
    
    async def run():
        try:
            runner = get_runner_with_config()
            result = await runner.execute_tool(server_name, tool_name, tool_params)
            
            if output_json:
                click.echo(json.dumps(result, indent=2))
                return
            
            click.echo(f"✅ Executed {tool_name} on {server_name}")
            click.echo("=" * 40)
            
            # Pretty print the result
            if isinstance(result, dict):
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                click.echo(item.get("text", ""))
                            else:
                                click.echo(str(item))
                    else:
                        click.echo(str(content))
                else:
                    click.echo(json.dumps(result, indent=2))
            else:
                click.echo(str(result))
        
        except MCPError as e:
            click.echo(f"MCP Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@cli.command("quick")
@click.argument("command")
@click.argument("tool_name")
@click.option("--params", help="Tool parameters as JSON string")
@click.option("--param", multiple=True, help="Individual parameters (format: key=value)")
@click.option("--env", multiple=True, help="Environment variables (format: KEY=VALUE)")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON response")
def quick_execute(command: str, tool_name: str, params: Optional[str], 
                  param: tuple, env: tuple, output_json: bool):
    """
    Quick execute: run a tool without saving server config.
    
    Example:
    e2b-mcp quick "npx -y @modelcontextprotocol/server-github" search_repositories --params '{"query": "e2b"}'
    """
    
    # Parse environment variables
    env_dict = {}
    for env_var in env:
        if "=" not in env_var:
            click.echo(f"Invalid environment variable format: {env_var}", err=True)
            sys.exit(1)
        key, value = env_var.split("=", 1)
        env_dict[key] = value
    
    # Parse parameters
    tool_params = {}
    if params:
        try:
            tool_params = json.loads(params)
        except json.JSONDecodeError as e:
            click.echo(f"Invalid JSON in --params: {e}", err=True)
            sys.exit(1)
    
    for p in param:
        if "=" not in p:
            click.echo(f"Invalid parameter format: {p}", err=True)
            sys.exit(1)
        key, value = p.split("=", 1)
        try:
            tool_params[key] = json.loads(value)
        except json.JSONDecodeError:
            tool_params[key] = value
    
    async def run():
        try:
            runner = E2BMCPRunner()
            runner.add_server_from_dict("temp_server", {
                "command": command,
                "env": env_dict
            })
            
            result = await runner.execute_tool("temp_server", tool_name, tool_params)
            
            if output_json:
                click.echo(json.dumps(result, indent=2))
                return
            
            click.echo(f"✅ Executed {tool_name}")
            click.echo("=" * 30)
            
            # Pretty print the result
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            click.echo(item.get("text", ""))
                        else:
                            click.echo(str(item))
                else:
                    click.echo(str(content))
            else:
                click.echo(json.dumps(result, indent=2))
        
        except MCPError as e:
            click.echo(f"MCP Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())


@cli.command("config")
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--edit", is_flag=True, help="Edit configuration file")
@click.option("--reset", is_flag=True, help="Reset configuration")
def config_cmd(show: bool, edit: bool, reset: bool):
    """Manage e2b-mcp configuration."""
    
    if reset:
        if click.confirm("Reset all configuration?"):
            config_file = get_servers_config_file()
            if config_file.exists():
                config_file.unlink()
            click.echo("✅ Configuration reset")
        return
    
    if edit:
        config_file = get_servers_config_file()
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {config_file}")
        return
    
    if show or True:  # Default to show
        config_file = get_servers_config_file()
        click.echo(f"Configuration file: {config_file}")
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                click.echo(f.read())
        else:
            click.echo("No configuration file found.")


if __name__ == "__main__":
    cli() 