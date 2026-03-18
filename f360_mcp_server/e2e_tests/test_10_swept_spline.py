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
    await f360.call_tool("add_line", {"sketch_name": "PathSketch", "x1": 0, "y1": 0, "x2": 15, "y2": 0})
    await f360.call_tool("create_sketch", {"name": "ProfileSketch", "plane": "yz"})
    await f360.call_tool("add_rectangle", {"sketch_name": "ProfileSketch", "x1": -0.5, "y1": -0.5, "x2": 0.5, "y2": 0.5})
    await f360.call_tool("create_sweep", {
        "name": "SweepBody", 
        "profile_sketch_name": "ProfileSketch", 
        "path_sketch_name": "PathSketch",
        "path_ent_type": "line", 
        "path_ent_idx": 0
    })
    await f360.export_and_verify("swept_spline")
