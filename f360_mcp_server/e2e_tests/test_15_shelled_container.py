import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_15_shelled_container(mcp_client):
    """Scenario 15: Shelled Container."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Shell"})
    await f360.call_tool("create_sketch", {"name": "BoxSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "BoxSketch", "x1": -10, "y1": -10, "x2": 10, "y2": 10})
    await f360.call_tool("create_extrude", {"name": "BoxBody", "sketch_name": "BoxSketch", "distance": 10.0})
    await f360.call_tool("create_shell", {"name": "BoxShell", "body_name": "BoxBody", "thickness": 0.5})
    await f360.export_and_verify("shelled_container")
