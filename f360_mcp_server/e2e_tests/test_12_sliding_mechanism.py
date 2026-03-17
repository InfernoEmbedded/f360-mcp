import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_12_sliding_mechanism(mcp_client):
    """Scenario 12: Sliding Mechanism."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Slider"})
    await f360.call_tool("create_component", {"name": "Base"})
    await f360.call_tool("create_component", {"name": "Slider"})
    await f360.call_tool("create_joint", {
        "name": "SliderJoint", 
        "component1_name": "Base", 
        "component2_name": "Slider", 
        "joint_type": "slider"
    })
    await f360.export_and_verify("sliding_mechanism")
