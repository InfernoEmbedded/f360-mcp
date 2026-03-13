import asyncio
import json
import os
import socket
import sys
import uuid
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fusion360-mcp-server")

def get_addin_host():
    return os.environ.get('F360_ADDIN_HOST', '127.0.0.1')

def get_addin_port():
    return int(os.environ.get('F360_ADDIN_PORT', 30011))

mcp = FastMCP("fusion360-mcp")

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

async def send_to_addin(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }
    
    host = get_addin_host()
    port = get_addin_port()
    
    def sync_request():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10.0)
                s.connect((host, port))
                s.sendall(json.dumps(request).encode('utf-8') + b'\n')
                
                # Read response
                buffer = ""
                while True:
                    data = s.recv(16384)
                    if not data:
                        break
                    buffer += data.decode('utf-8')
                    if '\n' in buffer:
                        break
                
                if not buffer.strip():
                    return {"error": "No response from Add-In"}
                
                return json.loads(buffer.strip())
        except Exception as e:
            return {"error": str(e)}

    try:
        response = await asyncio.to_thread(sync_request)
        if "error" in response:
            raise Exception(f"Fusion 360 Error: {response['error']}")
        return response.get("result", {})
    except Exception as e:
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
    
    if param_docs:
        docstring += "\n\n    Args:\n" + "\n".join(param_docs)
    
    full_sig = ", ".join(arg_strings)
    
    # Add local_file_path for specific tools if they seem to return files
    if name in ["export_model", "capture_screenshot"]:
        if "local_file_path" not in [p["name"] for p in params_list]:
            field = "local_file_path: Optional[str] = None"
            if full_sig:
                full_sig += f", {field}"
            else:
                full_sig = field
            docstring += f"\n\n    Args (MCP Host):\n        local_file_path: Optional path to save the returned file on the host machine."
    
    # Create the function source
    # We use indent to ensure the docstring is properly formatted in the exec'd string
    doc_lines = docstring.split("\n")
    indented_doc = "\n".join("    " + line for line in doc_lines)
    
    source = f"""
async def {name}({full_sig}):
    \"\"\"
{indented_doc}
    \"\"\"
    # Collect all local variables (which are the function arguments)
    args = locals().copy()
    result = await send_to_addin('{name}', args)
    
    # Special handling for file downloads if local_file_path is provided
    if "local_file_path" in args and args["local_file_path"] and "file_content_base64" in result:
        import base64
        try:
            with open(args["local_file_path"], "wb") as f:
                f.write(base64.b64decode(result["file_content_base64"]))
            logger.info(f"Saved returned file to {{args['local_file_path']}}")
        except Exception as e:
            logger.error(f"Failed to save file: {{str(e)}}")
            
    return result
"""
    
    # Execute in a namespace with necessary imports
    namespace = {
        "send_to_addin": send_to_addin,
        "Optional": Optional,
        "List": List,
        "Dict": Dict,
        "Any": Any,
        "logger": logger
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
        # FastMCP mcp.tool() returns a decorator, so we call it on our handler
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
        metadata = await send_to_addin("_get_command_metadata", {})
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
        
        # Make sure it's a git repo
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return f"Error: Directory {repo_dir} is not a git repository."
            
        cmds = [
            ["git", "fetch", "origin", branch],
            ["git", "checkout", branch],
            ["git", "reset", "--hard", f"origin/{branch}"]
        ]
        
        for cmd in cmds:
            result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
                return f"Error during git update: {result.stderr}"
                
        logger.info("Files updated successfully. Telling Add-in to reload...")
                
        # 2. Tell the Fusion 360 Add-in to reload itself
        # This will spin off a temporary script in Fusion that stops the old addin and runs the new one
        addin_response = await send_to_addin("reload_addin", {})
        
        # 3. Restart this server process
        logger.info("Restarting MCP Server process...")
        
        def restart_server():
            time.sleep(1) # Give the add-in a moment to start its reloader script
            os.execv(sys.executable, ['python'] + sys.argv)
            
        # Run restart in a background thread so we can return the response first
        import threading
        threading.Thread(target=restart_server, daemon=True).start()
        
        return f"Successfully pulled latest code from {branch}. The Fusion 360 Add-in and MCP Server are now restarting."
        
    except Exception as e:
        logger.error(f"Auto-update failed: {str(e)}")
        return f"Error during update and reload: {str(e)}"

# We'll return a special placeholder that delegates to the real handler
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
    This allows 'from server import some_tool' to work even before initialization.
    """
    # If it's a known tool name (optional check, but let's be guestimate)
    # or just try to initialize if not already done.
    if name.startswith("_") or name == "mcp":
        raise AttributeError(f"module {__name__} has no attribute {name}")
    
    # Returning a placeholder or attempting a sync init?
    # Sync init is risky if it hangs, but let's try to return the handler if it's there
    if name in globals():
        val = globals()[name]
        if not isinstance(val, ToolPlaceholder):
            return val
        
    # For pytest collection, we just need the name to exist.
    # Let's return a placeholder that will be replaced by the real handler in globals()
    # when initialize_tools() is called.
    logger.debug(f"Lazy lookup for {name}")
    
    placeholder = ToolPlaceholder(name)
    # Important: do NOT put the placeholder in globals() yet, or __getattr__ won't be called again
    # unless we explicitly check for it. 
    # Actually, from server import X will bind it.
    return placeholder

def start_background_discovery():
    """
    Starts a background thread to discover tools from the Add-in.
    This ensures the server stays alive even if the Add-in is not running initially.
    """
    import threading
    import time

    def discovery_loop():
        logger.info("Background tool discovery thread started.")
        while True:
            try:
                # Use a fresh event loop for discovery to avoid conflicts with the main server loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(initialize_tools())
                loop.close()
                logger.info("Successfully discovered and registered tools from Add-in.")
                break 
            except Exception as e:
                logger.warning(f"Tool discovery failed (Add-in might not be started or responding), retrying in 10s: {e}")
                time.sleep(10)

    thread = threading.Thread(target=discovery_loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    try:
        # Check transport from environment
        transport_env = os.environ.get("MCP_TRANSPORT", "stdio").lower()
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = os.environ.get("MCP_PORT", "8000")
        
        logger.info(f"Starting MCP Server (transport={transport_env}, host={host}, port={port})")
        
        start_background_discovery()
        
        if transport_env in ["sse", "streamable-http"]:
            import uvicorn
            # Ensure settings are synced
            mcp.settings.host = host
            mcp.settings.port = int(port)
            
            # Create the appropriate app
            if transport_env == "sse":
                app = mcp.sse_app()
            else:
                app = mcp.streamable_http_app()
                
            # Add CORS support for browser-based clients (like OpenWebUI)
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            config = uvicorn.Config(
                app,
                host=host,
                port=int(port),
                log_level=logging.getLevelName(logger.getEffectiveLevel()).lower(),
            )
            server = uvicorn.Server(config)
            
            # Use asyncio.run to start the uvicorn server
            asyncio.run(server.serve())
        else:
            mcp.run(transport="stdio")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)
