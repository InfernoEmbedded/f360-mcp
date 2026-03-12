import logging
import inspect

logger = logging.getLogger('f360_mcp')

class CommandRegistry:
    def __init__(self):
        self._commands = {}

    def _parse_params_from_doc(self, doc):
        """
        Simple parser to extract parameter descriptions from a docstring.
        Looks for 'Arguments:' or 'Args:' section.
        """
        if not doc: return {}
        params_info = {}
        lines = doc.split('\n')
        in_args_section = False
        for line in lines:
            line = line.strip()
            if line.lower().startswith(('arguments:', 'args:')):
                in_args_section = True
                continue
            if in_args_section:
                if not line: continue
                if ':' in line:
                    # Expecting "name (type): description" or "name: description"
                    parts = line.split(':', 1)
                    name_part = parts[0].strip()
                    desc_part = parts[1].strip()
                    # Extract name from "name (type)"
                    name = name_part.split('(')[0].strip()
                    params_info[name] = desc_part
                elif line.startswith('- ') or line.startswith('* '):
                    # Handle bullet points
                    line = line[2:].strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        name = parts[0].strip()
                        desc_part = parts[1].strip()
                        params_info[name] = desc_part
        return params_info

    def register(self, name=None):
        """
        Decorator to register a function as an MCP command.
        """
        def decorator(func):
            cmd_name = name or func.__name__
            
            # Capture metadata
            sig = inspect.signature(func)
            doc = func.__doc__ or "No description provided."
            param_descriptions = self._parse_params_from_doc(doc)
            
            params = []
            for param_name, param in sig.parameters.items():
                if param_name == 'app': continue # Internal param
                
                param_info = {
                    "name": param_name,
                    "description": param_descriptions.get(param_name, ""),
                    "has_default": param.default is not inspect.Parameter.empty,
                    "default": param.default if param.default is not inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else "Any"
                }
                params.append(param_info)

            self._commands[cmd_name] = {
                "func": func,
                "doc": doc,
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
