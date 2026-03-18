import asyncio
import fnmatch
import json
import os
import socket
import sys
import uuid
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.datastructures import MutableHeaders

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("fusion360-mcp-server")
logger.setLevel(logging.DEBUG)

SERVER_VERSION = "0.3.1"

def get_addin_host():
    return os.environ.get('F360_ADDIN_HOST', '127.0.0.1')

def get_addin_port():
    return int(os.environ.get('F360_ADDIN_PORT', 30011))

mcp = FastMCP(
    "fusion360-mcp",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    json_response=False,
)

# Command history for testing/verification
command_history: List[Dict[str, Any]] = []
def should_record_commands():
    return os.environ.get("F360_RECORD_COMMANDS", "false").lower() == "true"

@mcp.resource("fusion360://cheat-sheet.md")
def get_cheat_sheet() -> str:
    """Returns the Fusion 360 MCP Cheat Sheet for LLMs."""
    path = os.path.join(os.path.dirname(__file__), "mcp_cheat_sheet.md")
    if not os.path.exists(path):
        # Try finding it in the same directory as this script if it's served elsewhere
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_cheat_sheet.md")
    
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "# Cheat Sheet Not Found\nPlease ensure mcp_cheat_sheet.md is in the server directory."

@mcp.resource("fusion360://command-history.json")
def get_command_history_json() -> str:
    """Returns the recorded command history as JSON."""
    return json.dumps(command_history, indent=2)

@mcp.tool()
def export_command_history() -> List[Dict[str, Any]]:
    """Returns the recorded command history."""
    return command_history

@mcp.tool()
async def ping_server() -> str:
    """Simple tool to verify MCP communication."""
    return "pong"

@mcp.tool()
async def get_server_info() -> Dict[str, Any]:
    """Returns version and configuration info for the MCP server."""
    return {
        "version": SERVER_VERSION,
        "addin_host": get_addin_host(),
        "addin_port": get_addin_port()
    }

# Global state for persistent connection to the Add-in
_addin_connection = None  # (reader, writer, host, port)
_conn_lock: Optional[asyncio.Lock] = None

async def get_addin_connection():
    """
    Returns a persistent reader/writer pair for the Add-in connection.
    Reconnects if the host/port has changed or if the connection is dead.
    """
    global _addin_connection, _conn_lock
    host = get_addin_host()
    port = get_addin_port()
    
    if _conn_lock is None:
        _conn_lock = asyncio.Lock()
    
    async with _conn_lock:
        if _addin_connection:
            prev_reader, prev_writer, prev_host, prev_port = _addin_connection
            if prev_host == host and prev_port == port:
                # Basic check for dead connection (transport closing)
                if not prev_writer.is_closing():
                    return prev_reader, prev_writer
            
            # Host/Port changed or writer closing, clean up
            try:
                prev_writer.close()
                await prev_writer.wait_closed()
            except:
                pass
            _addin_connection = None

        # Create new connection
        logger.info(f"Establishing persistent connection to Add-In at {host}:{port}...")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, limit=50 * 1024 * 1024),
            timeout=30.0
        )
        _addin_connection = (reader, writer, host, port)
        logger.info("Persistent connection established.")
        return reader, writer

async def drop_addin_connection():
    """Drops the current persistent connection."""
    global _addin_connection, _conn_lock
    if _conn_lock is None:
        _conn_lock = asyncio.Lock()
        
    async with _conn_lock:
        if _addin_connection:
            _, writer, _, _ = _addin_connection
            try:
                writer.close()
                # don't wait_closed here to avoid hangs in callback threads
            except:
                pass
            _addin_connection = None

