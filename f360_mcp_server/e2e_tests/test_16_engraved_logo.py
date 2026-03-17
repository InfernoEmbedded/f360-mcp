import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_16_engraved_logo(mcp_client):
    """Scenario 16: Engraved Logo."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Logo"})
    await f360.call_tool("create_sketch", {"name": "PlateSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "PlateSketch", "x1": -10, "y1": -5, "x2": 10, "y2": 5})
    await f360.call_tool("create_extrude", {"name": "PlateBody", "sketch_name": "PlateSketch", "distance": 1.0})
    await f360.call_tool("create_sketch", {"name": "TextSketch", "plane": "xy"})
    await f360.call_tool("add_text", {"sketch_name": "TextSketch", "text": "F360", "x": -5, "y": -1.5, "height": 3.0})
    await f360.call_tool("create_extrude", {"name": "Engrave", "sketch_name": "TextSketch", "distance": -0.2, "operation": "cut"})
    await f360.export_and_verify("engraved_logo")
