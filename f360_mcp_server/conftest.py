import pytest
import asyncio
import pytest_asyncio
import httpx
from contextlib import AsyncExitStack
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

@pytest.fixture(scope="session")
def test_app():
    from f360_mcp_server import server
    # Use default transport setting
    return server.create_starlette_app(server.mcp, "sse", "0.0.0.0", "8360")

@pytest.fixture(scope="session")
async def client(test_app):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(test_app.router.lifespan_context(test_app))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=test_app), 
            base_url="http://localhost:8360"
        ) as client:
            yield client
