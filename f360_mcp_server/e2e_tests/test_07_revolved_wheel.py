import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_07_revolved_wheel(mcp_client):
    """Scenario 07: Revolved Wheel."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Revolved_Wheel"})
    await f360.call_tool("create_sketch", {"name": "WheelSketch", "plane": "xz"})
    await f360.call_tool("add_line", {"sketch_name": "WheelSketch", "x1": 0, "y1": -5, "x2": 0, "y2": 5})
    await f360.call_tool("add_rectangle", {"sketch_name": "WheelSketch", "x1": 1, "y1": -2, "x2": 3, "y2": 2})
    await f360.call_tool("create_revolve", {
        "name": "WheelBody", 
        "sketch_name": "WheelSketch", 
        "axis_ent_type": "line", 
        "axis_ent_idx": 0, 
        "angle": 360.0
    })
    await f360.export_and_verify("revolved_wheel")
