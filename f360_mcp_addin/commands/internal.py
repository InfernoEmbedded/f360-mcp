import os
from . import registry, command

@command(name="_get_command_metadata")
def get_command_metadata(app):
    """
    Internal command to export all registered command signatures and docstrings.
    
    Used by the MCP server for tool discovery and schema generation.

    Returns:
        dict: A mapping of command names to their metadata (args, doc, etc.).

    Examples:
        call_addin("_get_command_metadata", {})
    """
    return registry.get_metadata()

@command(name="get_addin_logs")
def get_addin_logs(app):
    """
    Internal command to read the Add-in's persistent log file (last 100KB).
    
    Useful for remote debugging and troubleshooting add-in issues.

    Returns:
        str: Recent log entries.

    Examples:
        call_addin("get_addin_logs", {})
    """
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'f360_mcp.log')
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Return last 100KB
                return f.read()[-100000:]
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    return "Log file not found."
@command()
def reload_addin(app):
    """
    Creates a temporary script to stop and restart this Add-in.
    This safely allows the Add-in to reload its own code after an update.

    Examples:
        call_addin("reload_addin", {})
    """
    import os
    import tempfile
    import adsk.core
    
    # Ensure app is valid (in case we're in background thread)
    actual_app = app if app else adsk.core.Application.get()
    
    # Create the temporary script
    script_content = """import adsk.core
import traceback

def run(context):
    try:
        app = adsk.core.Application.get()
        
        # Give the old process a tiny moment to exit cleanly
        import time
        time.sleep(1)
        
        target_name = 'f360_mcp_addin'
        for p in app.scripts:
            if p.name == target_name:
                p.stop()
                p.run()
                break
    except:
        pass
"""
    
    # Write to a temp file
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "f360_mcp_reloader.py")
    
    with open(script_path, 'w') as f:
        f.write(script_content)
        
    try:
        actual_app.executeTextCommand(f'TextCommands.RunPythonScript "{script_path}"')
        return {"message": "Reloader script executed. Add-in should restart momentarily."}
    except Exception as e:
        error_message = str(e)
        if "There is no command TextCommands.RunPythonScript" in error_message:
            return {
                "message": (
                    "This Fusion 360 build does not support TextCommands.RunPythonScript. "
                    "Skipping in-process add-in reload and leaving the current add-in running."
                ),
                "reloaded": False,
                "reason": error_message,
            }
        raise Exception(f"Failed to execute reloader: {error_message}")

@command()
def get_system_info(app):
    """
    Internal command to retrieve system and environment information.

    Returns:
        dict: {"os": str, "platform": str, "temp_dir": str, "addin_path": str}

    Examples:
        call_addin("get_system_info", {})
    """
    import os
    import tempfile
    import platform
    return {
        "os": os.name,
        "platform": platform.platform(),
        "temp_dir": tempfile.gettempdir(),
        "addin_path": os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    }
