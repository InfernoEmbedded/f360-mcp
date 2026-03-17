import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_18_mirrored_chassis(mcp_client):
    """Scenario 18: Mirrored Chassis."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Mirror"})
    await f360.call_tool("create_sketch", {"name": "HalfSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "HalfSketch", "x1": 0, "y1": -5, "x2": 10, "y2": 5})
    await f360.call_tool("create_extrude", {"name": "HalfBody", "sketch_name": "HalfSketch", "distance": 2.0})
    await f360.call_tool("feature_mirror", {"name": "MirrorFeature", "body_name": "HalfBody", "plane_name": "yz"})
    await f360.export_and_verify("mirrored_chassis")
