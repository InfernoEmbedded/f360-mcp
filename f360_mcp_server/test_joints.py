import pytest
from f360_mcp_server.server import create_joint, create_as_built_joint

@pytest.mark.asyncio
async def test_create_joint(mock_fusion):
    result = await create_joint(
        component1_name="Comp1",
        component2_name="Comp2",
        joint_type="rigid",
        offset_x=1.0
    )
    assert "Created rigid joint" in result["message"]
    assert "joint_name" in result

@pytest.mark.asyncio
async def test_create_as_built_joint(mock_fusion):
    result = await create_as_built_joint(
        component1_name="Comp1",
        component2_name="Comp2",
        joint_type="revolute"
    )
    assert "Created as-built revolute joint" in result["message"]
    assert "joint_name" in result
