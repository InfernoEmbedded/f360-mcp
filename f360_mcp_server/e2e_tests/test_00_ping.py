import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_00_ping(mcp_client):
    """Scenario 00: Simple MCP Ping."""
    f360 = FusionE2E(mcp_client)
    result = await f360.call_tool("ping_server")
    print(f"Ping result: {result}")
    assert result == "pong"
