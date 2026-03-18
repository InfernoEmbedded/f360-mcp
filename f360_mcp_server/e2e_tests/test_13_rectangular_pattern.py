import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_13_rectangular_pattern(mcp_client):
    """Scenario 13: Rectangular Hole Pattern."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Rect_Pattern"})
    await f360.call_tool("create_sketch", {"name": "PlateSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "PlateSketch", "x1": 0, "y1": 0, "x2": 20, "y2": 20})
    await f360.call_tool("create_extrude", {"name": "PlateBody", "sketch_name": "PlateSketch", "distance": 1.0})
    await f360.call_tool("create_sketch", {"name": "HoleSketch", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "HoleSketch", "x": 2, "y": 2, "radius": 0.5})
    await f360.call_tool("create_extrude", {
        "name": "HoleBody",
        "sketch_name": "HoleSketch",
        "distance": -2.0,
        "operation": "cut",
        "target_body_name": "PlateBody"
    })
    await f360.call_tool("create_rectangular_pattern", {
        "name": "RectPattern", 
        "body_name": "HoleBody", 
        "count_x": 4, 
        "count_y": 4, 
        "distance_x": 5.0, 
        "distance_y": 5.0
    })
    await f360.export_and_verify("rectangular_pattern")
