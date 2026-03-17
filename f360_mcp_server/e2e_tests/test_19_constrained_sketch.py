import pytest
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_19_constrained_sketch(mcp_client):
    """Scenario 19: Constrained Sketch."""
    f360 = FusionE2E(mcp_client)
    await f360.call_tool("create_new_design", {"name": "E2E_Constraints"})
    await f360.call_tool("create_sketch", {"name": "ConstrainedSketch", "plane": "xy"})
    await f360.call_tool("add_line", {"sketch_name": "ConstrainedSketch", "x1": 0, "y1": 0, "x2": 5, "y2": 1})
    await f360.call_tool("add_line", {"sketch_name": "ConstrainedSketch", "x1": 0, "y1": 5, "x2": 5, "y2": 4})
    await f360.call_tool("apply_constraint", {
        "sketch_name": "ConstrainedSketch", 
        "constraint_type": "parallel",
        "ent1_type": "line", "ent1_idx": 0,
        "ent2_type": "line", "ent2_idx": 1
    })
    await f360.export_and_verify("constrained_sketch")
