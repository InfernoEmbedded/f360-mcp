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
                # Return last 1000 lines or 1MB
                return f.read()[-1000000:]
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    return "Log file not found."