async def call_addin(method: str, params: Optional[Dict[str, Any]] = None):
    """
    Calls a method on the Fusion 360 Add-in via persistent TCP socket.
    Handles automatic reconnection and one retry on failure.
    """
    if params is None:
        params = {}
        
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }
    
    host = get_addin_host()
    port = get_addin_port()
    
    logger.info(f"Command: {method} (to {host}:{port})")
    p_str = json.dumps(params)
    logger.info(f"Arguments: {p_str[:500]}{'...' if len(p_str) > 500 else ''}")
    
    # Record command if enabled
    record = None
    if should_record_commands():
        from datetime import datetime, timezone
        record = {
            "method": method,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "status": "pending"
        }
        command_history.append(record)

    for attempt in range(2):
        try:
            reader, writer = await get_addin_connection()
            
            # Send request terminated by newline
            writer.write(json.dumps(request).encode('utf-8') + b'\n')
            await writer.drain()
            
            # Read response terminated by newline
            data = await asyncio.wait_for(reader.readuntil(b'\n'), timeout=30.0)
            
            response = json.loads(data.decode('utf-8').strip())
            
            if "error" in response:
                if record:
                    record["status"] = "error"
                    record["error"] = response["error"]
                raise Exception(f"Fusion 360 Error: {response['error']}")
            
            result = response.get("result", {})
            
            if record:
                record["status"] = "success"
                record["result"] = result

            # Log response result
            res_to_log = result.copy() if isinstance(result, dict) else result
            if isinstance(res_to_log, dict) and "file_content_base64" in res_to_log:
                res_to_log["file_content_base64"] = "[BASE64_BLOB_TRUNCATED]"
            
            r_str = json.dumps(res_to_log)
            logger.debug(f"Full response result: {r_str}")
            logger.info(f"Response: {r_str[:500]}{'...' if len(r_str) > 500 else ''}")
            
            return result

        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError, asyncio.TimeoutError) as e:
            logger.warning(f"Add-in connection failure on attempt {attempt + 1}: {e}")
            await drop_addin_connection()
            if attempt == 1:
                error_msg = f"Failed to communicate with Add-In at {host}:{port} after 2 attempts: {e}"
                if record:
                    record["status"] = "error"
                    record["error"] = error_msg
                logger.error(error_msg)
                raise Exception(error_msg)
            # Re-try on attempt 0
            continue
        except Exception as e:
            if record and record.get("status") == "pending":
                record["status"] = "exception"
                record["error"] = str(e)
            logger.error(f"Error communicating with Add-In: {str(e)}")
            raise

