import pytest
import asyncio
import pytest_asyncio
from mock_fusion_tcp import MockFusionServer

@pytest.fixture(scope="session")
def mock_fusion():
    server = MockFusionServer(port=0)
    server.start_threaded()
    yield server
    server.stop_threaded()

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
