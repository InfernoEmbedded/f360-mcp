import pytest
import asyncio
import json
from server import apply_constraint, ADDIN_HOST, ADDIN_PORT

async def mock_addin_handler(reader, writer):
    """A simple mock server that replies with success to any JSON-RPC request."""
    data = await reader.read(4096)
    request = json.loads(data.decode('utf-8'))
    
    response = {
        "jsonrpc": "2.0",
        "id": request.get('id'),
        "result": {"message": "Mock success"}
    }
    writer.write(json.dumps(response).encode('utf-8') + b'\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()

import pytest_asyncio

@pytest_asyncio.fixture
async def mock_server():
    """Fixture that starts and stops the mock TCP server."""
    server = await asyncio.start_server(mock_addin_handler, ADDIN_HOST, ADDIN_PORT)
    async with server:
        # Give the server a moment to start
        await asyncio.sleep(0.1)
        yield server

@pytest.mark.asyncio
async def test_apply_constraint(mock_server):
    """Test that the MCP server correctly sends requests and parses responses."""
    result = await apply_constraint(
        sketch_name="pytest_sketch",
        constraint_type="coincident",
        ent1_type="point",
        ent1_idx=0,
        ent2_type="line",
        ent2_idx=1
    )
    assert result == {"message": "Mock success"}
