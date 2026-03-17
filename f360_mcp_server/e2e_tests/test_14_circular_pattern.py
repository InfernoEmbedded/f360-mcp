import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_14_circular_pattern(mcp_client):
    """Scenario 14: Circular Pattern."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Circ_Pattern"})
    await f360.call_tool("create_sketch", {"name": "DiscSketch", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "DiscSketch", "x": 0, "y": 0, "radius": 10.0})
    await f360.call_tool("create_extrude", {"name": "DiscBody", "sketch_name": "DiscSketch", "distance": 1.0})
    await f360.call_tool("create_sketch", {"name": "SeedSketch", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "SeedSketch", "x": 8, "y": 0, "radius": 1.0})
    await f360.call_tool("create_extrude", {"name": "SeedBody", "sketch_name": "SeedSketch", "distance": 5.0})
    await f360.call_tool("create_circular_pattern", {
        "name": "CircPattern", 
        "body_name": "SeedBody", 
        "axis_name": "z", 
        "count": 6, 
        "angle_deg": 360.0
    })
    await f360.export_and_verify("circular_pattern")
