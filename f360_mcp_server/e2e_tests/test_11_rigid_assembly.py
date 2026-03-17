import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_11_rigid_assembly(mcp_client):
    """Scenario 11: Rigid Assembly (Two Components)."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Rigid_Assembly"})
    await f360.call_tool("create_component", {"name": "CompA"})
    await f360.call_tool("create_sketch", {"name": "SketchA", "plane": "xy"})
    await f360.call_tool("add_circle", {"sketch_name": "SketchA", "x": 0, "y": 0, "radius": 2.5})
    await f360.call_tool("create_extrude", {"name": "BodyA", "sketch_name": "SketchA", "distance": 5.0})
    await f360.call_tool("create_component", {"name": "CompB"})
    await f360.call_tool("create_sketch", {"name": "SketchB", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "SketchB", "x1": -2, "y1": -2, "x2": 2, "y2": 2})
    await f360.call_tool("create_extrude", {"name": "BodyB", "sketch_name": "SketchB", "distance": 5.0})
    await f360.call_tool("create_joint", {
        "name": "RigidJoint", 
        "component1_name": "CompA", 
        "component2_name": "CompB", 
        "joint_type": "rigid",
        "offset_z": 10.0
    })
    await f360.export_and_verify("rigid_assembly")
