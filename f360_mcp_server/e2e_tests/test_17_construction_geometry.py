import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_17_construction_geometry(mcp_client):
    """Scenario 17: Construction Geometry (Offset Plane)."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Construction"})
    await f360.call_tool("create_offset_plane", {"name": "OffsetPlane", "base_plane": "xy", "offset": 10.0})
    await f360.call_tool("create_sketch_on_plane", {"name": "ConstSketch", "plane_name": "OffsetPlane"})
    await f360.call_tool("add_circle", {"sketch_name": "ConstSketch", "x": 0, "y": 0, "radius": 5.0})
    await f360.export_and_verify("construction_geometry")
