import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_10_swept_spline(mcp_client):
    """Scenario 10: Swept Spline."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Sweep"})
    await f360.call_tool("create_sketch", {"name": "PathSketch", "plane": "xy"})
    points = [[0, 0, 0], [5, 2, 0], [10, -2, 0], [15, 0, 0]]
    await f360.call_tool("add_spline", {"sketch_name": "PathSketch", "points": points})
    await f360.call_tool("create_sketch", {"name": "ProfileSketch", "plane": "yz"})
    await f360.call_tool("add_circle", {"sketch_name": "ProfileSketch", "center_x": 0, "center_y": 0, "radius": 1.0})
    await f360.call_tool("create_sweep", {
        "name": "SweepBody", 
        "profile_sketch_name": "ProfileSketch", 
        "path_sketch_name": "PathSketch",
        "path_ent_type": "spline", 
        "path_ent_idx": 0
    })
    await f360.export_and_verify("swept_spline")
