import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_04_hollow_pipe(mcp_client):
    """Scenario 04: Hollow Pipe (Concentric Circles)."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Pipe"})
    await f360.call_tool("create_sketch", {"name": "PipeSketch", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "PipeSketch", "x": 0, "y": 0, "radius": 5.0})
    await f360.call_tool("add_circle", {"sketch_name": "PipeSketch", "x": 0, "y": 0, "radius": 4.0})
    await f360.call_tool("create_extrude", {"name": "PipeBody", "sketch_name": "PipeSketch", "distance": 20.0, "profile_index": 0})
    await f360.export_and_verify("hollow_pipe")
