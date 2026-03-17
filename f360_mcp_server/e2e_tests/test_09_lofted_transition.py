import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_09_lofted_transition(mcp_client):
    """Scenario 09: Lofted Transition."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Loft"})
    await f360.call_tool("create_sketch", {"name": "BottomSketch", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "BottomSketch", "x": 0, "y": 0, "radius": 5.0})
    await f360.call_tool("create_offset_plane", {"name": "TopPlane", "base_plane": "xy", "offset": 10.0})
    await f360.call_tool("create_sketch_on_plane", {"name": "TopSketch", "plane_name": "TopPlane"})
    await f360.call_tool("add_rectangle", {"sketch_name": "TopSketch", "x1": -2, "y1": -2, "x2": 2, "y2": 2})
    await f360.call_tool("create_loft", {
        "name": "LoftBody", 
        "profiles_info": [
            {"sketch_name": "BottomSketch", "profile_idx": 0},
            {"sketch_name": "TopSketch", "profile_idx": 0}
        ]
    })
    await f360.export_and_verify("lofted_transition")
