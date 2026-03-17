import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_06_chamfered_plate(mcp_client):
    """Scenario 06: Chamfered Plate."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Chamfered_Plate"})
    await f360.call_tool("create_sketch", {"name": "PlateSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "PlateSketch", "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    await f360.call_tool("create_extrude", {"name": "PlateBody", "sketch_name": "PlateSketch", "distance": 1.0})
    await f360.call_tool("create_chamfer", {"name": "PlateChamfer", "body_name": "PlateBody", "distance": 0.2})
    await f360.export_and_verify("chamfered_plate")