def register_dynamic_tool(name, metadata, module_globals=None):
    """
    Dynamically creates and registers an MCP tool based on metadata.
    """
    params_list = metadata.get("parameters", [])
    raw_doc = metadata.get("doc", "No description provided.")
    
    # Clean up the docstring
    import inspect
    docstring = inspect.cleandoc(raw_doc)
    
    # Append cheat sheet reference prominently
    docstring += "\n\n    IMPORTANT: Refer to fusion360://cheat-sheet.md for modeling patterns and units (cm)."
    
    # Build the function signature string and collect parameter docs
    arg_strings = []
    param_docs = []
    addin_param_names = [p["name"] for p in params_list]
    
    for param in params_list:
        arg_name = param["name"]
        arg_str = arg_name
        
        # Add type annotation if available
        annotation = param.get("annotation", "Any")
        if annotation and annotation != "inspect._empty":
            arg_str += f": {annotation}"
            
        # Add default value if available
        if param.get("has_default"):
            default_val = param["default"]
            if isinstance(default_val, str):
                arg_str += f' = "{default_val}"'
            else:
                arg_str += f" = {default_val}"
        arg_strings.append(arg_str)
        
        # Collect description for docstring enrichment
        if param.get("description"):
            param_docs.append(f"        {arg_name}: {param['description']}")
    
    # Add plane alias to signature if plane_name is present but plane is not
    if "plane_name" in addin_param_names and "plane" not in addin_param_names:
        arg_strings.append('plane: Optional[str] = None')
    
    if param_docs:
        docstring += "\n\n    Args:\n" + "\n".join(param_docs)
    
    full_sig = ", ".join(arg_strings)
    
    # Add local_file_path for specific tools if they seem to return files
    if name in ["export_model", "capture_screenshot"]:
        if "local_file_path" not in addin_param_names:
            field = "local_file_path: Optional[str] = None"
            if full_sig:
                full_sig += f", {field}"
            else:
                full_sig = field
            docstring += f"\n\n    Args (MCP Host):\n        local_file_path: Optional path to save the returned file on the host machine."
    
    # Create the function source
    doc_lines = docstring.split("\n")
    indented_doc = "\n".join("    " + line for line in doc_lines)
    
    source = f"""
async def {name}({full_sig}):
    \"\"\"
{indented_doc}
    \"\"\"
    # Collect all local variables
    all_vars = locals().copy()
    
    # Strip server-side only arguments before sending to the Add-in
    local_file_path = all_vars.pop("local_file_path", None)
    
    # Special case: map 'plane' to 'plane_name' if 'plane_name' is expected but 'plane' was provided
    if "plane_name" in valid_addin_params and "plane" in all_vars and all_vars["plane"] is not None:
        all_vars["plane_name"] = all_vars.pop("plane")

    # Filter for only those arguments the add-in expects
    args = {{k: v for k, v in all_vars.items() if k in valid_addin_params}}
    
    result = await call_addin('{name}', args)
    
    # Special handling for file downloads if local_file_path was provided
    if local_file_path and "file_content_base64" in result:
        import base64
        try:
            with open(local_file_path, "wb") as f:
                f.write(base64.b64decode(result["file_content_base64"]))
            logger.info(f"Saved returned file to {{local_file_path}}")
        except Exception as e:
            logger.error(f"Failed to save file: {{str(e)}}")
            
    return result
"""
    
    # Execute in a namespace with necessary imports
    namespace = {
        "call_addin": call_addin,
        "Optional": Optional,
        "List": List,
        "Dict": Dict,
        "Any": Any,
        "logger": logger,
        "valid_addin_params": set(addin_param_names)
    }
    
    try:
        exec(source, namespace)
        handler = namespace[name]
        
        # Inject into the provided globals (or this module's globals)
        if module_globals is not None:
            module_globals[name] = handler
        else:
            globals()[name] = handler
            
        # Register with MCP
        mcp.tool()(handler)
        logger.info(f"Registered dynamic tool: {name}")
    except Exception as e:
        logger.error(f"Failed to register dynamic tool {name}: {str(e)}")

async def initialize_tools(module_globals=None):
    """
    Fetches tool metadata from the Add-in and registers them.
    If module_globals is provided, injects the handlers into it.
    """
    logger.info("Initializing dynamic tools from Fusion 360 Add-in...")
    try:
        metadata = await call_addin("_get_command_metadata", {})
        if not metadata:
            logger.warning("No tool metadata received from Add-in.")
            return

        for cmd_name, cmd_info in metadata.items():
            if cmd_name.startswith("_"):
                continue # Skip internal commands
            
            register_dynamic_tool(cmd_name, cmd_info, module_globals)
            
        logger.info(f"Successfully registered {len(metadata)} tools.")
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise # Re-raise to allow discovery_loop to catch it

@mcp.tool()
async def refresh_tools() -> str:
    """
    Reloads tool definitions from the Fusion 360 Add-in.
    Useful if you've added new commands to the add-in without wanting to restart the server.
    """
    await initialize_tools()
    return "Tools refreshed successfully."

