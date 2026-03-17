import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_08_parametric_bracket(mcp_client):
    """Scenario 08: Parametric Bracket."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Parametric_Bracket"})
    await f360.call_tool("create_parameter", {"name": "width", "value": "50mm", "comment": "Bracket width"})
    await f360.call_tool("create_parameter", {"name": "height", "value": "30mm"})
    await f360.call_tool("create_sketch", {"name": "BracketSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "BracketSketch", "x1": 0, "y1": 0, "x2": 5, "y2": 3})
    await f360.call_tool("create_extrude", {"name": "BracketBody", "sketch_name": "BracketSketch", "distance": 0.5})
    await f360.export_and_verify("parametric_bracket")
