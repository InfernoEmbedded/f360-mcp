import pytest
import asyncio
import os
from f360_mcp_server import server
from mock_fusion_tcp import MockFusionServer

@pytest.fixture(scope="session")
def mock_fusion():
    server_mock = MockFusionServer(port=0)
    server_mock.start_threaded()
    
    # Now that the mock server is up, initialize the MCP server tools
    from f360_mcp_server import server
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server.initialize_tools())
    loop.close()
    
    yield server_mock
    server_mock.stop_threaded()

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
def recorded_commands():
    # Enable recording via environment variable
    old_env = os.environ.get("F360_RECORD_COMMANDS")
    os.environ["F360_RECORD_COMMANDS"] = "true"
    
    from f360_mcp_server import server
    server.command_history.clear()
    
    yield server.command_history
    
    # Restore and clear
    if old_env is None:
        os.environ.pop("F360_RECORD_COMMANDS", None)
    else:
        os.environ["F360_RECORD_COMMANDS"] = old_env
    server.command_history.clear()