@mcp.tool()
async def update_and_reload_mcp(git_repo: str = "https://github.com/deece/fusion360-mcp.git", branch: str = "master") -> str:
    """
    Updates the Fusion 360 MCP Wrapper from a Git repository and restarts both the server and the Fusion 360 Add-in.
    
    Args:
        git_repo: The URL of the repository to pull from.
        branch: The specific branch to checkout and update to.
    """
    import subprocess
    import time
    
    logger.info(f"Triggering auto-update from {git_repo} branch {branch}")
    
    try:
        # Get the root directory of the repo (one level up from this file's dir)
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Update files via Git
        logger.info(f"Updating files in {repo_dir}...")
        
        # Ensure it's a git repo and has origin
        git_origin = "https://github.com/InfernoEmbedded/f360-mcp.git"
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            logger.info(f"Initializing git repo in {repo_dir}...")
            subprocess.run(["git", "init"], cwd=repo_dir)
            subprocess.run(["git", "remote", "add", "origin", git_origin], cwd=repo_dir)
        else:
            # Check if origin exists
            remotes = subprocess.run(["git", "remote"], cwd=repo_dir, capture_output=True, text=True).stdout
            if "origin" not in remotes:
                logger.info(f"Adding origin remote {git_origin}...")
                subprocess.run(["git", "remote", "add", "origin", git_origin], cwd=repo_dir)

        cmds = [
            ["git", "fetch", "origin", branch],
            ["git", "checkout", "-B", branch, f"origin/{branch}"],
            ["git", "reset", "--hard", f"origin/{branch}"]
        ]
        
        full_results = []
        for cmd in cmds:
            result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
            full_results.append(f"Command: {' '.join(cmd)}\nStdout: {result.stdout}\nStderr: {result.stderr}")
            if result.returncode != 0:
                logger.error(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
                return f"Error during git update:\n" + "\n".join(full_results)
                
        # Get head commit info
        status_res = subprocess.run(["git", "log", "-1", "--oneline"], cwd=repo_dir, capture_output=True, text=True)
        full_results.append(f"HEAD: {status_res.stdout}")
                
        logger.info("Files updated successfully. Telling Add-in to reload...")
                
        # 2. Tell the Fusion 360 Add-in to reload itself
        addin_response = await call_addin("reload_addin", {})
        
        # 3. Restart this server process
        logger.info("Restarting MCP Server process...")
        
        def restart_server():
            time.sleep(1) # Give the add-in a moment to start its reloader script
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        # Run restart in a background thread so we can return the response first
        import threading
        threading.Thread(target=restart_server, daemon=True).start()
        
        return f"Successfully updated code from {branch}. Logs:\n" + "\n".join(full_results)
        
    except Exception as e:
        logger.error(f"Auto-update failed: {str(e)}")
        return f"Error during update and reload: {str(e)}"

# Placeholder for lazy tool lookup
class ToolPlaceholder:
    def __init__(self, tool_name):
        self._tool_name = tool_name
    async def __call__(self, *args, **kwargs):
        # Check module globals for the real handler
        handler = globals().get(self._tool_name)
        # If it's a real handler (not this placeholder), call it
        if handler and not isinstance(handler, ToolPlaceholder):
            return await handler(*args, **kwargs)
            
        # Otherwise try to initialize
        try:
            await initialize_tools()
            handler = globals().get(self._tool_name)
            if handler and not isinstance(handler, ToolPlaceholder):
                return await handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"Lazy init failed for {self._tool_name}: {e}")
            
        raise RuntimeError(f"Tool {self._tool_name} is not registered. Ensure the Fusion 360 Add-in is running and call initialize_tools().")

def __getattr__(name: str) -> Any:
    """
    Handle lazy lookup of dynamically registered tools.
    Allows 'from server import some_tool' even before initialization.
    """
    if name.startswith("_") or name == "mcp":
        raise AttributeError(f"module {__name__} has no attribute {name}")
    
    if name in globals():
        val = globals()[name]
        if not isinstance(val, ToolPlaceholder):
            return val
        
    logger.debug(f"Lazy lookup for {name}")
    return ToolPlaceholder(name)

async def start_discovery_task():
    """
    Async task to discover tools from the Add-in.
    """
    logger.info("Background tool discovery task started.")
    while True:
        try:
            await initialize_tools()
            logger.info("Successfully discovered and registered tools from Add-in.")
            break 
        except Exception as e:
            logger.warning(f"Tool discovery failed, retrying in 10s: {e}")
            await asyncio.sleep(10)

def _get_allowed_origins():
    """Parse allowed origins from environment variable."""
    env = os.environ.get("MCP_ALLOWED_ORIGINS", "")
    if env.strip():
        return [o.strip() for o in env.split(",") if o.strip()]
    return ["http://localhost:*", "http://127.0.0.1:*", "https://localhost:*", "https://127.0.0.1:*"]

def _origin_is_allowed(origin: str, allowed_patterns: list) -> bool:
    """Check if an origin matches any of the allowed patterns."""
    for pattern in allowed_patterns:
        if fnmatch.fnmatch(origin, pattern):
            return True
    return False

