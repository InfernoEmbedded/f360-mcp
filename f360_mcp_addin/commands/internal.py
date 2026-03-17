import os
from . import registry, command

@command(name="_get_command_metadata")
def get_command_metadata(app):
    """
    Internal command to export all registered command metadata (signatures, docstrings).
    """
    return registry.get_metadata()

@command(name="get_addin_logs")
def get_addin_logs(app):
    """
    Internal command to read the Add-in's persistent log file.
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
        raise Exception(f"Failed to execute reloader: {str(e)}")

@command()
def get_system_info(app):
    """
    Internal command to get system information (OS, temp dir).
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
