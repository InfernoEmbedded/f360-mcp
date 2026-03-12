import pytest
import asyncio
import pytest_asyncio
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
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
