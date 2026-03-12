import logging

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
            self._commands[cmd_name] = func
            logger.info(f"Registered command: {cmd_name}")
            return func
        return decorator

    @property
    def dispatch_table(self):
        return self._commands

# Global registry instance
registry = CommandRegistry()

def command(name=None):
    """
    Shortcut decorator for registry.register
    """
    return registry.register(name)
