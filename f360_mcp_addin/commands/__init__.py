import logging
import inspect

logger = logging.getLogger('f360_mcp')

class CommandRegistry:
    def __init__(self):
        self._commands = {}

    def register(self, name=None):
        """
        Decorator to register a function as an MCP command.
        """
        def decorator(func):
            cmd_name = name or func.__name__
            
            # Capture metadata
            sig = inspect.signature(func)
            params = []
            for param_name, param in sig.parameters.items():
                if param_name == 'app': continue # Internal param
                
                param_info = {
                    "name": param_name,
                    "has_default": param.default is not inspect.Parameter.empty,
                    "default": param.default if param.default is not inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else "Any"
                }
                params.append(param_info)

            self._commands[cmd_name] = {
                "func": func,
                "doc": func.__doc__ or "No description provided.",
                "parameters": params
            }
            logger.info(f"Registered command: {cmd_name}")
            return func
        return decorator

    @property
    def dispatch_table(self):
        # Return a mapping of name -> func for the addin's dispatcher
        return {name: info["func"] for name, info in self._commands.items()}

    def get_metadata(self):
        """
        Returns a serializable dictionary of all registered commands and their signatures.
        """
        metadata = {}
        for name, info in self._commands.items():
            metadata[name] = {
                "doc": info["doc"],
                "parameters": info["parameters"]
            }
        return metadata

# Global registry instance
registry = CommandRegistry()

def command(name=None):
    """
    Shortcut decorator for registry.register
    """
    return registry.register(name)