def create_starlette_app(mcp, transport_env, host, port):
    """
    Creates a unified Starlette application for SSE and Streamable HTTP.
    """
    # Ensure settings are synced
    mcp.settings.host = host
    mcp.settings.port = int(port)
    
    allowed_origins = _get_allowed_origins()
    logger.info(f"Allowed origins: {allowed_origins}")
    
    # Create apps for both transports
    sse_app = mcp.sse_app()
    http_app = mcp.streamable_http_app()
    
    # Find the Streamable HTTP handler
    mcp_handler = None
    for r in http_app.routes:
        if isinstance(r, Route) and r.path == mcp.settings.streamable_http_path:
            mcp_handler = r.app
            break

    # Build unified routes
    routes = []
    routes.append(Route(mcp.settings.sse_path, endpoint=sse_app, methods=["GET", "HEAD"]))
    if mcp_handler:
        routes.append(Route(mcp.settings.sse_path, mcp_handler, methods=["POST", "DELETE"]))
    
    for r in sse_app.routes:
        if isinstance(r, Route) and r.path == mcp.settings.message_path:
            routes.append(r)
            
    for r in http_app.routes:
        if isinstance(r, Route) and r.path == mcp.settings.streamable_http_path:
            routes.append(r)
    
    async def status_route(request):
        return JSONResponse({
            "status": "ok",
            "version": SERVER_VERSION,
            "transport_config": transport_env,
            "supported_endpoints": ["/sse", "/messages", "/mcp", "/history"]
        })
    routes.append(Route("/", endpoint=status_route))
    
    async def history_route(request):
        return JSONResponse({
            "command_history": command_history
        })
    routes.append(Route("/history", endpoint=history_route))
    
    @asynccontextmanager
    async def lifespan(app: Starlette):
        logger.info("Server lifespan starting...")
        discovery_task = asyncio.create_task(start_discovery_task())
        
        manager = None
        try:
            manager = mcp.session_manager
        except RuntimeError:
            pass

        if manager:
            try:
                async with manager.run():
                    yield
            except RuntimeError as e:
                if "can only be called once" in str(e):
                    yield
                else:
                    raise
        else:
            yield
        
        logger.info("Server lifespan ending")
        discovery_task.cancel()
        try:
            await discovery_task
        except asyncio.CancelledError:
            pass

    app = Starlette(routes=routes, lifespan=lifespan)
    
    class MCPComplianceMiddleware:
        def __init__(self, app: ASGIApp):
            self.app = app
        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode("latin-1")
            if origin and not _origin_is_allowed(origin, allowed_origins):
                response = JSONResponse(
                    {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Forbidden: invalid Origin"}},
                    status_code=403
                )
                response.headers["X-MCP-Protocol-Version"] = "2024-11-05"
                await response(scope, receive, send)
                return
            async def send_with_compliance_headers(message: Message):
                if message["type"] == "http.response.start":
                    headers = MutableHeaders(scope=message)
                    headers.append("X-MCP-Protocol-Version", "2024-11-05")
                await send(message)
            await self.app(scope, receive, send_with_compliance_headers)

    app.add_middleware(MCPComplianceMiddleware)
    cors_origins = [p for p in allowed_origins if "*" not in p]
    allow_all = any("*" in p for p in allowed_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else cors_origins,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    return app

if __name__ == "__main__":
    try:
        transport_env = os.environ.get("MCP_TRANSPORT", "stdio").lower()
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        port = os.environ.get("MCP_PORT", "8000")
        
        logger.info(f"Starting MCP Server (transport={transport_env}, host={host}, port={port})")
        
        if transport_env in ["sse", "streamable-http"]:
            import uvicorn
            app = create_starlette_app(mcp, transport_env, host, port)
            config = uvicorn.Config(app, host=host, port=int(port), log_level="info")
            server = uvicorn.Server(config)
            asyncio.run(server.serve())
        else:
            # For stdio, we don't have a lifespan easily, so we run discovery in the loop
            loop = asyncio.get_event_loop()
            loop.create_task(start_discovery_task())
            mcp.run(transport="stdio")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)
