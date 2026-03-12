from . import registry, command

@command(name="_get_command_metadata")
def get_command_metadata(app):
    """
    Internal command to export all registered command metadata (signatures, docstrings).
    """
    return registry.get_metadata()
