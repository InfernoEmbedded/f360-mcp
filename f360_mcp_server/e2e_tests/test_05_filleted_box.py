import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_05_filleted_box(mcp_client):
    """Scenario 05: Filleted Box."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Filleted_Box"})
    await f360.call_tool("create_sketch", {"name": "BoxSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "BoxSketch", "x1": -5, "y1": -5, "x2": 5, "y2": 5})
    await f360.call_tool("create_extrude", {"name": "BoxBody", "sketch_name": "BoxSketch", "distance": 10.0})
    await f360.call_tool("create_fillet", {"name": "BoxFillet", "body_name": "BoxBody", "radius": 1.0})
    await f360.export_and_verify("filleted_box")
