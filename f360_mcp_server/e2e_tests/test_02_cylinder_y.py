import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_02_cylinder_y(mcp_client):
    """Scenario 02: Cylinder along Y axis."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Cylinder_Y"})
    await f360.call_tool("create_sketch", {"name": "BaseSketch", "plane": "xz"})
    await f360.call_tool("add_circle", {"sketch_name": "BaseSketch", "center_x": 0, "center_y": 0, "radius": 2.5})
    await f360.call_tool("create_extrude", {"name": "MainBody", "sketch_name": "BaseSketch", "distance": 10.0})
    await f360.export_and_verify("cylinder_y")
