import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_20_comprehensive_final(mcp_client):
    """Scenario 20: Comprehensive Final Design."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Final_Masterpiece"})
    await f360.call_tool("create_component", {"name": "BaseComp"})
    await f360.call_tool("create_sketch", {"name": "BaseSketch", "plane": "xy"})
    await f360.call_tool("add_rectangle", {"sketch_name": "BaseSketch", "x1": -25, "y1": -25, "x2": 25, "y2": 25})
    await f360.call_tool("create_extrude", {"name": "BaseBody", "sketch_name": "BaseSketch", "distance": 2.0})
    await f360.call_tool("create_component", {"name": "UprightComp"})
    await f360.call_tool("create_sketch", {"name": "UprightSketch", "plane": "xz"})
    await f360.call_tool("add_rectangle", {"sketch_name": "UprightSketch", "x1": -5, "y1": 0, "x2": 5, "y2": 20})
    await f360.call_tool("create_extrude", {"name": "UprightBody", "sketch_name": "UprightSketch", "distance": 2.0})
    await f360.call_tool("create_joint", {
        "name": "BaseUprightJoint",
        "component1_name": "BaseComp",
        "component2_name": "UprightComp",
        "joint_type": "rigid"
    })
    await f360.call_tool("create_fillet", {"name": "FinalFillet", "body_name": "BaseBody", "radius": 1.0})
    try:
        await f360.call_tool("apply_material", {"body_name": "BaseBody", "material_name": "Steel"})
    except:
        pass 
    await f360.export_and_verify("comprehensive_final")
