import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_00_connectivity(mcp_client):
    """Scenario 00: Basic Connectivity Check."""
    f360 = FusionE2E(mcp_client)
    # Simple read tool that doesn't modify state/take much time
    result = await f360.call_tool("list_construction")
    print(f"Connectivity check result: {result}")
    assert "planes" in result
